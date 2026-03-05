"""
aLiGN — Streamlit UI
====================
AI-native Bid + Delivery OS for Data Centre Refurbs & New Builds.

Run locally:
    streamlit run streamlit_app.py

Environment variables:
    ALIGN_API_URL   Backend base URL (default: http://localhost:8000/api/v1)
    XAI_API_KEY     Optional — enables AI-powered Intel & Blog features
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────

API_URL: str = os.getenv("ALIGN_API_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="aLiGN OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── API helpers ───────────────────────────────────────────────────────────────


def _get(path: str, params: dict | None = None) -> Any:
    """GET from the backend; returns parsed JSON or None on error."""
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot reach the aLiGN backend. Is it running?", icon="🔌")
    except requests.exceptions.HTTPError as exc:
        st.error(f"API error {exc.response.status_code}: {exc.response.text[:200]}")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
    return None


def _post(path: str, payload: dict) -> Any:
    """POST to the backend; returns parsed JSON or None on error."""
    try:
        r = requests.post(f"{API_URL}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot reach the aLiGN backend. Is it running?", icon="🔌")
    except requests.exceptions.HTTPError as exc:
        st.error(f"API error {exc.response.status_code}: {exc.response.text[:300]}")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
    return None


def _delete(path: str) -> bool:
    """DELETE from the backend; returns True on success."""
    try:
        r = requests.delete(f"{API_URL}{path}", timeout=8)
        r.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot reach the aLiGN backend. Is it running?", icon="🔌")
    except requests.exceptions.HTTPError as exc:
        st.error(f"API error {exc.response.status_code}: {exc.response.text[:200]}")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
    return False


def _health() -> bool:
    """Return True if the backend health endpoint is reachable."""
    base = API_URL.replace("/api/v1", "")
    try:
        r = requests.get(f"{base}/health", timeout=5)
        return r.ok
    except Exception:
        return False


def _fmt_date(val: str | None) -> str:
    if not val:
        return "—"
    try:
        return datetime.fromisoformat(val.rstrip("Z")).strftime("%d %b %Y")
    except ValueError:
        return val


def _fmt_money(val: float | None, currency: str = "GBP") -> str:
    if val is None:
        return "—"
    sym = {"GBP": "£", "USD": "$", "EUR": "€"}.get(currency, currency)
    if val >= 1_000_000:
        return f"{sym}{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{sym}{val / 1_000:.0f}k"
    return f"{sym}{val:.0f}"


# ── Sidebar navigation ────────────────────────────────────────────────────────

st.sidebar.markdown(
    """
    <div style='padding:8px 0 16px'>
      <span style='font-size:1.6rem;font-weight:700;color:#00E5FF;letter-spacing:0.02em'>
        a<span style='font-size:2rem'>L</span>iGN
      </span>
      <div style='color:#94A3B8;font-size:0.7rem;font-family:monospace;margin-top:2px;
                  text-transform:uppercase;letter-spacing:0.1em'>
        Bid + Delivery OS
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

PAGES = {
    "🏠  Dashboard":      "dashboard",
    "🏢  Accounts":       "accounts",
    "🎯  Opportunities":  "opportunities",
    "📋  Bids":           "bids",
    "📐  Estimating":     "estimating",
    "🔍  Intelligence":   "intelligence",
    "📑  Tenders":        "tenders",
    "📞  Calls":          "calls",
    "⏱  Lead Times":     "lead_times",
    "🏛  Frameworks":     "frameworks",
}

page_label = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
page = PAGES[page_label]

# Backend status indicator in the sidebar
alive = _health()
dot   = "🟢" if alive else "🔴"
st.sidebar.markdown(
    f"<div style='color:#94A3B8;font-size:0.72rem;margin-top:8px'>"
    f"{dot} Backend: {'online' if alive else 'offline'}</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"<div style='color:#64748B;font-size:0.65rem;margin-top:2px'>{API_URL}</div>",
    unsafe_allow_html=True,
)

st.sidebar.divider()
st.sidebar.caption("v0.1.0 · AI-native for DC")


# ══════════════════════════════════════════════════════════════════════════════
# Page: Dashboard
# ══════════════════════════════════════════════════════════════════════════════


def page_dashboard() -> None:
    st.title("⚡ Command Centre")
    st.caption("Global overview · Bid Intelligence OS")

    accounts   = _get("/accounts")     or []
    opps       = _get("/opportunities") or []
    bids       = _get("/bids")          or []
    tenders    = _get("/tenders")        or []

    active_opps  = [o for o in opps if o.get("stage") not in ("Won", "Lost")]
    active_bids  = [b for b in bids if b.get("status") not in ("won", "lost")]
    won_bids     = [b for b in bids if b.get("status") == "won"]
    closed_bids  = [b for b in bids if b.get("status") in ("won", "lost")]
    win_rate     = round(len(won_bids) / len(closed_bids) * 100) if closed_bids else 0

    # ── KPI metrics ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accounts",       len(accounts))
    c2.metric("Active Opportunities", len(active_opps))
    c3.metric("Active Bids",          len(active_bids))
    c4.metric("Win Rate",             f"{win_rate}%")

    st.divider()

    col_left, col_right = st.columns(2)

    # ── Pipeline value ───────────────────────────────────────────────────────
    with col_left:
        st.markdown("##### 📊 Pipeline by Stage")
        if opps:
            stage_counts: dict[str, int] = {}
            stage_values: dict[str, float] = {}
            for o in opps:
                s = o.get("stage", "unknown")
                stage_counts[s] = stage_counts.get(s, 0) + 1
                stage_values[s] = stage_values.get(s, 0.0) + (o.get("estimated_value") or 0)
            df_pipeline = pd.DataFrame(
                {
                    "Stage": list(stage_counts.keys()),
                    "Count": list(stage_counts.values()),
                    "Value (£)": [stage_values.get(s, 0) for s in stage_counts],
                }
            )
            st.dataframe(df_pipeline, use_container_width=True, hide_index=True)
        else:
            st.info("No opportunities yet.")

    # ── Recent bids ──────────────────────────────────────────────────────────
    with col_right:
        st.markdown("##### 📋 Recent Bids")
        if bids:
            recent = sorted(bids, key=lambda b: b.get("created_at") or "", reverse=True)[:6]
            df_bids = pd.DataFrame(
                [
                    {
                        "Title":  b.get("title"),
                        "Status": b.get("status"),
                        "Ref":    b.get("tender_ref") or "—",
                        "Due":    _fmt_date(b.get("submission_date")),
                    }
                    for b in recent
                ]
            )
            st.dataframe(df_bids, use_container_width=True, hide_index=True)
        else:
            st.info("No bids yet.")

    st.divider()

    # ── Tender intelligence snapshot ─────────────────────────────────────────
    st.markdown("##### 📑 Recent Tender Awards")
    if tenders:
        df_t = pd.DataFrame(
            [
                {
                    "Company":   t.get("company_name"),
                    "Value":     _fmt_money(t.get("contract_value")),
                    "Awarded":   _fmt_date(t.get("award_date")),
                    "Sector":    t.get("sector") or "—",
                    "Duration":  f"{t.get('contract_duration_months', '—')} mo",
                }
                for t in tenders[:8]
            ]
        )
        st.dataframe(df_t, use_container_width=True, hide_index=True)
    else:
        st.info("No tender awards recorded yet.")


# ══════════════════════════════════════════════════════════════════════════════
# Page: Accounts
# ══════════════════════════════════════════════════════════════════════════════


def page_accounts() -> None:
    st.title("🏢 Account Intel")
    st.caption("Target list · Contact mapping · Trigger signals")

    # ── Add account ──────────────────────────────────────────────────────────
    with st.expander("➕ Add New Account", expanded=False):
        with st.form("add_account"):
            col1, col2 = st.columns(2)
            name     = col1.text_input("Company Name *")
            acc_type = col2.selectbox(
                "Type *",
                ["operator", "hyperscaler", "developer", "colo", "enterprise"],
            )
            location = col1.text_input("Location")
            website  = col2.text_input("Website URL")
            stage    = col1.text_input("Stage (e.g. Prospect, Active)")
            tier     = col2.text_input("Tier Target (e.g. Tier III)")
            notes    = st.text_area("Notes")
            if st.form_submit_button("Create Account", type="primary"):
                if not name:
                    st.warning("Company name is required.")
                else:
                    payload = {
                        "name": name,
                        "type": acc_type,
                        "location": location or None,
                        "website":  website or None,
                        "stage":    stage or None,
                        "tier_target": tier or None,
                        "notes":    notes or None,
                    }
                    result = _post("/accounts", payload)
                    if result:
                        st.success(f"✅ Account '{result['name']}' created (ID {result['id']})")
                        st.rerun()

    # ── List accounts ────────────────────────────────────────────────────────
    accounts = _get("/accounts") or []
    if not accounts:
        st.info("No accounts yet. Add your first target above.")
        return

    search = st.text_input("🔍 Filter accounts", placeholder="Name, type or location…")
    if search:
        q = search.lower()
        accounts = [
            a for a in accounts
            if q in (a.get("name") or "").lower()
            or q in (a.get("type") or "").lower()
            or q in (a.get("location") or "").lower()
        ]

    df = pd.DataFrame(
        [
            {
                "ID":       a["id"],
                "Name":     a.get("name"),
                "Type":     a.get("type"),
                "Location": a.get("location") or "—",
                "Stage":    a.get("stage") or "—",
                "Tier":     a.get("tier_target") or "—",
                "Added":    _fmt_date(a.get("created_at")),
            }
            for a in accounts
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(accounts)} account(s)")

    # ── Account detail ───────────────────────────────────────────────────────
    st.divider()
    st.markdown("##### Account Detail")
    acct_names = {f"[{a['id']}] {a['name']}": a["id"] for a in accounts}
    chosen_label = st.selectbox("Select account", ["— select —"] + list(acct_names.keys()))
    if chosen_label != "— select —":
        acct_id = acct_names[chosen_label]
        acct = _get(f"/accounts/{acct_id}")
        if acct:
            col1, col2 = st.columns(2)
            col1.markdown(f"**Type:** {acct.get('type')}")
            col1.markdown(f"**Location:** {acct.get('location') or '—'}")
            col1.markdown(f"**Stage:** {acct.get('stage') or '—'}")
            col2.markdown(f"**Website:** {acct.get('website') or '—'}")
            col2.markdown(f"**Tier Target:** {acct.get('tier_target') or '—'}")
            col2.markdown(f"**Created:** {_fmt_date(acct.get('created_at'))}")
            if acct.get("notes"):
                st.markdown(f"**Notes:** {acct['notes']}")

        # Contacts
        contacts = _get(f"/accounts/{acct_id}/contacts") or []
        st.markdown(f"**Contacts** ({len(contacts)})")
        if contacts:
            df_c = pd.DataFrame(
                [
                    {
                        "Name":      c.get("name"),
                        "Role":      c.get("role") or "—",
                        "Email":     c.get("email") or "—",
                        "Phone":     c.get("phone") or "—",
                        "Influence": c.get("influence_level") or "—",
                    }
                    for c in contacts
                ]
            )
            st.dataframe(df_c, use_container_width=True, hide_index=True)
        else:
            st.caption("No contacts on record.")

        # Trigger Signals
        signals = _get(f"/accounts/{acct_id}/signals") or []
        st.markdown(f"**Trigger Signals** ({len(signals)})")
        if signals:
            df_s = pd.DataFrame(
                [
                    {
                        "Type":    s.get("signal_type"),
                        "Title":   s.get("title"),
                        "Status":  s.get("status"),
                        "Detected": _fmt_date(s.get("detected_at")),
                    }
                    for s in signals
                ]
            )
            st.dataframe(df_s, use_container_width=True, hide_index=True)
        else:
            st.caption("No trigger signals recorded.")


# ══════════════════════════════════════════════════════════════════════════════
# Page: Opportunities
# ══════════════════════════════════════════════════════════════════════════════


def page_opportunities() -> None:
    st.title("🎯 Opportunity Pipeline")
    st.caption("Qualify & track deals from Target → Won")

    accounts = _get("/accounts") or []
    acct_map = {a["id"]: a["name"] for a in accounts}

    # ── Add opportunity ──────────────────────────────────────────────────────
    with st.expander("➕ Add Opportunity", expanded=False):
        with st.form("add_opp"):
            col1, col2 = st.columns(2)
            title    = col1.text_input("Title *")
            acct_id_sel = col2.selectbox(
                "Account *",
                options=["— select —"] + [f"[{a['id']}] {a['name']}" for a in accounts],
            )
            stage    = col1.selectbox("Stage", ["target", "lead", "qualified", "bid", "won", "lost", "delivered"])
            value    = col2.number_input("Estimated Value (£)", min_value=0.0, step=1000.0)
            currency = col2.selectbox("Currency", ["GBP", "USD", "EUR"])
            desc     = st.text_area("Description")
            if st.form_submit_button("Create Opportunity", type="primary"):
                if not title or acct_id_sel == "— select —":
                    st.warning("Title and Account are required.")
                else:
                    acct_id = int(acct_id_sel.split("]")[0].lstrip("["))
                    result = _post(
                        "/opportunities",
                        {
                            "title": title,
                            "account_id": acct_id,
                            "stage": stage,
                            "estimated_value": value if value > 0 else None,
                            "currency": currency,
                            "description": desc or None,
                        },
                    )
                    if result:
                        st.success(f"✅ Opportunity '{result['title']}' created (ID {result['id']})")
                        st.rerun()

    # ── Pipeline board ───────────────────────────────────────────────────────
    opps = _get("/opportunities") or []
    if not opps:
        st.info("No opportunities yet.")
        return

    # Stage summary bar
    stages = ["target", "lead", "qualified", "bid", "won", "lost", "delivered"]
    stage_counts = {s: 0 for s in stages}
    for o in opps:
        s = (o.get("stage") or "target").lower()
        stage_counts[s] = stage_counts.get(s, 0) + 1

    cols = st.columns(len(stages))
    for col, s in zip(cols, stages):
        col.metric(s.title(), stage_counts.get(s, 0))

    st.divider()

    # Filter
    sel_stage = st.selectbox("Filter by stage", ["All"] + [s.title() for s in stages])
    filtered = opps if sel_stage == "All" else [
        o for o in opps if (o.get("stage") or "").lower() == sel_stage.lower()
    ]

    df = pd.DataFrame(
        [
            {
                "ID":      o["id"],
                "Title":   o.get("title"),
                "Account": acct_map.get(o.get("account_id"), "—"),
                "Stage":   o.get("stage"),
                "Value":   _fmt_money(o.get("estimated_value"), o.get("currency", "GBP")),
                "Created": _fmt_date(o.get("created_at")),
            }
            for o in filtered
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(filtered)} of {len(opps)} opportunities")

    # ── Qualification score tool ─────────────────────────────────────────────
    st.divider()
    st.markdown("##### 🧮 Go/No-Go Scoring")
    opp_choices = {f"[{o['id']}] {o['title']}": o["id"] for o in opps}
    sel_opp = st.selectbox("Select opportunity to score", ["— select —"] + list(opp_choices.keys()))
    if sel_opp != "— select —":
        opp_id = opp_choices[sel_opp]
        with st.form("score_opp"):
            sc1, sc2, sc3 = st.columns(3)
            budget_conf   = sc1.slider("Budget Confidence",       0.0, 10.0, 5.0, 0.5)
            route_clarity = sc2.slider("Route-to-Market Clarity", 0.0, 10.0, 5.0, 0.5)
            incumbent_risk= sc3.slider("Incumbent Lock-in Risk",  0.0, 10.0, 5.0, 0.5)
            timeline_real = sc1.slider("Timeline Realism",        0.0, 10.0, 5.0, 0.5)
            tech_fit      = sc2.slider("Technical Fit",           0.0, 10.0, 5.0, 0.5)
            rationale     = st.text_area("Rationale (optional)")
            if st.form_submit_button("Calculate Score", type="primary"):
                result = _post(
                    f"/opportunities/{opp_id}/qualify",
                    {
                        "budget_confidence": budget_conf,
                        "route_to_market_clarity": route_clarity,
                        "incumbent_lock_in_risk": incumbent_risk,
                        "procurement_timeline_realism": timeline_real,
                        "technical_fit": tech_fit,
                        "rationale": rationale or None,
                    },
                )
                if result:
                    decision_color = {"go": "green", "conditional": "orange", "no_go": "red"}.get(
                        result.get("recommendation", ""), "blue"
                    )
                    st.markdown(
                        f"**Overall Score:** `{result.get('overall_score', '—')} / 10`  "
                        f" &nbsp; **Decision:** :{decision_color}[{result.get('recommendation', '—').upper()}]"
                    )


# ══════════════════════════════════════════════════════════════════════════════
# Page: Bids
# ══════════════════════════════════════════════════════════════════════════════


def page_bids() -> None:
    st.title("📋 Bid Pack Builder")
    st.caption("Assemble, track and manage bid submissions")

    opps = _get("/opportunities") or []
    opp_map = {o["id"]: o["title"] for o in opps}

    # ── Add bid ──────────────────────────────────────────────────────────────
    with st.expander("➕ New Bid", expanded=False):
        with st.form("add_bid"):
            col1, col2 = st.columns(2)
            title    = col1.text_input("Bid Title *")
            opp_sel  = col2.selectbox(
                "Opportunity *",
                ["— select —"] + [f"[{o['id']}] {o['title']}" for o in opps],
            )
            tender_ref      = col1.text_input("Tender Reference")
            status          = col2.selectbox("Status", ["draft", "review", "submitted", "won", "lost"])
            submission_date = col1.date_input("Submission Date", value=None)
            win_themes      = st.text_area("Win Themes")
            notes           = st.text_area("Notes")
            if st.form_submit_button("Create Bid", type="primary"):
                if not title or opp_sel == "— select —":
                    st.warning("Title and Opportunity are required.")
                else:
                    opp_id = int(opp_sel.split("]")[0].lstrip("["))
                    result = _post(
                        "/bids",
                        {
                            "title": title,
                            "opportunity_id": opp_id,
                            "tender_ref": tender_ref or None,
                            "status": status,
                            "submission_date": submission_date.isoformat() if submission_date else None,
                            "win_themes": win_themes or None,
                            "notes": notes or None,
                        },
                    )
                    if result:
                        st.success(f"✅ Bid '{result['title']}' created (ID {result['id']})")
                        st.rerun()

    # ── List bids ────────────────────────────────────────────────────────────
    bids = _get("/bids") or []
    if not bids:
        st.info("No bids yet.")
        return

    filter_status = st.selectbox(
        "Filter by status", ["All", "draft", "review", "submitted", "won", "lost"]
    )
    filtered = bids if filter_status == "All" else [
        b for b in bids if b.get("status") == filter_status
    ]

    df = pd.DataFrame(
        [
            {
                "ID":          b["id"],
                "Title":       b.get("title"),
                "Opportunity": opp_map.get(b.get("opportunity_id"), "—"),
                "Status":      b.get("status"),
                "Ref":         b.get("tender_ref") or "—",
                "Due":         _fmt_date(b.get("submission_date")),
                "Created":     _fmt_date(b.get("created_at")),
            }
            for b in filtered
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(filtered)} bid(s)")

    # ── Bid detail: documents and RFIs ───────────────────────────────────────
    st.divider()
    st.markdown("##### Bid Detail")
    bid_choices = {f"[{b['id']}] {b['title']}": b["id"] for b in bids}
    sel_bid = st.selectbox("Select bid", ["— select —"] + list(bid_choices.keys()))
    if sel_bid != "— select —":
        bid_id = bid_choices[sel_bid]

        col_docs, col_rfis = st.columns(2)

        with col_docs:
            st.markdown("**Documents**")
            docs = _get(f"/bids/{bid_id}/documents") or []
            if docs:
                df_d = pd.DataFrame(
                    [
                        {
                            "Filename": d.get("filename"),
                            "Type":     d.get("doc_type") or "—",
                            "Uploaded": _fmt_date(d.get("uploaded_at")),
                        }
                        for d in docs
                    ]
                )
                st.dataframe(df_d, use_container_width=True, hide_index=True)
            else:
                st.caption("No documents uploaded.")

        with col_rfis:
            st.markdown("**RFIs**")
            rfis = _get(f"/bids/{bid_id}/rfis") or []
            if rfis:
                df_r = pd.DataFrame(
                    [
                        {
                            "Question":  r.get("question", "")[:60],
                            "Priority":  r.get("priority"),
                            "Status":    r.get("status"),
                            "Due":       _fmt_date(r.get("due_date")),
                        }
                        for r in rfis
                    ]
                )
                st.dataframe(df_r, use_container_width=True, hide_index=True)
            else:
                st.caption("No RFIs yet.")

        # Compliance matrix
        st.markdown("**Compliance Matrix**")
        compliance = _get(f"/bids/{bid_id}/compliance") or []
        if compliance:
            df_comp = pd.DataFrame(
                [
                    {
                        "Requirement":   c.get("requirement", "")[:80],
                        "Status":        c.get("compliance_status"),
                        "Evidence":      c.get("evidence_ref") or "—",
                    }
                    for c in compliance
                ]
            )
            st.dataframe(df_comp, use_container_width=True, hide_index=True)
        else:
            st.caption("No compliance items yet.")

    # ── Export downloads ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("##### 📥 Export")
    col_pdf, col_word, col_xl = st.columns(3)
    col_pdf.markdown(
        f"[⬇ Pursuit Pack PDF]({API_URL}/bids/{bid_id}/export/pursuit-pack-pdf)",
        unsafe_allow_html=True,
    )
    col_word.markdown(
        f"[⬇ Tender Response Word]({API_URL}/bids/{bid_id}/export/tender-response-docx)",
        unsafe_allow_html=True,
    )
    col_xl.markdown(
        f"[⬇ Compliance Matrix Excel]({API_URL}/bids/{bid_id}/export/compliance-matrix-xlsx)",
        unsafe_allow_html=True,
    )

    # ── Bid debrief ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("##### 📝 Bid Debrief")
    existing_debrief = _get(f"/bids/{bid_id}/debrief")
    if existing_debrief:
        out = existing_debrief.get("outcome", "—")
        outcome_icon = {"won": "🏆", "lost": "❌", "withdrawn": "↩️", "no_award": "⚪"}.get(out, "?")
        st.markdown(f"**Outcome:** {outcome_icon} {out.replace('_', ' ').title()}")
        cols = st.columns(4)
        if existing_debrief.get("our_score") is not None:
            cols[0].metric("Our Score",    existing_debrief["our_score"])
        if existing_debrief.get("winner_score") is not None:
            cols[1].metric("Winner Score", existing_debrief["winner_score"])
        if existing_debrief.get("our_price") and existing_debrief.get("winner_price"):
            gap = (existing_debrief["our_price"] - existing_debrief["winner_price"]) / existing_debrief["winner_price"] * 100
            cols[2].metric("Price Gap", f"{gap:+.1f}%")
        if existing_debrief.get("winning_company"):
            cols[3].metric("Winner", existing_debrief["winning_company"])
        if existing_debrief.get("strengths"):
            st.markdown(f"**Strengths:** {existing_debrief['strengths']}")
        if existing_debrief.get("weaknesses"):
            st.markdown(f"**Weaknesses:** {existing_debrief['weaknesses']}")
        if existing_debrief.get("lessons_learned"):
            st.info(f"💡 **Lessons:** {existing_debrief['lessons_learned']}")

    with st.expander("✏️ Record / Update Debrief", expanded=existing_debrief is None):
        with st.form("bid_debrief_form"):
            col1, col2 = st.columns(2)
            outcome  = col1.selectbox("Outcome *", ["won", "lost", "withdrawn", "no_award"],
                                      index=["won","lost","withdrawn","no_award"].index(
                                          existing_debrief.get("outcome", "lost")) if existing_debrief else 1)
            winner_co = col2.text_input("Winning company",
                                         value=existing_debrief.get("winning_company","") if existing_debrief else "")
            c1, c2, c3, c4 = st.columns(4)
            our_score    = c1.number_input("Our score",    0.0, 10.0, float(existing_debrief.get("our_score") or 0) if existing_debrief else 0.0, 0.1)
            win_score    = c2.number_input("Winner score", 0.0, 10.0, float(existing_debrief.get("winner_score") or 0) if existing_debrief else 0.0, 0.1)
            our_price    = c3.number_input("Our price £",  0.0, step=10000.0, value=float(existing_debrief.get("our_price") or 0) if existing_debrief else 0.0)
            win_price    = c4.number_input("Winner price £", 0.0, step=10000.0, value=float(existing_debrief.get("winner_price") or 0) if existing_debrief else 0.0)
            feedback = st.text_area("Client feedback", value=existing_debrief.get("client_feedback","") if existing_debrief else "")
            strengths= st.text_area("Strengths",       value=existing_debrief.get("strengths","") if existing_debrief else "")
            weaknesses=st.text_area("Weaknesses",      value=existing_debrief.get("weaknesses","") if existing_debrief else "")
            lessons  = st.text_area("Lessons learned", value=existing_debrief.get("lessons_learned","") if existing_debrief else "")
            improvements=st.text_area("Process improvements", value=existing_debrief.get("process_improvements","") if existing_debrief else "")
            bid_mgr  = st.text_input("Bid manager",    value=existing_debrief.get("bid_manager","") if existing_debrief else "")
            if st.form_submit_button("Save Debrief", type="primary"):
                payload = {
                    "bid_id": bid_id, "outcome": outcome,
                    "our_score":    our_score    if our_score    > 0 else None,
                    "winner_score": win_score    if win_score    > 0 else None,
                    "our_price":    our_price    if our_price    > 0 else None,
                    "winner_price": win_price    if win_price    > 0 else None,
                    "client_feedback":      feedback     or None,
                    "strengths":            strengths    or None,
                    "weaknesses":           weaknesses   or None,
                    "winning_company":      winner_co    or None,
                    "lessons_learned":      lessons      or None,
                    "process_improvements": improvements or None,
                    "bid_manager":          bid_mgr      or None,
                }
                if existing_debrief:
                    try:
                        import requests as _req
                        r = _req.patch(f"{API_URL}/bids/{bid_id}/debrief", json=payload, timeout=10)
                        r.raise_for_status()
                        st.success("✅ Debrief updated")
                    except Exception as exc:
                        st.error(f"Update failed: {exc}")
                else:
                    result = _post(f"/bids/{bid_id}/debrief", payload)
                    if result:
                        st.success("✅ Debrief saved")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Page: Estimating
# ══════════════════════════════════════════════════════════════════════════════


def page_estimating() -> None:
    st.title("📐 Estimating & Scope Gap")
    st.caption("Detect scope omissions before they become commercial liabilities")

    bids = _get("/bids") or []
    bid_map = {b["id"]: b["title"] for b in bids}

    # ── Add project ──────────────────────────────────────────────────────────
    with st.expander("➕ New Estimating Project", expanded=False):
        with st.form("add_est"):
            col1, col2 = st.columns(2)
            title        = col1.text_input("Project Title *")
            bid_sel      = col2.selectbox(
                "Link to Bid *",
                ["— select —"] + [f"[{b['id']}] {b['title']}" for b in bids],
            )
            proj_type    = col1.selectbox("Project Type", ["Refurb", "New Build", "Extension"])
            tier         = col2.selectbox("Tier Level", ["Tier I", "Tier II", "Tier III", "Tier IV"])
            budget       = col1.number_input("Budget (£)", min_value=0.0, step=10000.0)
            notes        = st.text_area("Notes")
            if st.form_submit_button("Create Project", type="primary"):
                if not title or bid_sel == "— select —":
                    st.warning("Title and Bid are required.")
                else:
                    bid_id = int(bid_sel.split("]")[0].lstrip("["))
                    result = _post(
                        "/estimating",
                        {
                            "title": title,
                            "bid_id": bid_id,
                            "project_type": proj_type,
                            "tier_level": tier,
                            "total_budget": budget if budget > 0 else None,
                            "notes": notes or None,
                        },
                    )
                    if result:
                        st.success(f"✅ Project '{result.get('title', title)}' created")
                        st.rerun()

    # ── List projects ────────────────────────────────────────────────────────
    projects = _get("/estimating") or []
    if not projects:
        st.info("No estimating projects yet.")
        return

    df = pd.DataFrame(
        [
            {
                "ID":           p["id"],
                "Title":        p.get("title") or f"Project {p['id']}",
                "Bid":          bid_map.get(p.get("bid_id"), "—"),
                "Type":         p.get("project_type"),
                "Tier":         p.get("tier_level") or "—",
                "Budget":       _fmt_money(p.get("total_budget")),
                "Gap Score":    p.get("scope_gap_score") or "—",
                "Created":      _fmt_date(p.get("created_at")),
            }
            for p in projects
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Scope gap detail ─────────────────────────────────────────────────────
    st.divider()
    st.markdown("##### Scope Gap Analysis")
    proj_choices = {
        f"[{p['id']}] {p.get('title') or 'Project ' + str(p['id'])}": p["id"]
        for p in projects
    }
    sel_proj = st.selectbox("Select project", ["— select —"] + list(proj_choices.keys()))
    if sel_proj != "— select —":
        proj_id = proj_choices[sel_proj]

        col_gaps, col_checks = st.columns(2)

        with col_gaps:
            st.markdown("**Scope Gaps**")
            gaps = _get(f"/estimating/{proj_id}/scope-gaps") or []
            if gaps:
                df_g = pd.DataFrame(
                    [
                        {
                            "Category":    g.get("category"),
                            "Risk":        g.get("risk_level"),
                            "Description": (g.get("description") or "")[:60],
                            "Identified":  "✅" if g.get("identified") else "❌",
                            "In Price":    "✅" if g.get("included_in_price") else "❌",
                        }
                        for g in gaps
                    ]
                )
                st.dataframe(df_g, use_container_width=True, hide_index=True)
            else:
                st.caption("No scope gaps recorded.")

        with col_checks:
            st.markdown("**Checklist**")
            checks = _get(f"/estimating/{proj_id}/checklist") or []
            if checks:
                for item in checks:
                    label  = item.get("description") or item.get("item") or "Item"
                    done   = item.get("completed", False)
                    icon   = "✅" if done else "⬜"
                    st.markdown(f"{icon} {label}")
            else:
                st.caption("No checklist items yet.")

        # Gap report
        report = _get(f"/estimating/{proj_id}/scope-gap-report")
        if report:
            score = report.get("score") or report.get("gap_score")
            if score is not None:
                colour = "green" if score <= 3 else "orange" if score <= 6 else "red"
                st.markdown(f"**Composite Gap Score:** :{colour}[{score} / 10]")


# ══════════════════════════════════════════════════════════════════════════════
# Page: Intelligence
# ══════════════════════════════════════════════════════════════════════════════


def page_intelligence() -> None:
    st.title("🔍 Account Intelligence")
    st.caption("AI-powered company research — powered by Grok")

    # ── Research a company ───────────────────────────────────────────────────
    with st.expander("🌐 Research a Company Website", expanded=False):
        with st.form("research_company"):
            website = st.text_input(
                "Company website URL", placeholder="https://equinix.com"
            )
            if st.form_submit_button("Run Deep Research", type="primary"):
                if not website:
                    st.warning("Enter a URL.")
                else:
                    with st.spinner("Crawling and analysing… (this may take ~15s)"):
                        result = _post("/intel/company", {"website": website})
                    if result:
                        st.success(f"✅ Intel captured for **{result.get('company_name', website)}**")
                        if result.get("intel_summary"):
                            st.info(result["intel_summary"])
                        st.rerun()

    # ── Company intel list ───────────────────────────────────────────────────
    companies = _get("/intel/companies") or []
    if not companies:
        st.info("No intelligence snapshots yet. Use the form above to research a company.")
        return

    df = pd.DataFrame(
        [
            {
                "ID":      c["id"],
                "Company": c.get("company_name") or c.get("website"),
                "Website": c.get("website"),
                "Created": _fmt_date(c.get("created_at")),
            }
            for c in companies
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Intel detail ─────────────────────────────────────────────────────────
    st.divider()
    comp_choices = {
        f"[{c['id']}] {c.get('company_name') or c.get('website')}": c["id"]
        for c in companies
    }
    sel_comp = st.selectbox("View full intel", ["— select —"] + list(comp_choices.keys()))
    if sel_comp != "— select —":
        comp_id = comp_choices[sel_comp]
        intel   = _get(f"/intel/companies/{comp_id}")
        if intel:
            col1, col2 = st.columns(2)
            col1.markdown(f"**Website:** {intel.get('website') or '—'}")
            col1.markdown(f"**Business Model:** {intel.get('business_model') or '—'}")
            col2.markdown(f"**Locations:** {intel.get('locations') or '—'}")
            col2.markdown(f"**Stock Ticker:** {intel.get('stock_ticker') or '—'}")

            if intel.get("expansion_signals"):
                st.markdown(f"**Expansion Signals:** {intel['expansion_signals']}")
            if intel.get("bid_opportunities"):
                st.markdown(f"**Bid Opportunities:** {intel['bid_opportunities']}")
            if intel.get("intel_summary"):
                st.info(intel["intel_summary"])
            if intel.get("suggested_touchpoint"):
                st.markdown("**Suggested Touchpoint:**")
                st.code(intel["suggested_touchpoint"], language=None)

    # ── News feed ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("##### 📰 Tracked News")
    news = _get("/intel/news") or []
    if news:
        for item in news[:10]:
            with st.container(border=True):
                cols = st.columns([3, 1])
                cols[0].markdown(f"**{item.get('headline')}**")
                cols[1].caption(f"{item.get('category', '')} · {_fmt_date(item.get('published_at'))}")
                if item.get("source_url"):
                    cols[0].markdown(f"[Read more]({item['source_url']})")
    else:
        st.caption("No news items yet.")


# ══════════════════════════════════════════════════════════════════════════════
# Page: Tenders
# ══════════════════════════════════════════════════════════════════════════════


def page_tenders() -> None:
    st.title("📑 Tender Award Intelligence")
    st.caption("Track competitor wins, CPI scoring, and win probability")

    # ── Add tender award ─────────────────────────────────────────────────────
    with st.expander("➕ Record Tender Award", expanded=False):
        with st.form("add_tender"):
            col1, col2 = st.columns(2)
            company_name     = col1.text_input("Winning Company *")
            contractor       = col2.text_input("Awarded To (your company or competitor)")
            contract_value   = col1.number_input("Contract Value (£)", min_value=0.0, step=10000.0)
            award_date       = col2.date_input("Award Date", value=None)
            duration_months  = col1.number_input("Duration (months)", min_value=0, step=1)
            tier_level       = col2.selectbox("Tier Level", ["—", "Tier I", "Tier II", "Tier III", "Tier IV"])
            sector           = col1.text_input("Sector (e.g. Hyperscale, Colo)")
            source_url       = col2.text_input("Source URL")
            notes            = st.text_area("Notes")
            if st.form_submit_button("Add Award", type="primary"):
                if not company_name:
                    st.warning("Company name is required.")
                else:
                    result = _post(
                        "/tenders",
                        {
                            "company_name":           company_name,
                            "awarded_to":             contractor or None,
                            "contract_value":         contract_value if contract_value > 0 else None,
                            "award_date":             award_date.isoformat() if award_date else None,
                            "contract_duration_months": int(duration_months) if duration_months > 0 else None,
                            "tier_level":             tier_level if tier_level != "—" else None,
                            "sector":                 sector or None,
                            "source_url":             source_url or None,
                            "notes":                  notes or None,
                        },
                    )
                    if result:
                        st.success(f"✅ Award recorded (ID {result['id']})")
                        st.rerun()

    # ── List awards ──────────────────────────────────────────────────────────
    tenders = _get("/tenders") or []
    if not tenders:
        st.info("No tender awards recorded yet.")
        return

    search = st.text_input("🔍 Filter by company")
    if search:
        tenders = [t for t in tenders if search.lower() in (t.get("company_name") or "").lower()]

    df = pd.DataFrame(
        [
            {
                "ID":       t["id"],
                "Company":  t.get("company_name"),
                "Value":    _fmt_money(t.get("contract_value")),
                "Awarded":  _fmt_date(t.get("award_date")),
                "Duration": f"{t.get('contract_duration_months', '—')} mo",
                "Tier":     t.get("tier_level") or "—",
                "Sector":   t.get("sector") or "—",
            }
            for t in tenders
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(tenders)} award(s)")

    # ── Win probability scorer ───────────────────────────────────────────────
    st.divider()
    st.markdown("##### 🎯 Win Probability Scorer")
    with st.form("win_score"):
        col1, col2, col3 = st.columns(3)
        company  = col1.text_input("Company *")
        rel_score  = col2.slider("Relationship Score",     0.0, 10.0, 5.0, 0.5)
        tech_score = col3.slider("Technical Fit",          0.0, 10.0, 5.0, 0.5)
        price_comp = col1.slider("Price Competitiveness",  0.0, 10.0, 5.0, 0.5)
        track_rec  = col2.slider("Track Record Relevance", 0.0, 10.0, 5.0, 0.5)
        if st.form_submit_button("Calculate Win %", type="primary"):
            if not company:
                st.warning("Company is required.")
            else:
                result = _post(
                    "/tenders/score/win",
                    {
                        "company_name":           company,
                        "relationship_score":     rel_score,
                        "technical_fit":          tech_score,
                        "price_competitiveness":  price_comp,
                        "track_record_relevance": track_rec,
                    },
                )
                if result:
                    prob = result.get("win_probability") or result.get("probability")
                    if prob is not None:
                        colour = "green" if prob >= 60 else "orange" if prob >= 40 else "red"
                        st.markdown(f"**Win Probability:** :{colour}[{prob:.0f}%]")
                    if result.get("recommendation"):
                        st.info(result["recommendation"])


# ══════════════════════════════════════════════════════════════════════════════
# Page: Calls
# ══════════════════════════════════════════════════════════════════════════════


def page_calls() -> None:
    st.title("📞 Call Intelligence")
    st.caption("AI analysis of executive call transcripts")

    # ── Analyse a call ───────────────────────────────────────────────────────
    with st.expander("➕ Analyse New Call", expanded=False):
        with st.form("analyse_call"):
            col1, col2 = st.columns(2)
            company_name   = col1.text_input("Company Name")
            executive_name = col2.text_input("Executive Name")
            transcript     = st.text_area(
                "Call Transcript *",
                placeholder="Paste the full call transcript here…",
                height=200,
            )
            if st.form_submit_button("Run AI Analysis", type="primary"):
                if not transcript:
                    st.warning("Transcript is required.")
                else:
                    with st.spinner("Analysing transcript… (this may take ~15s)"):
                        result = _post(
                            "/calls/analyse",
                            {
                                "company_name":   company_name or None,
                                "executive_name": executive_name or None,
                                "transcript":     transcript,
                            },
                        )
                    if result:
                        st.success("✅ Call analysed")
                        if result.get("sentiment_score") is not None:
                            s = result["sentiment_score"]
                            colour = "green" if s >= 0.6 else "orange" if s >= 0.4 else "red"
                            st.markdown(f"**Sentiment:** :{colour}[{s:.2f}]")
                        st.rerun()

    # ── List calls ───────────────────────────────────────────────────────────
    calls = _get("/calls") or []
    if not calls:
        st.info("No call records yet. Analyse a transcript above.")
        return

    filter_co = st.text_input("🔍 Filter by company")
    if filter_co:
        calls = [c for c in calls if filter_co.lower() in (c.get("company_name") or "").lower()]

    df = pd.DataFrame(
        [
            {
                "ID":        c["id"],
                "Company":   c.get("company_name") or "—",
                "Executive": c.get("executive_name") or "—",
                "Sentiment": f"{c['sentiment_score']:.2f}" if c.get("sentiment_score") is not None else "—",
                "Analysed":  _fmt_date(c.get("created_at")),
            }
            for c in calls
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(calls)} call record(s)")

    # ── Call detail ──────────────────────────────────────────────────────────
    st.divider()
    call_choices = {
        f"[{c['id']}] {c.get('company_name', '—')} – {c.get('executive_name', 'Unknown')}": c["id"]
        for c in calls
    }
    sel_call = st.selectbox("View call detail", ["— select —"] + list(call_choices.keys()))
    if sel_call != "— select —":
        call_id = call_choices[sel_call]
        call    = next((c for c in calls if c["id"] == call_id), None)
        if call:
            col1, col2 = st.columns(2)
            with col1:
                if call.get("key_points"):
                    st.markdown("**Key Points**")
                    for kp in call["key_points"]:
                        if isinstance(kp, dict):
                            st.markdown(f"- {kp.get('text') or kp.get('point') or str(kp)}")
                        else:
                            st.markdown(f"- {kp}")
            with col2:
                if call.get("next_steps"):
                    st.markdown("**Next Steps**")
                    ns = call["next_steps"]
                    if isinstance(ns, list):
                        for step in ns:
                            st.markdown(f"- {step}")
                    else:
                        st.markdown(ns)
                if call.get("budget_signals"):
                    st.markdown("**Budget Signals**")
                    for s in (call["budget_signals"] or []):
                        st.markdown(f"- {s}")



# ══════════════════════════════════════════════════════════════════════════════
# Page: Lead Times
# ══════════════════════════════════════════════════════════════════════════════


def page_lead_times() -> None:
    st.title("⏱ Lead-Time Intelligence")
    st.caption("Equipment delivery windows — switchgear, UPS, chillers, generators & more")

    CATEGORIES = [
        "switchgear", "ups", "chiller", "generator", "pdu",
        "crac", "transformer", "busbar", "battery", "other",
    ]
    CAT_ICONS = {
        "switchgear": "⚡", "ups": "🔋", "chiller": "❄️", "generator": "🛢️",
        "pdu": "🔌", "crac": "💨", "transformer": "🔧", "busbar": "📊",
        "battery": "🔋", "other": "📦",
    }

    col_filter, col_region, col_seed = st.columns([2, 2, 1])
    with col_filter:
        cat_filter = st.selectbox("Category", ["All"] + CATEGORIES, key="lt_cat")
    with col_region:
        region_filter = st.text_input("Region", placeholder="e.g. UK", key="lt_region")
    with col_seed:
        st.write("")
        if st.button("⚡ Seed Defaults", help="Load default dataset"):
            result = _post("/lead-times/seed", {})
            if result is not None:
                if isinstance(result, list) and len(result) == 0:
                    st.info("All default items already loaded.")
                else:
                    st.success(f"✅ Seeded {len(result) if isinstance(result, list) else '?'} items")
                st.rerun()

    params: dict = {}
    if cat_filter != "All":
        params["category"] = cat_filter
    if region_filter:
        params["region"] = region_filter

    items = _get("/lead-times", params=params) or []
    if not items:
        st.info("No lead-time data. Use ⚡ Seed Defaults to load standard DC equipment data.")
        return

    # Colour-code lead time
    def lt_colour(weeks_min: int) -> str:
        if weeks_min <= 12:
            return "🟢"
        if weeks_min <= 24:
            return "🟡"
        return "🔴"

    df = pd.DataFrame(
        [
            {
                "Cat": CAT_ICONS.get(i.get("category", ""), "📦"),
                "Category":      i.get("category"),
                "Manufacturer":  i.get("manufacturer") or "—",
                "Model":         i.get("model_ref") or "—",
                "Description":   (i.get("description") or "")[:60],
                "Lead (weeks)":  f"{lt_colour(i.get('lead_weeks_min', 0))} {i.get('lead_weeks_min')}–{i.get('lead_weeks_max')}w",
                "Typical":       f"{i.get('lead_weeks_typical', '—')}w" if i.get("lead_weeks_typical") else "—",
                "Region":        i.get("region") or "—",
                "Source":        i.get("source") or "—",
            }
            for i in items
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(items)} item(s)")

    # ── Add item form ─────────────────────────────────────────────────────────
    st.divider()
    with st.expander("➕ Add Lead-Time Item", expanded=False):
        with st.form("add_lt"):
            col1, col2 = st.columns(2)
            cat      = col1.selectbox("Category *", CATEGORIES)
            mfr      = col2.text_input("Manufacturer")
            model    = col1.text_input("Model Ref")
            region   = col2.text_input("Region", value="UK")
            desc     = st.text_input("Description *")
            col3, col4, col5 = st.columns(3)
            wmin = col3.number_input("Min weeks *", min_value=1, step=1)
            wmax = col4.number_input("Max weeks *", min_value=1, step=1)
            source = col5.text_input("Source")
            notes  = st.text_area("Notes")
            if st.form_submit_button("Add Item", type="primary"):
                if not desc:
                    st.warning("Description is required.")
                elif wmax < wmin:
                    st.warning("Max weeks must be ≥ min weeks.")
                else:
                    result = _post("/lead-times", {
                        "category": cat, "manufacturer": mfr or None, "model_ref": model or None,
                        "description": desc, "lead_weeks_min": int(wmin), "lead_weeks_max": int(wmax),
                        "region": region or None, "source": source or None, "notes": notes or None,
                    })
                    if result:
                        st.success(f"✅ Item added (ID {result['id']})")
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Page: Frameworks
# ══════════════════════════════════════════════════════════════════════════════


def page_frameworks() -> None:
    st.title("🏛 Procurement Frameworks")
    st.caption("Track framework agreements, DPS, and procurement routes")

    STATUS_ICONS = {
        "active": "🟢", "expiring_soon": "🟡", "expired": "🔴",
        "pending": "🔵", "not_listed": "⚪",
    }

    col_status, col_listed = st.columns(2)
    with col_status:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "active", "expiring_soon", "expired", "pending", "not_listed"],
            key="fw_status",
        )
    with col_listed:
        listed_filter = st.selectbox(
            "Listing status",
            ["All", "We are listed", "Not listed"],
            key="fw_listed",
        )

    params: dict = {}
    if status_filter != "All":
        params["status"] = status_filter
    if listed_filter == "We are listed":
        params["we_are_listed"] = "true"
    elif listed_filter == "Not listed":
        params["we_are_listed"] = "false"

    frameworks = _get("/frameworks", params=params) or []

    # KPIs
    if frameworks:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Active",        sum(1 for f in frameworks if f.get("status") == "active"))
        col2.metric("We Are Listed", sum(1 for f in frameworks if f.get("we_are_listed")))
        col3.metric("Expiring Soon", sum(1 for f in frameworks if f.get("status") == "expiring_soon"))
        col4.metric("Expired",       sum(1 for f in frameworks if f.get("status") == "expired"))

    if not frameworks:
        st.info("No frameworks yet. Add one below.")
    else:
        df = pd.DataFrame(
            [
                {
                    "Status":    STATUS_ICONS.get(f.get("status", ""), "⚪") + " " + f.get("status", ""),
                    "Name":      f.get("name"),
                    "Authority": f.get("authority"),
                    "Reference": f.get("reference") or "—",
                    "Listed?":   "✅" if f.get("we_are_listed") else "—",
                    "Expiry":    f.get("expiry_date") or "—",
                    "Region":    f.get("region") or "—",
                }
                for f in frameworks
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(frameworks)} framework(s)")

    # ── Add / Edit form ───────────────────────────────────────────────────────
    st.divider()
    with st.expander("➕ Add Framework", expanded=False):
        with st.form("add_fw"):
            col1, col2 = st.columns(2)
            name      = col1.text_input("Framework Name *")
            authority = col2.text_input("Contracting Authority *")
            reference = col1.text_input("Reference / Lot")
            region    = col2.text_input("Region", value="UK")
            status    = col1.selectbox(
                "Status", ["active", "expiring_soon", "expired", "pending", "not_listed"]
            )
            we_listed = col2.checkbox("We are listed")
            start_d   = col1.date_input("Start Date", value=None)
            expiry_d  = col2.date_input("Expiry Date", value=None)
            url       = st.text_input("Framework URL")
            notes     = st.text_area("Notes")
            if st.form_submit_button("Add Framework", type="primary"):
                if not name or not authority:
                    st.warning("Name and Authority are required.")
                else:
                    result = _post("/frameworks", {
                        "name": name, "authority": authority,
                        "reference": reference or None, "region": region or None,
                        "status": status, "we_are_listed": we_listed,
                        "start_date":  start_d.isoformat()  if start_d  else None,
                        "expiry_date": expiry_d.isoformat() if expiry_d else None,
                        "url": url or None, "notes": notes or None,
                    })
                    if result:
                        st.success(f"✅ Framework added (ID {result['id']})")
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════════════════════

_PAGE_HANDLERS = {
    "dashboard":    page_dashboard,
    "accounts":     page_accounts,
    "opportunities": page_opportunities,
    "bids":         page_bids,
    "estimating":   page_estimating,
    "intelligence": page_intelligence,
    "tenders":      page_tenders,
    "calls":        page_calls,
    "lead_times":   page_lead_times,
    "frameworks":   page_frameworks,
}

_PAGE_HANDLERS[page]()
