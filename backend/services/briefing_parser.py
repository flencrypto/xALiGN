"""Briefing Parser Service – ingests daily GLOBAL DATA CENTRE INTELLIGENCE BRIEFINGs.

Parses the structured markdown/text, upserts Accounts, creates Opportunities and
TriggerSignals, and stores the raw briefing as a DailyBriefing record.
"""

import logging
import re
from datetime import datetime, date
from typing import Any

from sqlalchemy.orm import Session

from backend.models.account import Account, AccountType, SignalType, SignalStatus, TriggerSignal
from backend.models.intelligence import DailyBriefing
from backend.models.opportunity import Opportunity, OpportunityStage

logger = logging.getLogger("align.briefing_parser")


# ── Company-type heuristics ───────────────────────────────────────────────────

_HYPERSCALERS = {
    "aws", "amazon", "google", "microsoft", "meta", "apple", "oracle",
    "alibaba", "tencent", "bytedance", "openai", "anthropic",
}
_SUPPLIERS = {
    "semtech", "vertiv", "schneider", "apc", "eaton", "legrand", "siemens",
    "abb", "pue", "rittal", "panduit", "commscope", "nvidia", "amd", "intel",
    "qualcomm", "broadcom", "tsmc", "samsung", "sk hynix", "micron",
}


def _classify_account_type(name: str) -> AccountType:
    """Heuristically classify a company name into an AccountType."""
    lower = name.lower()
    for h in _HYPERSCALERS:
        if h in lower:
            return AccountType.hyperscaler
    for s in _SUPPLIERS:
        if s in lower:
            return AccountType.enterprise
    return AccountType.operator


# ── Regex patterns ────────────────────────────────────────────────────────────

# Matches "€1.2bn", "$500m", "£2.5 billion", "USD 300 million" etc.
_VALUE_RE = re.compile(
    r"(?:£|\$|€|USD|GBP|EUR)\s*(\d+(?:\.\d+)?)\s*(billion|bn|million|m)\b",
    re.IGNORECASE,
)

# Matches "250MW", "1.2 GW", "500 megawatts"
_CAPACITY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(GW|MW|gigawatt|megawatt)",
    re.IGNORECASE,
)

# Detect signal type keywords
_SIGNAL_KEYWORDS: list[tuple[str, SignalType]] = [
    (r"\bnew[\s\-]build\b|\bground[\s\-]breaking\b|\bbreaking[\s\-]ground\b|\bconstruction[\s\-]start", SignalType.new_build),
    (r"\bexpansion\b|\bexpand\b|\bphase\s*[23]\b|\bextension\b", SignalType.expansion),
    (r"\bcancell?ed?\b|\babandoned?\b|\bshelved?\b|\bwithdraw", SignalType.cancellation),
    (r"\bacquisition\b|\bacquire[sd]?\b|\btakeover\b|\bmerger\b|\bbuy\b", SignalType.acquisition),
    (r"\benergy[\s\-]deal\b|\bppa\b|\bpower[\s\-]purchase\b|\brenewable[\s\-]energ", SignalType.energy_deal),
    (r"\bsupply[\s\-]chain\b|\bshortage\b|\bcritical[\s\-]component\b|\blead[\s\-]time", SignalType.supply_chain_risk),
]

# Date extraction from briefing header
_DATE_RE = re.compile(
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|"
    r"(\d{4}-\d{2}-\d{2})|"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE,
)


def _extract_date(text: str) -> str:
    """Extract the first recognisable date from the briefing header (first 500 chars)."""
    header = text[:500]
    m = _DATE_RE.search(header)
    if m:
        return m.group(0).strip()
    return date.today().isoformat()


def _detect_signal_type(text: str) -> SignalType:
    """Return the most relevant signal type for a block of text."""
    for pattern, sig_type in _SIGNAL_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return sig_type
    return SignalType.new_build


def _extract_value_millions(text: str) -> float | None:
    """Return investment value normalised to millions, or None."""
    m = _VALUE_RE.search(text)
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2).lower()
    if unit in ("billion", "bn"):
        value *= 1000
    return value


def _extract_capacity_mw(text: str) -> float | None:
    """Return capacity in MW, or None."""
    m = _CAPACITY_RE.search(text)
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2).upper()
    if unit in ("GW", "GIGAWATT"):
        value *= 1000
    return value


# ── Company extraction ────────────────────────────────────────────────────────

# Known company names that appear in briefings (extend as needed)
_KNOWN_COMPANIES = [
    "Oracle", "Meta", "AWS", "Amazon", "Google", "Microsoft", "Apple",
    "Semtech", "FRV", "OpenAI", "Anthropic", "Nvidia", "AMD", "Intel",
    "Vertiv", "Schneider Electric", "ABB", "Siemens", "Eaton",
    "Digital Realty", "Equinix", "NTT", "Colt", "Iron Mountain",
    "CyrusOne", "CoreSite", "QTS", "DataBank",
]

_COMPANY_RE = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in _KNOWN_COMPANIES) + r")\b",
    re.IGNORECASE,
)


def _extract_companies(text: str) -> list[str]:
    """Return deduplicated list of company names found in text."""
    found: dict[str, str] = {}  # lower → canonical
    for m in _COMPANY_RE.finditer(text):
        lower = m.group(0).lower()
        if lower not in found:
            # Use the canonical casing from _KNOWN_COMPANIES
            canonical = next(
                (c for c in _KNOWN_COMPANIES if c.lower() == lower), m.group(0)
            )
            found[lower] = canonical
    return list(found.values())


# ── Section parsing ────────────────────────────────────────────────────────────

def _split_sections(text: str) -> dict[str, str]:
    """Split briefing into named sections by markdown headings."""
    sections: dict[str, str] = {"__root__": ""}
    current = "__root__"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            current = stripped.lstrip("#").strip().upper()
            sections[current] = ""
        else:
            sections[current] = sections.get(current, "") + line + "\n"
    return sections


def _extract_table_rows(text: str) -> list[dict[str, str]]:
    """Parse simple markdown tables into list-of-dicts.

    Supports:
      | Header1 | Header2 | ...
      |---------|---------|
      | val1    | val2    | ...
    """
    rows: list[dict[str, str]] = []
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return rows

    headers = [h.strip() for h in lines[0].strip("|").split("|")]
    for line in lines[2:]:  # skip separator
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


# ── Upsert helpers ────────────────────────────────────────────────────────────

def _upsert_account(db: Session, name: str) -> tuple[Account, bool]:
    """Return (account, created) – upserts by name (case-insensitive)."""
    existing = (
        db.query(Account)
        .filter(Account.name.ilike(name))
        .first()
    )
    if existing:
        return existing, False
    account = Account(
        name=name,
        type=_classify_account_type(name),
    )
    db.add(account)
    db.flush()  # get id without committing
    logger.info("Created account: %s", name)
    return account, True


def _upsert_opportunity(
    db: Session,
    account: Account,
    title: str,
    description: str | None,
    estimated_value: float | None,
) -> tuple[Opportunity, bool]:
    """Return (opportunity, created) – upserts by account_id + title."""
    existing = (
        db.query(Opportunity)
        .filter(Opportunity.account_id == account.id, Opportunity.title == title)
        .first()
    )
    if existing:
        # Update estimated_value if we now have one
        if estimated_value and not existing.estimated_value:
            existing.estimated_value = estimated_value
        return existing, False
    opp = Opportunity(
        account_id=account.id,
        title=title,
        description=description,
        stage=OpportunityStage.target,
        estimated_value=estimated_value,
        currency="USD",
    )
    db.add(opp)
    db.flush()
    logger.info("Created opportunity: %s for %s", title, account.name)
    return opp, True


# ── Main parse-and-upsert ─────────────────────────────────────────────────────

def parse_and_upsert(db: Session, briefing_text: str) -> dict[str, Any]:
    """Parse the briefing, upsert accounts/opportunities/signals, save the briefing.

    Returns a summary dict matching BriefingIngestResponse.
    """
    processed_at = datetime.utcnow()
    accounts_updated = 0
    opportunities_created = 0
    trigger_signals_created = 0
    suggested_touchpoints: list[str] = []

    briefing_date = _extract_date(briefing_text)
    sections = _split_sections(briefing_text)

    # ── Pass 1: extract all company names from the full text ──────────────────
    all_companies = _extract_companies(briefing_text)
    account_map: dict[str, Account] = {}  # canonical name → Account

    for company_name in all_companies:
        try:
            account, created = _upsert_account(db, company_name)
            account_map[company_name.lower()] = account
            if created:
                accounts_updated += 1
            else:
                accounts_updated += 1  # count updates too
        except Exception as exc:
            logger.warning("Failed to upsert account %s: %s", company_name, exc)

    # ── Pass 2: extract opportunities from table rows ─────────────────────────
    for section_name, section_text in sections.items():
        rows = _extract_table_rows(section_text)
        for row in rows:
            # Try to find location/project name/capacity/value columns
            project_name = (
                row.get("Project")
                or row.get("Project Name")
                or row.get("Name")
                or row.get("Site")
            )
            location = row.get("Location") or row.get("Country") or row.get("Region")
            company_col = (
                row.get("Company")
                or row.get("Operator")
                or row.get("Developer")
                or row.get("Client")
            )
            value_col = (
                row.get("Investment")
                or row.get("Value")
                or row.get("CapEx")
                or row.get("Capex")
            )

            if not project_name:
                continue

            # Determine which account to link
            account: Account | None = None
            if company_col:
                for k, a in account_map.items():
                    if k in company_col.lower():
                        account = a
                        break
                if not account:
                    try:
                        account, created = _upsert_account(db, company_col)
                        account_map[company_col.lower()] = account
                        if created:
                            accounts_updated += 1
                        else:
                            accounts_updated += 1
                    except Exception as exc:
                        logger.warning("Upsert account from table %s: %s", company_col, exc)

            if not account and account_map:
                # fall back to first account
                account = next(iter(account_map.values()))

            if not account:
                continue

            title = project_name
            if location:
                title = f"{project_name} – {location}"

            estimated_value = _extract_value_millions(value_col or "") if value_col else None

            try:
                _, created = _upsert_opportunity(
                    db, account, title[:255],
                    section_text[:500] if section_text else None,
                    estimated_value,
                )
                if created:
                    opportunities_created += 1
                    suggested_touchpoints.append(
                        f"Draft outreach for {account.name} re: {title[:60]}"
                    )
            except Exception as exc:
                logger.warning("Upsert opportunity %s: %s", title, exc)

    # ── Pass 3: extract trigger signals from key sections ─────────────────────
    signal_sections = [
        k for k in sections if any(
            kw in k for kw in (
                "DEVELOPMENT", "DATASET", "INTELLIGENCE", "SIGNAL", "TRIGGER",
                "INDUSTRY", "HIGHLIGHT",
            )
        )
    ]

    for section_name in signal_sections:
        section_text = sections[section_name]
        # Each paragraph/bullet is a potential signal
        paragraphs = re.split(r"\n{2,}|(?:^|\n)[•\-\*]\s+", section_text)
        for para in paragraphs:
            para = para.strip()
            if len(para) < 30:
                continue

            sig_type = _detect_signal_type(para)
            companies_in_para = _extract_companies(para)
            if not companies_in_para:
                continue

            for company_name in companies_in_para[:2]:  # max 2 signals per paragraph
                account = account_map.get(company_name.lower())
                if not account:
                    try:
                        account, created = _upsert_account(db, company_name)
                        account_map[company_name.lower()] = account
                        if created:
                            accounts_updated += 1
                        else:
                            accounts_updated += 1
                    except Exception as exc:
                        logger.warning("Upsert account for signal %s: %s", company_name, exc)
                        continue

                title = para[:120].rstrip() + ("…" if len(para) > 120 else "")
                try:
                    signal = TriggerSignal(
                        account_id=account.id,
                        signal_type=sig_type,
                        title=title[:255],
                        description=para[:2000],
                        source_url=None,
                        status=SignalStatus.new,
                    )
                    db.add(signal)
                    trigger_signals_created += 1
                    logger.info("Created signal (%s) for %s", sig_type.value, account.name)

                    # Suggest a touchpoint for expansion/new_build signals
                    if sig_type in (SignalType.new_build, SignalType.expansion):
                        suggested_touchpoints.append(
                            f"Draft outreach for {account.name} – {sig_type.value} signal detected"
                        )
                except Exception as exc:
                    logger.warning("Create signal for %s: %s", company_name, exc)

    # ── Save the full briefing as a DailyBriefing record ─────────────────────
    doc_title = f"Daily Intelligence Briefing – {briefing_date}"
    briefing_doc = DailyBriefing(
        title=doc_title[:500],
        briefing_type="daily_intelligence_briefing",
        full_text=briefing_text,
        briefing_date=briefing_date,
        accounts_updated=accounts_updated,
        opportunities_created=opportunities_created,
        trigger_signals_created=trigger_signals_created,
    )
    db.add(briefing_doc)
    db.commit()
    db.refresh(briefing_doc)

    logger.info(
        "Briefing ingested: accounts=%d opp=%d signals=%d doc_id=%d",
        accounts_updated, opportunities_created, trigger_signals_created, briefing_doc.id,
    )

    return {
        "processed_at": processed_at,
        "accounts_updated": accounts_updated,
        "opportunities_created": opportunities_created,
        "trigger_signals_created": trigger_signals_created,
        "briefing_doc_id": f"doc_{briefing_doc.id}",
        "suggested_touchpoints": list(dict.fromkeys(suggested_touchpoints))[:10],  # dedup, cap at 10
    }
