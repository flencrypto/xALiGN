"""Core intelligence service – website crawling, Grok AI analysis, and asset management."""

import asyncio
import json
import logging
import os
import re
import unicodedata
import urllib.robotparser
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from backend.models.intelligence import (
    BlogDraft,
    CompanyIntelligence,
    ExecutiveProfile,
    IntelPhoto,
)

logger = logging.getLogger("contractghost.intelligence")

GROK_API_KEY = os.getenv("GROK_API_KEY", "")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
GROK_CHAT_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-beta"
GROK_VISION_MODEL = "grok-2-vision-1212"

_HEADERS = {
    "User-Agent": "ContractGHOST-Intelligence/1.0 (+https://contractghost.com/bot)",
    "Accept": "text/html,application/xhtml+xml",
}


# ── Robots.txt helpers ────────────────────────────────────────────────────────

def _can_fetch(url: str) -> bool:
    """Return True if the URL is allowed by the site's robots.txt."""
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(_HEADERS["User-Agent"], url)
    except Exception:
        return True  # Allow on error – conservative default


# ── Website crawler ───────────────────────────────────────────────────────────

async def crawl_website(url: str) -> dict:
    """
    Crawl the homepage and key sub-pages of a website.

    Respects robots.txt, sets a compliant User-Agent, and rate-limits
    between requests. Returns a dict with page_texts and metadata.
    """
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    pages_to_try = [url, urljoin(base, "/about"), urljoin(base, "/investor-relations")]

    page_texts: dict[str, str] = {}
    metadata: dict[str, str | list] = {"title": "", "meta_description": "", "links": []}
    sources: list[str] = []

    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15) as client:
        for page_url in pages_to_try:
            if not _can_fetch(page_url):
                logger.info("robots.txt disallows %s – skipping", page_url)
                continue
            try:
                resp = await client.get(page_url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # Strip scripts and styles
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()

                text = " ".join(soup.get_text(separator=" ").split())
                page_texts[page_url] = text[:8000]  # Cap per page to avoid token blowout
                sources.append(page_url)

                if not metadata["title"]:
                    title_tag = soup.find("title")
                    if title_tag:
                        metadata["title"] = title_tag.get_text(strip=True)

                if not metadata["meta_description"]:
                    desc = soup.find("meta", attrs={"name": "description"})
                    if desc and desc.get("content"):
                        metadata["meta_description"] = desc["content"]

                if not metadata["links"]:
                    metadata["links"] = [
                        a["href"] for a in soup.find_all("a", href=True)
                        if a["href"].startswith("http")
                    ][:20]

                await asyncio.sleep(1)  # Rate limit between requests
            except Exception as exc:
                logger.warning("Failed to crawl %s: %s", page_url, exc)

    return {"page_texts": page_texts, "metadata": metadata, "sources": sources}


# ── Grok API helper ───────────────────────────────────────────────────────────

async def _call_grok(system_prompt: str, user_message: str) -> str:
    """Call the Grok chat completions API and return the assistant message text."""
    if not GROK_API_KEY:
        raise ValueError("GROK_API_KEY is not set")

    payload = {
        "model": GROK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            GROK_CHAT_URL,
            json=payload,
            headers={"Authorization": f"Bearer {GROK_API_KEY}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _extract_json_from_text(text: str) -> dict:
    """Extract the first JSON object found in a text string."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {}


def _slugify(text: str) -> str:
    """Convert a title string to a URL-safe slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:128]


# ── Core intelligence functions ───────────────────────────────────────────────

async def research_company(website_url: str, db: Session) -> CompanyIntelligence:
    """
    Orchestrate full company research: crawl → Grok analysis → persist.

    Creates a CompanyIntelligence record at status='processing', populates it
    from the Grok response, and returns the completed record.
    """
    intel = CompanyIntelligence(website_url=website_url, status="processing")
    db.add(intel)
    db.commit()
    db.refresh(intel)

    try:
        crawl_data = await crawl_website(website_url)

        combined_text = "\n\n".join(
            f"[{url}]\n{text}" for url, text in crawl_data["page_texts"].items()
        )
        metadata = crawl_data["metadata"]
        sources = crawl_data["sources"]

        if GROK_API_KEY:
            system_prompt = (
                "You are an institutional infrastructure intelligence analyst. "
                "Extract structured signals indicating expansion, capital investment, "
                "AI infrastructure adoption, vendor opportunity signals, and risk indicators. "
                "Only use publicly available data. Return strictly formatted JSON."
            )
            user_message = (
                f"Website: {website_url}\n"
                f"Title: {metadata.get('title', '')}\n"
                f"Meta description: {metadata.get('meta_description', '')}\n\n"
                f"Page content:\n{combined_text[:12000]}\n\n"
                "Return a JSON object with exactly these fields:\n"
                "company_name, business_model, locations (list), expansion_signals (list),\n"
                "technology_growth_indicators (list), financial_health_summary (string),\n"
                "recent_earnings_highlights (list), competitor_mentions (list),\n"
                "strategic_risk_factors (list), potential_bid_opportunities (list)"
            )
            raw_response = await _call_grok(system_prompt, user_message)
            extracted = _extract_json_from_text(raw_response)
        else:
            logger.warning("GROK_API_KEY not set – returning empty intelligence data")
            extracted = {}

        intel.company_name = extracted.get("company_name") or metadata.get("title") or None
        intel.business_model = extracted.get("business_model")
        intel.locations = json.dumps(extracted.get("locations", []))
        intel.expansion_signals = json.dumps(extracted.get("expansion_signals", []))
        intel.technology_growth_indicators = json.dumps(
            extracted.get("technology_growth_indicators", [])
        )
        intel.financial_health_summary = extracted.get("financial_health_summary")
        intel.recent_earnings_highlights = json.dumps(
            extracted.get("recent_earnings_highlights", [])
        )
        intel.competitor_mentions = json.dumps(extracted.get("competitor_mentions", []))
        intel.strategic_risk_factors = json.dumps(extracted.get("strategic_risk_factors", []))
        intel.potential_bid_opportunities = json.dumps(
            extracted.get("potential_bid_opportunities", [])
        )
        intel.raw_crawl_data = combined_text[:20000]
        intel.sources_cited = json.dumps(sources)
        intel.status = "completed"
        intel.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(intel)

        # Extract executive profiles as a side-effect
        await extract_executive_profiles(intel, crawl_data, db)

    except Exception as exc:
        logger.error("research_company failed for %s: %s", website_url, exc)
        intel.status = "failed"
        intel.error_message = str(exc)
        intel.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(intel)

    return intel


async def extract_executive_profiles(
    intelligence: CompanyIntelligence, crawl_data: dict, db: Session
) -> list[ExecutiveProfile]:
    """
    Use Grok to extract compliant public-data executive profiles from crawl data.

    Only extracts publicly available professional information. Never extracts
    personal addresses, family information, or private social data.
    """
    combined_text = "\n\n".join(crawl_data["page_texts"].values())
    profiles: list[ExecutiveProfile] = []

    if not GROK_API_KEY:
        return profiles

    try:
        system_prompt = (
            "You are a compliance-first executive research analyst. "
            "Extract ONLY publicly available professional information about named executives. "
            "NEVER include: personal addresses, family information, or private social media data. "
            "Return strictly formatted JSON."
        )
        user_message = (
            f"Company: {intelligence.company_name or intelligence.website_url}\n"
            f"Content:\n{combined_text[:10000]}\n\n"
            "Return a JSON object with a single key 'executives' containing a list. "
            "Each executive entry must have only these fields: "
            "name, role, professional_focus (list of topics), recent_interviews (list), "
            "conference_appearances (list), public_charity_involvement (list), "
            "communication_style, conversation_angles (list), source_urls (list)"
        )
        raw_response = await _call_grok(system_prompt, user_message)
        data = _extract_json_from_text(raw_response)
        executives = data.get("executives", [])

        for exec_data in executives:
            if not exec_data.get("name"):
                continue
            profile = ExecutiveProfile(
                intelligence_id=intelligence.id,
                account_id=intelligence.account_id,
                name=exec_data.get("name", ""),
                role=exec_data.get("role"),
                professional_focus=json.dumps(exec_data.get("professional_focus", [])),
                public_interests=json.dumps(exec_data.get("public_interests", [])),
                recent_interviews=json.dumps(exec_data.get("recent_interviews", [])),
                conference_appearances=json.dumps(exec_data.get("conference_appearances", [])),
                public_charity_involvement=json.dumps(
                    exec_data.get("public_charity_involvement", [])
                ),
                communication_style=exec_data.get("communication_style"),
                conversation_angles=json.dumps(exec_data.get("conversation_angles", [])),
                source_urls=json.dumps(exec_data.get("source_urls", [])),
            )
            db.add(profile)
            profiles.append(profile)

        if profiles:
            db.commit()
            for p in profiles:
                db.refresh(p)

    except Exception as exc:
        logger.error("extract_executive_profiles failed: %s", exc)

    return profiles


async def generate_blog_draft(intelligence: CompanyIntelligence, db: Session) -> BlogDraft:
    """
    Generate an institutional-tone blog post from company intelligence data.

    Returns a BlogDraft record at status='pending_approval'.
    """
    intel_summary = {
        "company_name": intelligence.company_name,
        "business_model": intelligence.business_model,
        "expansion_signals": intelligence.expansion_signals,
        "technology_growth_indicators": intelligence.technology_growth_indicators,
        "potential_bid_opportunities": intelligence.potential_bid_opportunities,
        "financial_health_summary": intelligence.financial_health_summary,
    }

    title = f"Intelligence Brief: {intelligence.company_name or intelligence.website_url}"
    body_markdown = ""
    seo_meta = None
    linkedin_variant = None
    x_variant = None

    if GROK_API_KEY:
        try:
            system_prompt = (
                "You are a senior institutional content strategist writing for a "
                "data centre infrastructure consultancy. Write authoritative, concise, "
                "and insight-rich content. Return strictly formatted JSON."
            )
            user_message = (
                f"Intelligence data:\n{json.dumps(intel_summary, indent=2)}\n\n"
                "Write a blog post and return a JSON object with these fields:\n"
                "title (string), body_markdown (full blog post in markdown, min 400 words), "
                "seo_meta_description (max 160 chars), "
                "linkedin_variant (300-word LinkedIn post), "
                "x_variant (max 280 chars Twitter/X post)"
            )
            raw = await _call_grok(system_prompt, user_message)
            data = _extract_json_from_text(raw)
            title = data.get("title", title)
            body_markdown = data.get("body_markdown", "")
            seo_meta = data.get("seo_meta_description")
            linkedin_variant = data.get("linkedin_variant")
            x_variant = data.get("x_variant")
        except Exception as exc:
            logger.error("generate_blog_draft Grok call failed: %s", exc)

    if not body_markdown:
        body_markdown = (
            f"# {title}\n\n"
            f"**Company:** {intelligence.company_name or 'Unknown'}\n\n"
            f"**Business Model:** {intelligence.business_model or 'N/A'}\n\n"
            f"**Expansion Signals:** {intelligence.expansion_signals or 'N/A'}\n\n"
            f"*This draft was generated with limited data. Please enrich before publishing.*"
        )

    slug = _slugify(title)
    # Ensure slug uniqueness by appending the intelligence id
    slug = f"{slug}-{intelligence.id}"

    draft = BlogDraft(
        intelligence_id=intelligence.id,
        title=title,
        slug=slug,
        body_markdown=body_markdown,
        seo_meta_description=seo_meta,
        linkedin_variant=linkedin_variant,
        x_variant=x_variant,
        status="pending_approval",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


async def analyze_photo(file_content: bytes, filename: str) -> dict:
    """
    Use Grok vision to analyze a photo for construction/facility intelligence.

    Falls back to an empty dict if the API key is not configured or on error.
    """
    if not GROK_API_KEY:
        return {}

    ext = Path(filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return {}

    try:
        import base64
        image_b64 = base64.b64encode(file_content).decode()
        mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else f"image/{ext.lstrip('.')}"

        payload = {
            "model": GROK_VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{image_b64}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Analyze this image for infrastructure intelligence. "
                                "Return a JSON object with: construction_stage, facility_type, "
                                "brand_signage (list), notable_details (list)"
                            ),
                        },
                    ],
                }
            ],
            "temperature": 0.1,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                GROK_CHAT_URL,
                json=payload,
                headers={"Authorization": f"Bearer {GROK_API_KEY}"},
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            return _extract_json_from_text(raw)
    except Exception as exc:
        logger.error("analyze_photo failed for %s: %s", filename, exc)
        return {}


def save_photo_local(
    file_content: bytes,
    filename: str,
    intelligence_id: int | None,
    account_id: int | None,
    photo_type: str | None,
    db: Session,
) -> IntelPhoto:
    """
    Save an uploaded photo to the local uploads directory and persist an IntelPhoto record.

    Optionally runs AI analysis (sync wrapper calls async via asyncio.run).
    """
    upload_path = Path(UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^\w.\-]", "_", filename)
    dest = upload_path / safe_name
    # Avoid overwriting existing files
    counter = 1
    while dest.exists():
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        dest = upload_path / f"{stem}_{counter}{suffix}"
        counter += 1

    dest.write_bytes(file_content)
    local_path = str(dest)

    # Analyze photo; always run in a dedicated thread with its own event loop
    # to avoid conflicts with any running loop in the calling thread.
    try:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, analyze_photo(file_content, filename))
            ai_result = future.result(timeout=90)
    except Exception as exc:
        logger.warning("Photo analysis skipped: %s", exc)
        ai_result = {}

    photo = IntelPhoto(
        intelligence_id=intelligence_id,
        account_id=account_id,
        filename=filename,
        local_path=local_path,
        photo_type=photo_type,
        ai_analysis=json.dumps(ai_result) if ai_result else None,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo
