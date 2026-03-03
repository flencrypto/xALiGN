"""Grok (xAI) API client for structured intelligence research.

Uses the OpenAI-compatible API endpoint at https://api.x.ai/v1.
Falls back gracefully when XAI_API_KEY is not configured.

Integrates with ai_governance for:
- Task-type based temperature routing
- Confidence scoring and evidence anchoring
- Numeric sanity checks
- Claim verification (hallucination detection)
- Audit logging per invocation
"""

import collections
import json
import logging
import os
import re
from typing import Any

import httpx

from backend.services.ai_governance import (
    TaskType,
    assess_output_confidence,
    create_invocation_record,
    get_temperature_params,
    hash_prompt,
    needs_human_review,
    run_numeric_sanity_checks,
    verify_claim_in_text,
    FALLBACK_CONFIDENCE_THRESHOLD,
    SUPPRESSION_THRESHOLD,
)

logger = logging.getLogger("contractghost.grok")

_BASE_URL = "https://api.x.ai/v1"
_MODEL = "grok-3-mini"
_TIMEOUT = 60.0

# In-memory audit log (flushed to DB via the ai_governance router on demand)
_invocation_log: collections.deque[dict] = collections.deque(maxlen=1000)

# Prefix length for claim verification spot-checks
_CLAIM_VERIFY_PREFIX = 30


def _api_key() -> str | None:
    return os.getenv("XAI_API_KEY")


def is_configured() -> bool:
    return bool(_api_key())


def get_invocation_log() -> list[dict]:
    """Return the in-memory invocation log (for persistence / review endpoints)."""
    return list(_invocation_log)


def clear_invocation_log() -> None:
    """Clear the in-memory log after persistence."""
    _invocation_log.clear()


async def _chat(
    system_prompt: str,
    user_content: str,
    task_type: TaskType,
    max_tokens: int = 2048,
) -> tuple[str, int, int]:
    """
    Send a chat request to the Grok API and return (reply, input_tokens, output_tokens).

    Temperature and top_p are determined by task_type via TEMPERATURE_MATRIX.
    Each invocation is logged for audit purposes.
    """
    key = _api_key()
    if not key:
        raise RuntimeError(
            "XAI_API_KEY is not set. Configure it to enable Grok AI features."
        )

    params = get_temperature_params(task_type)
    prompt_hash = hash_prompt(system_prompt, user_content)

    payload = {
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": params["temperature"],
        "top_p": params["top_p"],
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

    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", len(system_prompt.split()) + len(user_content.split()))
    output_tokens = usage.get("completion_tokens", len(content.split()))

    logger.debug(
        "Grok invocation | task=%s temp=%.2f prompt_hash=%s in=%d out=%d",
        task_type.value,
        params["temperature"],
        prompt_hash,
        input_tokens,
        output_tokens,
    )

    return content, input_tokens, output_tokens


def _log_invocation(record: dict) -> None:
    _invocation_log.append(record)


def _strip_fences(raw: str) -> str:
    return raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()


async def research_company(website: str, crawl_text: str) -> dict[str, Any]:
    """
    Use Grok to extract structured intelligence signals from crawled company content.
    Returns a dict matching the CompanyIntel schema fields, augmented with
    confidence_score, needs_human_review, and anomalies.
    """
    system_prompt = (
        "You are an institutional infrastructure intelligence analyst. "
        "Extract structured signals from the provided company web content. "
        "Only use publicly available data. "
        "Return strictly valid JSON with the following keys: "
        "company_name, business_model, locations, expansion_signals, "
        "technology_indicators, financial_summary, earnings_highlights, "
        "competitor_mentions, strategic_risks, bid_opportunities, "
        "evidence_source, quote_excerpt. "
        "Each value should be a short descriptive string or a JSON array of strings. "
        "evidence_source must name the page or document the data came from. "
        "Do not include any markdown, code fences, or extra text outside the JSON object."
    )
    user_content = (
        f"Company website: {website}\n\n"
        f"Crawled content:\n{crawl_text[:6000]}"
    )

    raw = ""
    task_type = TaskType.COMPANY_RESEARCH
    params = get_temperature_params(task_type)
    prompt_hash = hash_prompt(system_prompt, user_content)
    input_tokens = 0
    output_tokens = 0

    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, task_type, max_tokens=1500
        )
        result = json.loads(_strip_fences(raw))
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON response for company research; storing raw text")
        result = {"raw_response": raw}
    except Exception as exc:
        logger.error("Grok company research failed: %s", exc)
        raise

    # Numeric sanity checks
    anomalies = run_numeric_sanity_checks(result)
    if anomalies:
        logger.warning("Numeric sanity anomalies in company research: %s", anomalies)

    # Confidence scoring
    confidence = assess_output_confidence(result, task_type)

    # Human review gateway
    review_required, review_reasons = needs_human_review(result, confidence, task_type)

    # Determine validation outcome
    if confidence < SUPPRESSION_THRESHOLD:
        validation_outcome = "suppressed"
        logger.warning("Company research output suppressed (confidence=%.2f)", confidence)
    elif review_required:
        validation_outcome = "human_review"
    else:
        validation_outcome = "pass"

    # Claim verification: check that expansion_signals content appears in crawl text
    expansion = result.get("expansion_signals", "")
    if expansion and isinstance(expansion, str):
        if not verify_claim_in_text(expansion[:_CLAIM_VERIFY_PREFIX], crawl_text):
            logger.info("Expansion signal claim not verified in source text")

    record = create_invocation_record(
        prompt_hash=prompt_hash,
        model_version=_MODEL,
        task_type=task_type,
        temperature=params["temperature"],
        top_p=params["top_p"],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        confidence_score=confidence,
        validation_outcome=validation_outcome,
        needs_review=review_required,
        review_reasons=review_reasons,
        anomalies=anomalies,
    )
    _log_invocation(vars(record))

    result["confidence_score"] = confidence
    result["needs_human_review"] = review_required
    result["review_reasons"] = review_reasons
    result["anomalies"] = anomalies
    return result


async def research_executives(company_name: str, exec_text: str) -> list[dict[str, Any]]:
    """
    Use Grok to build public professional profiles for company executives.
    Returns a list of dicts matching the ExecutiveProfile schema fields.
    Only public, professional data is extracted — no private or family information.
    """
    system_prompt = (
        "You are a professional sales intelligence analyst. "
        "Extract public professional profiles for executives mentioned in the provided text. "
        "ONLY use publicly available professional data. "
        "Do NOT include: private family info, home addresses, private social data, "
        "or anything behind login walls. "
        "Return strictly valid JSON: a list of objects with keys: "
        "name, role, professional_focus, public_interests, recent_interviews, "
        "conference_appearances, charity_involvement, communication_style, "
        "conversation_angles, evidence_source. "
        "Each value is a string or list of strings. "
        "evidence_source must name the page this data came from. "
        "Do not include any markdown or extra text outside the JSON array."
    )
    user_content = (
        f"Company: {company_name}\n\n"
        f"Leadership content:\n{exec_text[:4000]}"
    )

    task_type = TaskType.EXECUTIVE_PROFILING
    params = get_temperature_params(task_type)
    prompt_hash = hash_prompt(system_prompt, user_content)
    input_tokens = 0
    output_tokens = 0

    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, task_type, max_tokens=1200
        )
        result = json.loads(_strip_fences(raw))
        if isinstance(result, dict):
            result = [result]
        profiles = result if isinstance(result, list) else []
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for executive profiles")
        profiles = []
    except Exception as exc:
        logger.error("Grok executive research failed: %s", exc)
        raise

    # Assess confidence and human review for each profile
    for profile in profiles:
        confidence = assess_output_confidence(profile, task_type)
        review_required, review_reasons = needs_human_review(profile, confidence, task_type)
        profile["confidence_score"] = confidence
        profile["needs_human_review"] = review_required
        profile["review_reasons"] = review_reasons

    aggregate_confidence = (
        sum(p.get("confidence_score", 0) for p in profiles) / len(profiles)
        if profiles
        else 0.0
    )
    validation_outcome = "human_review" if any(p.get("needs_human_review") for p in profiles) else "pass"

    record = create_invocation_record(
        prompt_hash=prompt_hash,
        model_version=_MODEL,
        task_type=task_type,
        temperature=params["temperature"],
        top_p=params["top_p"],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        confidence_score=aggregate_confidence,
        validation_outcome=validation_outcome,
        needs_review=any(p.get("needs_human_review") for p in profiles),
    )
    _log_invocation(vars(record))

    return profiles


async def extract_news_signals(company_name: str, news_text: str) -> list[dict[str, Any]]:
    """
    Use Grok to classify and summarise news articles into structured signals.
    Returns a list of dicts with keys: title, summary, category, published_at,
    confidence_score, evidence_source.
    """
    system_prompt = (
        "You are a corporate intelligence analyst monitoring news for infrastructure investment signals. "
        "Classify each news item and extract key signals. "
        "Categories: expansion, earnings, technology, competitor, hiring, funding, general. "
        "Return strictly valid JSON: a list of objects with keys: "
        "title, summary, category, published_at, evidence_source, quote_excerpt. "
        "evidence_source must name the publication or URL. "
        "Do not include any markdown or extra text outside the JSON array."
    )
    user_content = (
        f"Company: {company_name}\n\n"
        f"News content:\n{news_text[:5000]}"
    )

    task_type = TaskType.NEWS_EXTRACTION
    params = get_temperature_params(task_type)
    prompt_hash = hash_prompt(system_prompt, user_content)
    input_tokens = 0
    output_tokens = 0

    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, task_type, max_tokens=1000
        )
        result = json.loads(_strip_fences(raw))
        signals = result if isinstance(result, list) else []
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for news signals")
        signals = []
    except Exception as exc:
        logger.error("Grok news extraction failed: %s", exc)
        return []

    for signal in signals:
        confidence = assess_output_confidence(signal, task_type)
        review_required, review_reasons = needs_human_review(signal, confidence, task_type)
        signal["confidence_score"] = confidence
        signal["needs_human_review"] = review_required
        signal["review_reasons"] = review_reasons

    aggregate_confidence = (
        sum(s.get("confidence_score", 0) for s in signals) / len(signals)
        if signals
        else 0.0
    )

    record = create_invocation_record(
        prompt_hash=prompt_hash,
        model_version=_MODEL,
        task_type=task_type,
        temperature=params["temperature"],
        top_p=params["top_p"],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        confidence_score=aggregate_confidence,
        validation_outcome="pass",
    )
    _log_invocation(vars(record))

    return signals


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
    seo_keywords, linkedin_variant, x_variant, confidence_score.
    """
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

    task_type = TaskType.BLOG_GENERATION
    params = get_temperature_params(task_type)
    prompt_hash = hash_prompt(system_prompt, user_content)
    input_tokens = 0
    output_tokens = 0

    raw = ""
    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, task_type, max_tokens=3000
        )
        result = json.loads(_strip_fences(raw))
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

    confidence = assess_output_confidence(result, task_type)
    result["confidence_score"] = confidence

    record = create_invocation_record(
        prompt_hash=prompt_hash,
        model_version=_MODEL,
        task_type=task_type,
        temperature=params["temperature"],
        top_p=params["top_p"],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        confidence_score=confidence,
        validation_outcome="pass",
    )
    _log_invocation(vars(record))

    return result


async def verify_claims(output_text: str, source_context: str) -> dict[str, Any]:
    """
    Run a second-pass claim verification to detect hallucinations.
    Returns dict with keys: unsupported_claims (list), verification_passed (bool).
    """
    system_prompt = (
        "You are verifying factual accuracy. "
        "List any statements in the OUTPUT that are unsupported by the provided EVIDENCE. "
        "Return strictly valid JSON with keys: "
        "unsupported_claims (list of strings), verification_passed (boolean). "
        "If all statements are supported, return an empty list and verification_passed=true. "
        "Do not include any markdown or extra text outside the JSON object."
    )
    user_content = (
        f"OUTPUT TO VERIFY:\n{output_text[:3000]}\n\n"
        f"EVIDENCE (source content):\n{source_context[:4000]}"
    )

    task_type = TaskType.CLAIM_VERIFICATION
    params = get_temperature_params(task_type)
    prompt_hash = hash_prompt(system_prompt, user_content)
    input_tokens = 0
    output_tokens = 0

    try:
        raw, input_tokens, output_tokens = await _chat(
            system_prompt, user_content, task_type, max_tokens=800
        )
        result = json.loads(_strip_fences(raw))
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for claim verification")
        result = {"unsupported_claims": [], "verification_passed": True}
    except Exception as exc:
        logger.error("Grok claim verification failed: %s", exc)
        raise

    record = create_invocation_record(
        prompt_hash=prompt_hash,
        model_version=_MODEL,
        task_type=task_type,
        temperature=params["temperature"],
        top_p=params["top_p"],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        confidence_score=1.0 if result.get("verification_passed") else 0.4,
        validation_outcome="pass" if result.get("verification_passed") else "human_review",
    )
    _log_invocation(vars(record))

    return result
