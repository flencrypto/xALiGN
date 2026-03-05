"""Grok (xAI) API client for structured intelligence research.

Uses the OpenAI-compatible API endpoint at https://api.x.ai/v1.
Falls back gracefully when XAI_API_KEY is not configured.

Every public function routes through a task-based temperature / model table and
records a per-invocation governance entry (audit log, confidence score,
hallucination detection, citation verification, human-review flag).
"""

import json
import logging
import os
import re
from typing import Any

import httpx

from backend.services.governance import (
    GovernanceLogger,
    check_numeric_anomalies,
    needs_human_review,
    validate_citations,
)

logger = logging.getLogger("align.grok")

_BASE_URL = "https://api.x.ai/v1"
_TIMEOUT = 60.0

# ── Task-based model routing ──────────────────────────────────────────────────
# Each task key maps to the model best suited for that workload.
# Override any value via the corresponding env var (e.g. GROK_MODEL_BLOG_WRITING).

_DEFAULT_MODEL = os.getenv("GROK_DEFAULT_MODEL", "grok-3-mini")

_TASK_MODELS: dict[str, str] = {
    "company_research":      os.getenv("GROK_MODEL_COMPANY_RESEARCH",      _DEFAULT_MODEL),
    "company_swoop":         os.getenv("GROK_MODEL_COMPANY_SWOOP",         _DEFAULT_MODEL),
    "social_media_research": os.getenv("GROK_MODEL_SOCIAL_MEDIA_RESEARCH", _DEFAULT_MODEL),
    "executive_research":    os.getenv("GROK_MODEL_EXECUTIVE_RESEARCH",     _DEFAULT_MODEL),
    "news_signals":          os.getenv("GROK_MODEL_NEWS_SIGNALS",           _DEFAULT_MODEL),
    "compliance_answer":     os.getenv("GROK_MODEL_COMPLIANCE_ANSWER",      _DEFAULT_MODEL),
    "document_parsing":      os.getenv("GROK_MODEL_DOCUMENT_PARSING",       _DEFAULT_MODEL),
    "blog_writing":          os.getenv("GROK_MODEL_BLOG_WRITING",           _DEFAULT_MODEL),
    "relationship_brief":    os.getenv("GROK_MODEL_RELATIONSHIP_BRIEF",     _DEFAULT_MODEL),
    "transcript_analysis":   os.getenv("GROK_MODEL_TRANSCRIPT_ANALYSIS",    _DEFAULT_MODEL),
}

# ── Task-based temperature routing ────────────────────────────────────────────
# Lower temperatures for factual extraction; higher for creative / advisory tasks.
# Each value is overridable via env var (e.g. GROK_TEMP_BLOG_WRITING).

_TASK_TEMPERATURES: dict[str, float] = {
    "company_research":      float(os.getenv("GROK_TEMP_COMPANY_RESEARCH",      "0.1")),
    "company_swoop":         float(os.getenv("GROK_TEMP_COMPANY_SWOOP",         "0.1")),
    "social_media_research": float(os.getenv("GROK_TEMP_SOCIAL_MEDIA_RESEARCH", "0.15")),
    "executive_research":    float(os.getenv("GROK_TEMP_EXECUTIVE_RESEARCH",     "0.15")),
    "news_signals":          float(os.getenv("GROK_TEMP_NEWS_SIGNALS",           "0.1")),
    "compliance_answer":     float(os.getenv("GROK_TEMP_COMPLIANCE_ANSWER",      "0.2")),
    "document_parsing":      float(os.getenv("GROK_TEMP_DOCUMENT_PARSING",       "0.05")),
    "blog_writing":          float(os.getenv("GROK_TEMP_BLOG_WRITING",           "0.7")),
    "relationship_brief":    float(os.getenv("GROK_TEMP_RELATIONSHIP_BRIEF",     "0.2")),
    "transcript_analysis":   float(os.getenv("GROK_TEMP_TRANSCRIPT_ANALYSIS",    "0.1")),
}

# Keep a simple alias for legacy callers that just need the default model name.
_MODEL = _DEFAULT_MODEL


def _api_key() -> str | None:
    return os.getenv("XAI_API_KEY")


def is_configured() -> bool:
    return bool(_api_key())


async def _chat(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 2048,
    *,
    temperature: float,
    task: str = "unknown",
) -> tuple[str, int, int]:
    """Send a chat request to the Grok API and return *(reply, input_tokens, output_tokens)*.

    ``temperature`` is a required keyword argument; callers must supply the
    task-appropriate value from ``_TASK_TEMPERATURES``.  The model is resolved
    from ``_TASK_MODELS`` using *task* (defaults to ``_DEFAULT_MODEL``).
    """
    key = _api_key()
    if not key:
        raise RuntimeError("XAI_API_KEY is not set. Configure it to enable Grok AI features.")

    model = _TASK_MODELS.get(task, _DEFAULT_MODEL)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    usage = data.get("usage", {})
    input_tokens: int = usage.get("prompt_tokens", 0)
    output_tokens: int = usage.get("completion_tokens", 0)
    content: str = data["choices"][0]["message"]["content"]
    return content, input_tokens, output_tokens


def _governance_log(
    task: str,
    temperature: float,
    system_prompt: str,
    input_tokens: int,
    output_tokens: int,
    result: dict[str, Any] | list[Any],
    source_text: str = "",
    claimed_values: list[str] | None = None,
) -> None:
    """Run hallucination detection, confidence scoring, citation verification and audit logging."""
    flags: list[str] = []
    confidence = 0.65  # neutral default

    if isinstance(result, dict):
        flags = check_numeric_anomalies(result)
        for key in ("confidence", "overall_confidence", "confidence_level"):
            val = result.get(key)
            if val is not None:
                try:
                    confidence = float(val)
                    break
                except (TypeError, ValueError):
                    continue

    # Citation verification: check whether key claimed values are grounded in source text
    citation_results: dict[str, bool] = {}
    if source_text and claimed_values:
        citation_results = validate_citations(claimed_values, source_text)
        unverified = [v for v, found in citation_results.items() if not found]
        if unverified:
            flags.append(f"unverified_citations: {unverified}")

    # Multi-layer hallucination detection: low confidence + unverified citations
    hr = needs_human_review(confidence, flags)
    if isinstance(result, dict):
        result.setdefault("needs_human_review", hr)
        if flags:
            result.setdefault("anomaly_flags", flags)

    GovernanceLogger.log(
        worker_name=f"grok_client.{task}",
        model=_TASK_MODELS.get(task, _DEFAULT_MODEL),
        temperature=temperature,
        system_prompt=system_prompt,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        confidence=confidence,
        validation_outcome="anomaly_detected" if flags else "ok",
        extra={
            "citation_verification": citation_results,
            "human_review_queued": hr,
        } if citation_results else {"human_review_queued": hr},
    )


async def research_company(website: str, crawl_text: str) -> dict[str, Any]:
    """
    Use Grok to extract structured intelligence signals from crawled company content.

    Returns a dict matching the CompanyIntel schema fields.
    """
    _TASK = "company_research"
    _TEMP = _TASK_TEMPERATURES[_TASK]
    system_prompt = (
        "You are an institutional infrastructure intelligence analyst. "
        "Extract structured signals from the provided company web content. "
        "Only use publicly available data. "
        "Return strictly valid JSON with the following keys: "
        "company_name, business_model, locations, expansion_signals, "
        "technology_indicators, financial_summary, earnings_highlights, "
        "competitor_mentions, strategic_risks, bid_opportunities, "
        "stock_ticker, stock_price. "
        "stock_ticker: the stock exchange ticker symbol if publicly listed (e.g. 'NASDAQ:MSFT'), or null. "
        "stock_price: latest known public stock price and date if available (e.g. '$415.23 as of Jan 2025'), or null. "
        "Each other value should be a short descriptive string or a JSON array of strings. "
        "Do not include any markdown, code fences, or extra text outside the JSON object."
    )
    user_content = (
        f"Company website: {website}\n\n"
        f"Crawled content:\n{crawl_text[:6000]}"
    )

    raw = ""
    result: dict[str, Any] = {}
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, max_tokens=1800, temperature=_TEMP, task=_TASK
        )
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON response for company research; storing raw text")
        result = {"raw_response": raw}
    except Exception as exc:
        logger.error("Grok company research failed: %s", exc)
        raise
    finally:
        _governance_log(
            task=_TASK,
            temperature=_TEMP,
            system_prompt=system_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            result=result,
            source_text=crawl_text,
            claimed_values=[v for v in [str(result.get("company_name", "")), str(result.get("business_model", ""))] if v]
            if result and not result.get("raw_response")
            else None,
        )
    return result


async def swoop_company(url: str, page_title: str, page_text: str) -> dict[str, Any]:
    """
    Use Grok to extract a full structured account record from crawled company content.

    Returns a dict with keys:
      company_name, type, location, tags,
      key_personnel (list of {name, role, linkedin, x_handle}),
      recent_news (list of str), stock_ticker,
      triggers (list of str), intel_summary, suggested_touchpoint.

    Only public, professionally available information is used.
    """
    _TASK = "company_swoop"
    _TEMP = _TASK_TEMPERATURES[_TASK]
    system_prompt = (
        "You are an expert sales intelligence analyst. "
        "Extract a complete, structured company profile from the provided webpage content. "
        "Only use publicly available information. "
        "Return ONLY strictly valid JSON – no markdown, no code fences, no extra text – with these keys:\n"
        "  company_name (string),\n"
        "  type (one of: Operator, Hyperscale, Contractor, Colocation, Developer, Enterprise, Other),\n"
        "  location (string – city/country or region),\n"
        "  tags (list of short lowercase strings, e.g. [\"ai\", \"renewable\", \"2025-launch\"]),\n"
        "  key_personnel (list of objects: {name, role, linkedin, x_handle} – use null for unknown fields),\n"
        "  recent_news (list of up to 5 recent headline strings about the company),\n"
        "  stock_ticker (string like 'NASDAQ:MSFT' if publicly listed, else null),\n"
        "  triggers (list of up to 5 short trigger signal strings, e.g. funding rounds, hiring spikes, expansions),\n"
        "  intel_summary (string – 2-3 sentence summary of why this company is a target),\n"
        "  suggested_touchpoint (string – a short draft LinkedIn outreach message to the key decision-maker)."
    )
    user_content = (
        f"Company URL: {url}\n"
        f"Page title: {page_title}\n\n"
        f"Page content:\n{page_text[:7000]}"
    )

    raw = ""
    result: dict[str, Any] = {}
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, max_tokens=2000, temperature=_TEMP, task=_TASK
        )
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for website swoop; wrapping raw text")
        result = {"raw_response": raw, "company_name": page_title or "Unknown"}
    except Exception as exc:
        logger.error("Grok website swoop failed: %s", exc)
        raise
    finally:
        _governance_log(
            task=_TASK,
            temperature=_TEMP,
            system_prompt=system_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            result=result,
            source_text=page_text,
            claimed_values=[v for v in [str(result.get("company_name", "")), str(result.get("location", ""))] if v]
            if result and not result.get("raw_response")
            else None,
        )
    return result


async def research_social_media(company_name: str, crawl_text: str) -> dict[str, Any]:
    """
    Use Grok to synthesise recent LinkedIn and X.com (Twitter) posts for a company.

    Returns a dict with keys: linkedin_posts (list of str), x_posts (list of str).
    Only public, publicly-known post summaries are produced.
    """
    _TASK = "social_media_research"
    _TEMP = _TASK_TEMPERATURES[_TASK]
    system_prompt = (
        "You are a social media intelligence analyst. "
        "Based on the provided company content, synthesise what recent public LinkedIn and X.com (Twitter) posts "
        "from this company are likely to contain, drawing only on publicly known information about the company. "
        "ONLY use publicly available data — do NOT invent information. "
        "Return strictly valid JSON with keys: "
        "linkedin_posts (list of up to 5 strings — recent LinkedIn post summaries or topics), "
        "x_posts (list of up to 5 strings — recent X.com tweet summaries or topics). "
        "If insufficient public data is available for either platform, return an empty list for that key. "
        "Do not include any markdown or extra text outside the JSON object."
    )
    user_content = (
        f"Company: {company_name}\n\n"
        f"Public content:\n{crawl_text[:4000]}"
    )

    result: dict[str, Any] = {"linkedin_posts": [], "x_posts": []}
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, max_tokens=800, temperature=_TEMP, task=_TASK
        )
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(clean)
        result = {
            "linkedin_posts": parsed.get("linkedin_posts", []),
            "x_posts": parsed.get("x_posts", []),
        }
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for social media research")
    except Exception as exc:
        logger.error("Grok social media research failed: %s", exc)
        result = {"linkedin_posts": [], "x_posts": []}
    finally:
        _governance_log(
            task=_TASK,
            temperature=_TEMP,
            system_prompt=system_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            result=result,
        )
    return result


async def research_executives(company_name: str, exec_text: str) -> list[dict[str, Any]]:
    """
    Use Grok to build public professional profiles for company executives.

    Returns a list of dicts matching the ExecutiveProfile schema fields.
    Only public, professional data is extracted — no private or family information.
    """
    _TASK = "executive_research"
    _TEMP = _TASK_TEMPERATURES[_TASK]
    system_prompt = (
        "You are a professional sales intelligence analyst. "
        "Extract public professional profiles for executives mentioned in the provided text. "
        "ONLY use publicly available professional data. "
        "Do NOT include: private family info, home addresses, private social data, "
        "or anything behind login walls. "
        "Return strictly valid JSON: a list of objects with keys: "
        "name, role, professional_focus, public_interests, recent_interviews, "
        "conference_appearances, charity_involvement, communication_style, conversation_angles. "
        "Each value is a string or list of strings. "
        "Do not include any markdown or extra text outside the JSON array."
    )
    user_content = (
        f"Company: {company_name}\n\n"
        f"Leadership content:\n{exec_text[:4000]}"
    )

    result: list[dict[str, Any]] = []
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, max_tokens=1200, temperature=_TEMP, task=_TASK
        )
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(clean)
        if isinstance(parsed, dict):
            parsed = [parsed]
        result = parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for executive profiles")
    except Exception as exc:
        logger.error("Grok executive research failed: %s", exc)
        raise
    finally:
        # Verify claimed executive names appear in source text
        claimed = [str(p.get("name", "")) for p in result if isinstance(p, dict) and p.get("name")]
        _governance_log(
            task=_TASK,
            temperature=_TEMP,
            system_prompt=system_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            result=result,
            source_text=exec_text,
            claimed_values=claimed or None,
        )
    return result


async def extract_news_signals(company_name: str, news_text: str) -> list[dict[str, Any]]:
    """
    Use Grok to classify and summarise news articles into structured signals.

    Returns a list of dicts with keys: title, summary, category, published_at.
    """
    _TASK = "news_signals"
    _TEMP = _TASK_TEMPERATURES[_TASK]
    system_prompt = (
        "You are a corporate intelligence analyst monitoring news for infrastructure investment signals. "
        "Classify each news item and extract key signals. "
        "Categories: expansion, earnings, technology, competitor, hiring, funding, general. "
        "Return strictly valid JSON: a list of objects with keys: "
        "title, summary, category, published_at. "
        "Do not include any markdown or extra text outside the JSON array."
    )
    user_content = (
        f"Company: {company_name}\n\n"
        f"News content:\n{news_text[:5000]}"
    )

    result: list[dict[str, Any]] = []
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, max_tokens=1000, temperature=_TEMP, task=_TASK
        )
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(clean)
        result = parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for news signals")
    except Exception as exc:
        logger.error("Grok news extraction failed: %s", exc)
        raise
    finally:
        # Verify claimed news titles appear in source text
        claimed = [str(item.get("title", "")) for item in result if isinstance(item, dict) and item.get("title")]
        _governance_log(
            task=_TASK,
            temperature=_TEMP,
            system_prompt=system_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            result=result,
            source_text=news_text,
            claimed_values=claimed or None,
        )
    return result


async def generate_compliance_answer(
    requirement: str,
    category: str | None,
    company_context: str | None,
) -> dict[str, Any]:
    """
    Use Grok to draft a compliance answer for a tender requirement.

    Returns a dict with keys: ``answer``, ``compliance_status``, ``confidence``,
    ``evidence_suggestions``, ``caveats``.
    """
    _TASK = "compliance_answer"
    _TEMP = _TASK_TEMPERATURES[_TASK]
    system_prompt = (
        "You are a bid writer specialising in data centre infrastructure contracts. "
        "Given a tender requirement, draft a concise, professional compliance answer "
        "that a contractor would submit. "
        "Return strictly valid JSON with keys: "
        "answer (string – the draft response text), "
        "compliance_status (one of: yes, partial, no, tbc), "
        "confidence (float 0.0–1.0), "
        "evidence_suggestions (list of strings – documents or accreditations to reference), "
        "caveats (string – any important qualifications or assumptions). "
        "Do not include any markdown or text outside the JSON object."
    )

    ctx = f"Company context: {company_context}\n\n" if company_context else ""
    cat_note = f"Requirement category: {category}\n" if category else ""
    user_content = (
        f"{ctx}{cat_note}"
        f"Requirement:\n{requirement}"
    )

    raw = ""
    result: dict[str, Any] = {}
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, max_tokens=800, temperature=_TEMP, task=_TASK
        )
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for compliance answer; wrapping raw text")
        result = {
            "answer": raw,
            "compliance_status": "tbc",
            "confidence": 0.5,
            "evidence_suggestions": [],
            "caveats": "LLM response could not be structured.",
        }
    except Exception as exc:
        logger.error("Grok compliance answer generation failed: %s", exc)
        raise
    finally:
        _governance_log(
            task=_TASK,
            temperature=_TEMP,
            system_prompt=system_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            result=result,
        )
    return result


async def parse_document_requirements(
    document_text: str,
    doc_type: str,
) -> list[dict[str, Any]]:
    """
    Use Grok to extract structured compliance requirements from document text.

    Returns a list of dicts with keys: ``requirement``, ``category``.
    """
    _TASK = "document_parsing"
    _TEMP = _TASK_TEMPERATURES[_TASK]
    system_prompt = (
        "You are a bid analyst parsing tender documents for data centre infrastructure. "
        "Extract all compliance requirements from the document text provided. "
        "Focus on 'shall', 'must', 'required', 'should' statements. "
        f"Document type: {doc_type}. "
        "Return strictly valid JSON: a list of objects with keys: "
        "requirement (string – the full requirement text), "
        "category (string – one of: technical, commercial, legal, quality, hse, programme, general). "
        "Do not include any markdown or text outside the JSON array."
    )
    user_content = f"Document text:\n{document_text[:8000]}"

    raw = ""
    result: list[dict[str, Any]] = []
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, max_tokens=2000, temperature=_TEMP, task=_TASK
        )
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        parsed = json.loads(clean)
        result = parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for document requirements")
    except Exception as exc:
        logger.error("Grok document parsing failed: %s", exc)
        raise
    finally:
        _governance_log(
            task=_TASK,
            temperature=_TEMP,
            system_prompt=system_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            result=result,
        )
    return result


async def write_blog_post(
    topic: str,
    context: str,
    tone: str,
    target_persona: str,
    word_count: int,
    seo_keywords: str | None,
    cta: str | None,
) -> dict[str, Any]:
    """
    Use Grok to generate a blog post with social media variants.

    Returns a dict with keys: title, slug, body_markdown, meta_description,
    seo_keywords, linkedin_variant, x_variant.
    """
    _TASK = "blog_writing"
    _TEMP = _TASK_TEMPERATURES[_TASK]
    system_prompt = (
        "You are an expert B2B content writer specialising in infrastructure technology. "
        f"Write in a {tone} tone for a {target_persona} audience. "
        "Return strictly valid JSON with keys: "
        "title, slug, body_markdown, meta_description, seo_keywords, "
        "linkedin_variant, x_variant. "
        "slug must be URL-safe lowercase with hyphens. "
        "body_markdown must be full markdown content. "
        "meta_description must be under 160 characters. "
        "linkedin_variant: 3-5 sentence professional LinkedIn post. "
        "x_variant: under 280 characters. "
        "Do not include any markdown fences or extra text outside the JSON object."
    )

    keywords_note = f"Target SEO keywords: {seo_keywords}. " if seo_keywords else ""
    cta_note = f"End with CTA: {cta}. " if cta else ""

    user_content = (
        f"Topic: {topic}\n"
        f"Target word count: ~{word_count} words. "
        f"{keywords_note}{cta_note}\n\n"
        f"Research context:\n{context[:4000]}"
    )

    raw = ""
    result: dict[str, Any] = {}
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, max_tokens=3000, temperature=_TEMP, task=_TASK
        )
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for blog post; wrapping raw text")
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:80]
        result = {
            "title": topic,
            "slug": slug,
            "body_markdown": raw,
            "meta_description": "",
            "seo_keywords": seo_keywords or "",
            "linkedin_variant": "",
            "x_variant": "",
        }
    except Exception as exc:
        logger.error("Grok blog writing failed: %s", exc)
        raise
    finally:
        _governance_log(
            task=_TASK,
            temperature=_TEMP,
            system_prompt=system_prompt,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            result=result,
        )
    return result
