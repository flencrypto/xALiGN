"""
Pytest test suite for the eight features listed in the project roadmap:

  1. Document parsing (PDF/Word → structured requirements via pdfplumber + python-docx)
  2. LLM-assisted compliance answer generation
  3. Lead-time intelligence database (switchgear, UPS, chillers, generators)
  4. Bid debrief capture + learning loop
  5. Framework & procurement tracker
  6. Export: Pursuit Pack PDF, Tender Response Pack (Word), Compliance Matrix (Excel)
  7. PostgreSQL + S3 production config
  8. SSO / Auth (Clerk or Auth0)

All tests run against an in-memory SQLite database so no external services are needed.
"""

import io
import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker

# ── path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set env vars before importing backend modules that read them at import time.
# DATABASE_URL=sqlite:// ensures the lifespan's create_all/run_seed uses an
# in-memory database instead of creating an align.db file on disk.
# ENABLE_SCHEDULER=false prevents the APScheduler from starting during tests.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

from backend.database import Base, get_db  # noqa: E402
from backend.main import app  # noqa: E402

# ── in-memory test database (shared across the module) ────────────────────────
TEST_DATABASE_URL = "sqlite://"

_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable FK enforcement for SQLite
@event.listens_for(_engine, "connect")
def _set_sqlite_fk(dbapi_conn, _conn_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables once before any tests run.
Base.metadata.create_all(bind=_engine)


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Module-scoped TestClient that:
    - Overrides the DB dependency to use the in-memory test engine.
    - Runs FastAPI lifespan startup/shutdown inside a context manager so all
      resources (including any shutdown handlers) are properly released.
    - Clears the dependency override after all tests in the module finish.
    """
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


# ── helper to create an account → opportunity → bid for tests that need one ───

def _create_bid(c: TestClient) -> tuple[int, int]:
    """Create a minimal account, opportunity and bid. Returns (opp_id, bid_id)."""
    # Create account
    acct = c.post("/api/v1/accounts", json={
        "name": "Test Account",
        "type": "operator",
    })
    acct.raise_for_status()
    acct_id = acct.json()["id"]

    # Create opportunity
    opp = c.post("/api/v1/opportunities", json={
        "account_id": acct_id,
        "title": "Test Opportunity",
        "stage": "target",
    })
    opp.raise_for_status()
    opp_id = opp.json()["id"]

    # Create bid
    bid = c.post("/api/v1/bids", json={
        "opportunity_id": opp_id,
        "title": "Test Bid",
        "status": "draft",
    })
    bid.raise_for_status()
    return opp_id, bid.json()["id"]


# ══════════════════════════════════════════════════════════════════════════════
# 1. Document parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestDocumentParsing:
    """Feature 1 – Document parsing (PDF/Word → structured requirements)."""

    def test_parse_pdf_returns_requirements(self):
        """parse_pdf extracts requirement-like sentences from raw text."""
        from backend.services.document_parser import extract_requirements

        text = (
            "The contractor shall install all equipment to BS EN standards. "
            "All materials must comply with the project specification. "
            "The supplier should provide a 12-month warranty."
        )
        reqs = extract_requirements(text)
        assert len(reqs) >= 2
        categories = {r["category"] for r in reqs}
        assert "mandatory" in categories

    def test_parse_pdf_empty_bytes_returns_empty(self):
        """parse_pdf with empty bytes returns empty text and requirements."""
        from backend.services.document_parser import parse_pdf

        text, reqs = parse_pdf(b"")
        assert text == ""
        assert reqs == []

    def test_parse_docx_empty_bytes_returns_empty(self):
        """parse_docx with empty bytes returns empty text and requirements."""
        from backend.services.document_parser import parse_docx

        text, reqs = parse_docx(b"")
        assert text == ""
        assert reqs == []

    def test_parse_document_dispatcher_pdf(self):
        """parse_document routes .pdf extension to the PDF parser."""
        from backend.services.document_parser import parse_document

        content, reqs_json = parse_document(b"", "spec.pdf")
        assert isinstance(content, str)
        parsed = json.loads(reqs_json)
        assert isinstance(parsed, list)

    def test_parse_document_dispatcher_docx(self):
        """parse_document routes .docx extension to the Word parser."""
        from backend.services.document_parser import parse_document

        content, reqs_json = parse_document(b"", "spec.docx")
        assert isinstance(content, str)
        parsed = json.loads(reqs_json)
        assert isinstance(parsed, list)

    def test_parse_document_dispatcher_unknown(self):
        """parse_document returns empty for unknown extension."""
        from backend.services.document_parser import parse_document

        content, reqs_json = parse_document(b"data", "file.xyz")
        assert content == ""
        assert json.loads(reqs_json) == []

    def test_extract_requirements_deduplication(self):
        """Duplicate sentences are not returned twice."""
        from backend.services.document_parser import extract_requirements

        text = "The system must be fault-tolerant. The system must be fault-tolerant."
        reqs = extract_requirements(text)
        assert len(reqs) == 1

    def test_compliance_categories(self):
        """Sentences with 'shall/must/should/may' get the right category.

        Note: 'shall not' matches the 'mandatory' pattern (via 'shall') because
        the mandatory pattern is checked first. The exclusion pattern only fires
        for 'will not' or 'must not' when 'must' isn't matched first – these edge
        cases are tested here with the actual classifier behaviour.
        """
        from backend.services.document_parser import extract_requirements

        cases = {
            "mandatory": "The contractor shall submit all documentation on time.",
            "preferred": "The supplier should provide on-site training for staff.",
            "optional": "The installer may use alternative fixing methods if approved.",
        }
        for expected_cat, sentence in cases.items():
            reqs = extract_requirements(sentence)
            assert any(r["category"] == expected_cat for r in reqs), (
                f"Expected category {expected_cat!r} for: {sentence}"
            )

    def test_upload_and_parse_endpoint(self, client: TestClient):
        """POST /bids/{id}/documents/upload-and-parse returns 415 for unsupported type."""
        _, bid_id = _create_bid(client)

        # Plain-text pseudo-document (not a supported parse type)
        data = io.BytesIO(b"The contractor shall comply with all specifications.")
        resp = client.post(
            f"/api/v1/bids/{bid_id}/documents/upload-and-parse",
            files={"file": ("spec.txt", data, "text/plain")},
            data={"doc_type": "tender"},
        )
        # .txt is not a supported parse type; endpoint returns 415
        assert resp.status_code == 415


# ══════════════════════════════════════════════════════════════════════════════
# 2. LLM-assisted compliance answer generation (route level)
# ══════════════════════════════════════════════════════════════════════════════

class TestComplianceAnswerGeneration:
    """Feature 2 – LLM-assisted compliance answer generation."""

    def test_generate_compliance_matrix_endpoint_exists(self, client: TestClient):
        """POST /bids/{id}/generate-compliance-matrix returns 200 with an empty list when no documents exist."""
        _, bid_id = _create_bid(client)
        resp = client.post(f"/api/v1/bids/{bid_id}/generate-compliance-matrix")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_generate_compliance_answer_endpoint_exists(self, client: TestClient):
        """POST /bids/{id}/compliance/{item_id}/generate-answer returns 404 for missing item."""
        _, bid_id = _create_bid(client)
        resp = client.post(
            f"/api/v1/bids/{bid_id}/compliance/9999/generate-answer",
            json={},
        )
        assert resp.status_code == 404

    def test_create_and_list_compliance_items(self, client: TestClient):
        """Compliance items can be created and listed for a bid."""
        _, bid_id = _create_bid(client)

        # Create a compliance item
        resp = client.post(f"/api/v1/bids/{bid_id}/compliance", json={
            "bid_id": bid_id,
            "requirement": "The system shall achieve 99.999% uptime.",
            "category": "technical",
            "compliance_status": "tbc",
        })
        assert resp.status_code == 201
        item_id = resp.json()["id"]

        # List compliance items
        resp = client.get(f"/api/v1/bids/{bid_id}/compliance")
        assert resp.status_code == 200
        items = resp.json()
        assert any(i["id"] == item_id for i in items)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Lead-time intelligence database
# ══════════════════════════════════════════════════════════════════════════════

class TestLeadTimeDatabase:
    """Feature 3 – Lead-time intelligence database."""

    def test_list_lead_times_empty(self, client: TestClient):
        """GET /lead-times returns a list (possibly empty)."""
        resp = client.get("/api/v1/lead-times")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_lead_time_item(self, client: TestClient):
        """POST /lead-times creates a new entry."""
        resp = client.post("/api/v1/lead-times", json={
            "category": "switchgear",
            "manufacturer": "Schneider Electric",
            "model_ref": "SM6 Test",
            "description": "Test MV switchgear entry",
            "lead_weeks_min": 16,
            "lead_weeks_max": 28,
            "lead_weeks_typical": 22.0,
            "region": "UK",
            "source": "Test data",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "switchgear"
        assert data["lead_weeks_min"] == 16

    def test_get_lead_time_item(self, client: TestClient):
        """GET /lead-times/{id} returns the item."""
        create_resp = client.post("/api/v1/lead-times", json={
            "category": "ups",
            "description": "Test UPS entry for get test",
            "lead_weeks_min": 10,
            "lead_weeks_max": 20,
        })
        assert create_resp.status_code == 201
        item_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/lead-times/{item_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == item_id

    def test_update_lead_time_item(self, client: TestClient):
        """PATCH /lead-times/{id} updates the entry."""
        create_resp = client.post("/api/v1/lead-times", json={
            "category": "chiller",
            "description": "Test chiller entry for patch test",
            "lead_weeks_min": 12,
            "lead_weeks_max": 24,
        })
        item_id = create_resp.json()["id"]

        resp = client.patch(f"/api/v1/lead-times/{item_id}", json={
            "lead_weeks_min": 14,
            "notes": "Updated notes",
        })
        assert resp.status_code == 200
        assert resp.json()["lead_weeks_min"] == 14

    def test_delete_lead_time_item(self, client: TestClient):
        """DELETE /lead-times/{id} removes the entry."""
        create_resp = client.post("/api/v1/lead-times", json={
            "category": "generator",
            "description": "Test generator entry for delete test",
            "lead_weeks_min": 20,
            "lead_weeks_max": 40,
        })
        item_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/v1/lead-times/{item_id}")
        assert del_resp.status_code == 204

        get_resp = client.get(f"/api/v1/lead-times/{item_id}")
        assert get_resp.status_code == 404

    def test_seed_endpoint(self, client: TestClient):
        """POST /lead-times/seed populates the database with default equipment."""
        resp = client.post("/api/v1/lead-times/seed")
        assert resp.status_code == 201
        seeded = resp.json()
        assert len(seeded) > 0
        categories = {item["category"] for item in seeded}
        # Should include at least switchgear, ups, chiller, generator
        assert "switchgear" in categories
        assert "ups" in categories
        assert "chiller" in categories
        assert "generator" in categories

    def test_filter_by_category(self, client: TestClient):
        """GET /lead-times?category=ups returns only UPS items."""
        client.post("/api/v1/lead-times", json={
            "category": "ups",
            "description": "Filter test UPS",
            "lead_weeks_min": 8,
            "lead_weeks_max": 16,
        })
        resp = client.get("/api/v1/lead-times?category=ups")
        assert resp.status_code == 200
        items = resp.json()
        assert all(i["category"] == "ups" for i in items)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Bid debrief capture + learning loop
# ══════════════════════════════════════════════════════════════════════════════

class TestBidDebrief:
    """Feature 4 – Bid debrief capture + learning loop."""

    def test_create_debrief(self, client: TestClient):
        """POST /bids/{id}/debrief creates a debrief record."""
        _, bid_id = _create_bid(client)
        resp = client.post(f"/api/v1/bids/{bid_id}/debrief", json={
            "bid_id": bid_id,
            "outcome": "won",
            "our_score": 85.5,
            "winner_score": 85.5,
            "our_price": 500000.0,
            "strengths": "Strong technical proposal, local knowledge",
            "weaknesses": "Price slightly above market",
            "lessons_learned": "Early engagement with client paid off",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["outcome"] == "won"
        assert data["bid_id"] == bid_id

    def test_get_debrief(self, client: TestClient):
        """GET /bids/{id}/debrief returns the debrief."""
        _, bid_id = _create_bid(client)
        client.post(f"/api/v1/bids/{bid_id}/debrief", json={
            "bid_id": bid_id,
            "outcome": "lost",
        })
        resp = client.get(f"/api/v1/bids/{bid_id}/debrief")
        assert resp.status_code == 200
        assert resp.json()["outcome"] == "lost"

    def test_update_debrief(self, client: TestClient):
        """PATCH /bids/{id}/debrief updates the debrief."""
        _, bid_id = _create_bid(client)
        client.post(f"/api/v1/bids/{bid_id}/debrief", json={
            "bid_id": bid_id,
            "outcome": "lost",
        })
        resp = client.patch(f"/api/v1/bids/{bid_id}/debrief", json={
            "outcome": "won",
            "our_score": 90.0,
        })
        assert resp.status_code == 200
        assert resp.json()["outcome"] == "won"

    def test_delete_debrief(self, client: TestClient):
        """DELETE /bids/{id}/debrief removes the record."""
        _, bid_id = _create_bid(client)
        client.post(f"/api/v1/bids/{bid_id}/debrief", json={
            "bid_id": bid_id,
            "outcome": "withdrawn",
        })
        del_resp = client.delete(f"/api/v1/bids/{bid_id}/debrief")
        assert del_resp.status_code == 204
        assert client.get(f"/api/v1/bids/{bid_id}/debrief").status_code == 404

    def test_duplicate_debrief_returns_409(self, client: TestClient):
        """Creating a second debrief for the same bid returns 409."""
        _, bid_id = _create_bid(client)
        client.post(f"/api/v1/bids/{bid_id}/debrief", json={
            "bid_id": bid_id,
            "outcome": "won",
        })
        resp = client.post(f"/api/v1/bids/{bid_id}/debrief", json={
            "bid_id": bid_id,
            "outcome": "lost",
        })
        assert resp.status_code == 409

    def test_list_debriefs(self, client: TestClient):
        """GET /debriefs returns all debrief records."""
        _, bid_id = _create_bid(client)
        client.post(f"/api/v1/bids/{bid_id}/debrief", json={
            "bid_id": bid_id,
            "outcome": "won",
        })
        resp = client.get("/api/v1/debriefs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_learning_loop_insights(self, client: TestClient):
        """GET /debriefs/insights returns aggregated learning data."""
        resp = client.get("/api/v1/debriefs/insights")
        assert resp.status_code == 200
        data = resp.json()
        assert "win_rate_pct" in data
        assert "total_bids_debriefed" in data
        assert "top_strengths" in data
        assert "top_weaknesses" in data
        assert "common_winners" in data


# ══════════════════════════════════════════════════════════════════════════════
# 5. Framework & procurement tracker
# ══════════════════════════════════════════════════════════════════════════════

class TestFrameworkTracker:
    """Feature 5 – Framework & procurement tracker."""

    def test_list_frameworks_empty(self, client: TestClient):
        """GET /frameworks returns a list."""
        resp = client.get("/api/v1/frameworks")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_framework(self, client: TestClient):
        """POST /frameworks creates a new framework entry."""
        resp = client.post("/api/v1/frameworks", json={
            "name": "Crown Commercial Service Data Centre Framework",
            "authority": "Crown Commercial Service",
            "reference": "RM6259",
            "status": "active",
            "region": "UK",
            "we_are_listed": True,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Crown Commercial Service Data Centre Framework"
        assert data["we_are_listed"] is True

    def test_get_framework(self, client: TestClient):
        """GET /frameworks/{id} returns the entry."""
        create_resp = client.post("/api/v1/frameworks", json={
            "name": "Test Framework for Get",
            "authority": "Test Authority",
            "status": "active",
        })
        fw_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/frameworks/{fw_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == fw_id

    def test_update_framework(self, client: TestClient):
        """PATCH /frameworks/{id} updates the entry."""
        create_resp = client.post("/api/v1/frameworks", json={
            "name": "Test Framework for Update",
            "authority": "Test Authority",
            "status": "active",
        })
        fw_id = create_resp.json()["id"]

        resp = client.patch(f"/api/v1/frameworks/{fw_id}", json={
            "status": "expiring_soon",
            "notes": "Expires Q1 2025",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "expiring_soon"

    def test_delete_framework(self, client: TestClient):
        """DELETE /frameworks/{id} removes the entry."""
        create_resp = client.post("/api/v1/frameworks", json={
            "name": "Test Framework for Delete",
            "authority": "Test Authority",
            "status": "active",
        })
        fw_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/v1/frameworks/{fw_id}")
        assert del_resp.status_code == 204

        get_resp = client.get(f"/api/v1/frameworks/{fw_id}")
        assert get_resp.status_code == 404

    def test_filter_by_status(self, client: TestClient):
        """GET /frameworks?status=active returns only active frameworks."""
        client.post("/api/v1/frameworks", json={
            "name": "Active Framework Filter Test",
            "authority": "Test Authority",
            "status": "active",
        })
        resp = client.get("/api/v1/frameworks?status=active")
        assert resp.status_code == 200
        items = resp.json()
        assert all(i["status"] == "active" for i in items)

    def test_filter_by_we_are_listed(self, client: TestClient):
        """GET /frameworks?we_are_listed=true returns only frameworks where listed."""
        client.post("/api/v1/frameworks", json={
            "name": "Listed Framework Filter Test",
            "authority": "Test Authority",
            "status": "active",
            "we_are_listed": True,
        })
        resp = client.get("/api/v1/frameworks?we_are_listed=true")
        assert resp.status_code == 200
        items = resp.json()
        assert all(i["we_are_listed"] is True for i in items)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Export: Pursuit Pack PDF, Tender Response Word, Compliance Matrix Excel
# ══════════════════════════════════════════════════════════════════════════════

class TestExports:
    """Feature 6 – Export service (PDF, Word, Excel)."""

    def test_build_pursuit_pack_pdf_returns_bytes(self):
        """build_pursuit_pack_pdf returns non-empty PDF bytes."""
        from backend.services.export_service import build_pursuit_pack_pdf

        class FakeOpp:
            title = "Test Opportunity"
            name = "Test Opportunity"  # export_service uses getattr(opp, "name", ...)

        class FakeBid:
            title = "Test Bid"
            tender_ref = "TDR-001"
            status = "draft"
            win_themes = "Best value, proven track record"

        pdf = build_pursuit_pack_pdf(FakeOpp(), FakeBid(), [])
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0
        # PDF files start with %PDF
        assert pdf[:4] == b"%PDF"

    def test_build_tender_response_docx_returns_bytes(self):
        """build_tender_response_pack_docx returns non-empty .docx bytes."""
        from backend.services.export_service import build_tender_response_pack_docx

        class FakeBid:
            title = "Test Bid"
            tender_ref = "TDR-001"

        docx = build_tender_response_pack_docx(FakeBid(), [], [])
        assert isinstance(docx, bytes)
        assert len(docx) > 0
        # DOCX files are ZIP archives starting with PK
        assert docx[:2] == b"PK"

    def test_build_compliance_matrix_xlsx_returns_bytes(self):
        """build_compliance_matrix_xlsx returns non-empty .xlsx bytes."""
        from backend.services.export_service import build_compliance_matrix_xlsx

        class FakeBid:
            title = "Test Bid"
            tender_ref = "TDR-001"

        xlsx = build_compliance_matrix_xlsx(FakeBid(), [])
        assert isinstance(xlsx, bytes)
        assert len(xlsx) > 0
        # XLSX files are ZIP archives
        assert xlsx[:2] == b"PK"

    def test_pursuit_pack_endpoint_404_for_missing_bid(self, client: TestClient):
        """GET /bids/9999/export/pursuit-pack-pdf returns 404 for missing bid."""
        resp = client.get("/api/v1/bids/9999/export/pursuit-pack-pdf")
        assert resp.status_code == 404

    def test_tender_response_endpoint_404_for_missing_bid(self, client: TestClient):
        """GET /bids/9999/export/tender-response-docx returns 404 for missing bid."""
        resp = client.get("/api/v1/bids/9999/export/tender-response-docx")
        assert resp.status_code == 404

    def test_compliance_matrix_endpoint_404_for_missing_bid(self, client: TestClient):
        """GET /bids/9999/export/compliance-matrix-xlsx returns 404 for missing bid."""
        resp = client.get("/api/v1/bids/9999/export/compliance-matrix-xlsx")
        assert resp.status_code == 404

    def test_pursuit_pack_endpoint_returns_pdf(self, client: TestClient):
        """GET /bids/{id}/export/pursuit-pack-pdf returns a PDF file."""
        _, bid_id = _create_bid(client)
        resp = client.get(f"/api/v1/bids/{bid_id}/export/pursuit-pack-pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_tender_response_endpoint_returns_docx(self, client: TestClient):
        """GET /bids/{id}/export/tender-response-docx returns a Word document."""
        _, bid_id = _create_bid(client)
        resp = client.get(f"/api/v1/bids/{bid_id}/export/tender-response-docx")
        assert resp.status_code == 200
        ct = resp.headers["content-type"]
        assert "officedocument.wordprocessingml" in ct
        assert resp.content[:2] == b"PK"

    def test_compliance_matrix_endpoint_returns_xlsx(self, client: TestClient):
        """GET /bids/{id}/export/compliance-matrix-xlsx returns an Excel file."""
        _, bid_id = _create_bid(client)
        resp = client.get(f"/api/v1/bids/{bid_id}/export/compliance-matrix-xlsx")
        assert resp.status_code == 200
        ct = resp.headers["content-type"]
        assert "spreadsheetml" in ct
        assert resp.content[:2] == b"PK"


# ══════════════════════════════════════════════════════════════════════════════
# 7. PostgreSQL + S3 production config
# ══════════════════════════════════════════════════════════════════════════════

class TestProductionConfig:
    """Feature 7 – PostgreSQL + S3 production config."""

    def test_database_url_defaults_to_sqlite(self):
        """Default DATABASE_URL uses SQLite for local development."""
        from backend.core.config import Settings
        s = Settings()
        assert s.DATABASE_URL.startswith("sqlite")

    def test_database_url_accepts_postgres(self):
        """DATABASE_URL can be set to a PostgreSQL connection string."""
        from backend.core.config import Settings
        original = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/align"
        try:
            s = Settings()
            assert s.DATABASE_URL.startswith("postgresql")
        finally:
            if original is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = original

    def test_storage_backend_defaults_to_local(self):
        """Default STORAGE_BACKEND is 'local'."""
        from backend.core.config import Settings
        s = Settings()
        assert s.STORAGE_BACKEND == "local"

    def test_storage_backend_accepts_s3(self):
        """STORAGE_BACKEND can be set to 's3'."""
        from backend.core.config import Settings
        original = os.environ.get("STORAGE_BACKEND")
        os.environ["STORAGE_BACKEND"] = "s3"
        try:
            s = Settings()
            assert s.STORAGE_BACKEND == "s3"
        finally:
            if original is None:
                os.environ.pop("STORAGE_BACKEND", None)
            else:
                os.environ["STORAGE_BACKEND"] = original

    def test_s3_bucket_config_fields_present(self):
        """S3 config fields exist in Settings."""
        from backend.core.config import Settings
        s = Settings()
        assert hasattr(s, "S3_BUCKET")
        assert hasattr(s, "S3_REGION")
        assert hasattr(s, "AWS_ACCESS_KEY_ID")
        assert hasattr(s, "AWS_SECRET_ACCESS_KEY")

    def test_local_storage_save_and_load(self, tmp_path):
        """Local storage saves and loads bytes correctly."""
        import importlib
        original_upload_dir = os.environ.get("UPLOAD_DIR")
        original_storage_backend = os.environ.get("STORAGE_BACKEND")
        os.environ["UPLOAD_DIR"] = str(tmp_path)
        os.environ["STORAGE_BACKEND"] = "local"
        try:
            import backend.services.storage as storage_mod
            importlib.reload(storage_mod)
            data = b"hello storage"
            storage_mod._local_save(data, "test/file.bin")
            loaded = storage_mod._local_load("test/file.bin")
            assert loaded == data
        finally:
            if original_upload_dir is None:
                os.environ.pop("UPLOAD_DIR", None)
            else:
                os.environ["UPLOAD_DIR"] = original_upload_dir
            if original_storage_backend is None:
                os.environ.pop("STORAGE_BACKEND", None)
            else:
                os.environ["STORAGE_BACKEND"] = original_storage_backend
            importlib.reload(storage_mod)

    def test_local_storage_path_traversal_blocked(self, tmp_path):
        """Local storage rejects path-traversal keys."""
        import importlib
        original_upload_dir = os.environ.get("UPLOAD_DIR")
        original_storage_backend = os.environ.get("STORAGE_BACKEND")
        os.environ["UPLOAD_DIR"] = str(tmp_path)
        os.environ["STORAGE_BACKEND"] = "local"
        try:
            import backend.services.storage as storage_mod
            importlib.reload(storage_mod)
            with pytest.raises(ValueError, match="escapes the upload directory"):
                storage_mod._local_resolve("../../etc/passwd")
        finally:
            if original_upload_dir is None:
                os.environ.pop("UPLOAD_DIR", None)
            else:
                os.environ["UPLOAD_DIR"] = original_upload_dir
            if original_storage_backend is None:
                os.environ.pop("STORAGE_BACKEND", None)
            else:
                os.environ["STORAGE_BACKEND"] = original_storage_backend
            importlib.reload(storage_mod)


# ══════════════════════════════════════════════════════════════════════════════
# 8. SSO / Auth (Clerk or Auth0)
# ══════════════════════════════════════════════════════════════════════════════

class TestAuth:
    """Feature 8 – SSO / Auth (Clerk or Auth0)."""

    def test_auth_provider_defaults_to_none(self):
        """AUTH_PROVIDER defaults to 'none' – open access for local dev."""
        from backend.core.config import Settings
        s = Settings()
        assert s.AUTH_PROVIDER == "none"

    def test_auth_provider_none_allows_all_requests(self):
        """When AUTH_PROVIDER=none, get_current_user returns None (no auth check)."""
        import importlib
        original = os.environ.get("AUTH_PROVIDER")
        os.environ["AUTH_PROVIDER"] = "none"
        try:
            import backend.services.auth as auth_mod
            importlib.reload(auth_mod)
            result = auth_mod.get_current_user(credentials=None)
            assert result is None
        finally:
            if original is None:
                os.environ.pop("AUTH_PROVIDER", None)
            else:
                os.environ["AUTH_PROVIDER"] = original
            importlib.reload(auth_mod)

    def test_auth_provider_clerk_config_fields_present(self):
        """Clerk auth config fields exist in Settings."""
        from backend.core.config import Settings
        s = Settings()
        assert hasattr(s, "CLERK_ISSUER")
        assert hasattr(s, "CLERK_JWKS_URL")

    def test_auth_provider_auth0_config_fields_present(self):
        """Auth0 auth config fields exist in Settings."""
        from backend.core.config import Settings
        s = Settings()
        assert hasattr(s, "AUTH0_DOMAIN")
        assert hasattr(s, "AUTH0_AUDIENCE")

    def test_user_claims_populates_fields(self):
        """UserClaims correctly extracts sub, email, roles from a JWT payload."""
        from backend.services.auth import UserClaims

        claims = {
            "sub": "user_12345",
            "email": "test@example.com",
            "roles": ["admin", "bid_manager"],
        }
        uc = UserClaims(claims)
        assert uc.sub == "user_12345"
        assert uc.email == "test@example.com"
        assert uc.has_role("admin")
        assert not uc.has_role("unknown_role")

    def test_user_claims_handles_missing_fields(self):
        """UserClaims handles missing fields gracefully."""
        from backend.services.auth import UserClaims

        uc = UserClaims({})
        assert uc.sub == ""
        assert uc.email == ""
        assert uc.roles == []

    def test_clerk_provider_requires_credentials(self):
        """When AUTH_PROVIDER=clerk and no token provided, returns 401."""
        import importlib
        original_provider = os.environ.get("AUTH_PROVIDER")
        original_clerk_issuer = os.environ.get("CLERK_ISSUER")
        os.environ["AUTH_PROVIDER"] = "clerk"
        os.environ.setdefault("CLERK_ISSUER", "https://test.clerk.accounts.dev")
        try:
            import backend.services.auth as auth_mod
            importlib.reload(auth_mod)
            with pytest.raises(Exception) as exc_info:
                auth_mod.get_current_user(credentials=None)
            assert exc_info.value.status_code == 401
        finally:
            if original_provider is None:
                os.environ.pop("AUTH_PROVIDER", None)
            else:
                os.environ["AUTH_PROVIDER"] = original_provider
            if original_clerk_issuer is None:
                os.environ.pop("CLERK_ISSUER", None)
            else:
                os.environ["CLERK_ISSUER"] = original_clerk_issuer
            importlib.reload(auth_mod)

    def test_auth0_provider_requires_credentials(self):
        """When AUTH_PROVIDER=auth0 and no token provided, returns 401."""
        import importlib
        original_provider = os.environ.get("AUTH_PROVIDER")
        original_auth0_domain = os.environ.get("AUTH0_DOMAIN")
        original_auth0_audience = os.environ.get("AUTH0_AUDIENCE")
        os.environ["AUTH_PROVIDER"] = "auth0"
        os.environ.setdefault("AUTH0_DOMAIN", "test.auth0.com")
        os.environ.setdefault("AUTH0_AUDIENCE", "https://api.test.com")
        try:
            import backend.services.auth as auth_mod
            importlib.reload(auth_mod)
            with pytest.raises(Exception) as exc_info:
                auth_mod.get_current_user(credentials=None)
            assert exc_info.value.status_code == 401
        finally:
            if original_provider is None:
                os.environ.pop("AUTH_PROVIDER", None)
            else:
                os.environ["AUTH_PROVIDER"] = original_provider
            if original_auth0_domain is None:
                os.environ.pop("AUTH0_DOMAIN", None)
            else:
                os.environ["AUTH0_DOMAIN"] = original_auth0_domain
            if original_auth0_audience is None:
                os.environ.pop("AUTH0_AUDIENCE", None)
            else:
                os.environ["AUTH0_AUDIENCE"] = original_auth0_audience
            importlib.reload(auth_mod)

    def test_unknown_auth_provider_raises_500(self):
        """An unknown AUTH_PROVIDER raises a 500 error."""
        import importlib
        from fastapi.security import HTTPAuthorizationCredentials

        original = os.environ.get("AUTH_PROVIDER")
        os.environ["AUTH_PROVIDER"] = "unknown_provider"
        try:
            import backend.services.auth as auth_mod
            importlib.reload(auth_mod)
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake.token.here")
            with pytest.raises(Exception) as exc_info:
                auth_mod.get_current_user(credentials=creds)
            assert exc_info.value.status_code == 500
        finally:
            if original is None:
                os.environ.pop("AUTH_PROVIDER", None)
            else:
                os.environ["AUTH_PROVIDER"] = original
            importlib.reload(auth_mod)
