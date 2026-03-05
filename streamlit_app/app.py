"""
aLiGN Analytics Dashboard – Streamlit app.

Connects to the aLiGN FastAPI backend and surfaces key pipeline metrics.

Deploy to Streamlit Cloud (https://share.streamlit.io):
  1. Fork / push this repo to GitHub.
  2. Create a new app on Streamlit Cloud pointing to this file.
  3. Set ALIGN_API_URL in Streamlit Cloud's "Secrets" section:
       ALIGN_API_URL = "https://your-backend.example.com/api/v1"

Local development:
  pip install -r streamlit_app/requirements.txt
  ALIGN_API_URL=http://localhost:8000/api/v1 streamlit run streamlit_app/app.py
"""

import os
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

# ── Configuration ─────────────────────────────────────────────────────────────

API_URL = os.getenv("ALIGN_API_URL", st.secrets.get("ALIGN_API_URL", "http://localhost:8000/api/v1"))

st.set_page_config(
    page_title="aLiGN Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Helpers ───────────────────────────────────────────────────────────────────


@st.cache_data(ttl=60)
def fetch(path: str) -> list | dict:
    """Fetch JSON from the aLiGN API, returning an empty list on error."""
    try:
        r = requests.get(f"{API_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Could not load {path}: {exc}")
        return []


def safe_count(data) -> int:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict) and "total" in data:
        return data["total"]
    return 0


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://raw.githubusercontent.com/flencrypto/aLiGN/main/frontend/app/favicon.ico", width=48)
    st.title("aLiGN")
    st.caption("AI-native Bid + Delivery OS")
    st.markdown("---")
    st.markdown(f"**Backend:** `{API_URL}`")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

# ── Health check ──────────────────────────────────────────────────────────────

health = fetch("/health" if API_URL.endswith("/api/v1") else "/../health")
if isinstance(health, dict) and health.get("status") == "ok":
    st.sidebar.success("Backend connected ✅")
else:
    st.sidebar.error("Backend unreachable ❌")

# ── Load data ─────────────────────────────────────────────────────────────────

accounts = fetch("/accounts")
opportunities = fetch("/opportunities")
bids = fetch("/bids")
signals = fetch("/trigger-signals")

# ── KPI strip ─────────────────────────────────────────────────────────────────

st.title("🎯 aLiGN Pipeline Dashboard")
st.caption(f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Accounts", safe_count(accounts))
col2.metric("Opportunities", safe_count(opportunities))
col3.metric("Bids", safe_count(bids))
col4.metric("Trigger Signals", safe_count(signals))

st.markdown("---")

# ── Opportunity pipeline ──────────────────────────────────────────────────────

st.subheader("📌 Opportunity Pipeline")

if opportunities:
    df_opp = pd.DataFrame(opportunities)

    # Stage breakdown
    if "stage" in df_opp.columns:
        stage_counts = df_opp["stage"].value_counts().reset_index()
        stage_counts.columns = ["Stage", "Count"]
        st.bar_chart(stage_counts.set_index("Stage"))

    # Recent opportunities table
    cols_to_show = [c for c in ["name", "stage", "value_gbp", "go_no_go", "created_at"] if c in df_opp.columns]
    if cols_to_show:
        st.dataframe(df_opp[cols_to_show].head(20), use_container_width=True)
else:
    st.info("No opportunities found. Add some via the aLiGN web UI.")

# ── Account list ──────────────────────────────────────────────────────────────

st.subheader("🗺️ Account Intelligence")

if accounts:
    df_acc = pd.DataFrame(accounts)
    cols_to_show = [c for c in ["name", "type", "stage", "location", "tier_target"] if c in df_acc.columns]
    if cols_to_show:
        st.dataframe(df_acc[cols_to_show].head(30), use_container_width=True)
else:
    st.info("No accounts found.")

# ── Bids ──────────────────────────────────────────────────────────────────────

st.subheader("📦 Active Bids")

if bids:
    df_bid = pd.DataFrame(bids)
    cols_to_show = [c for c in ["title", "status", "submission_deadline", "value_gbp"] if c in df_bid.columns]
    if cols_to_show:
        st.dataframe(df_bid[cols_to_show].head(20), use_container_width=True)
else:
    st.info("No bids found.")

# ── Trigger signals ───────────────────────────────────────────────────────────

st.subheader("📡 Recent Trigger Signals")

if signals:
    df_sig = pd.DataFrame(signals)
    cols_to_show = [c for c in ["signal_type", "status", "description", "created_at"] if c in df_sig.columns]
    if cols_to_show:
        st.dataframe(df_sig[cols_to_show].head(20), use_container_width=True)
else:
    st.info("No trigger signals found.")

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption("aLiGN Analytics • powered by Streamlit • data from the aLiGN FastAPI backend")
