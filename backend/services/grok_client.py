"""Grok (xAI) API client for structured intelligence research.

Uses the OpenAI-compatible API endpoint at https://api.x.ai/v1.
Falls back gracefully when XAI_API_KEY is not configured.
"""

import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger("contractghost.grok")

_BASE_URL = "https://api.x.ai/v1"
_MODEL = "grok-3-mini"
_TIMEOUT = 60.0


def _api_key() -> str | None:
    return os.getenv("XAI_API_KEY")


def is_configured() -> bool:
    return bool(_api_key())


async def _chat(system_prompt: str, user_content: str, max_tokens: int = 2048) -> str:
    """Send a chat request to the Grok API and return the assistant reply."""
    key = _api_key()
    if not key:
        raise RuntimeError("XAI_API_KEY is not set. Configure it to enable Grok AI features.")

    payload = {
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
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
        return data["choices"][0]["message"]["content"]


async def research_company(website: str, crawl_text: str) -> dict[str, Any]:
    """
    Use Grok to extract structured intelligence signals from crawled company content.

    Returns a dict matching the CompanyIntel schema fields.
    """
    system_prompt = (
        "You are an institutional infrastructure intelligence analyst. "
        "Extract structured signals from the provided company web content. "
        "Only use publicly available data. "
        "Return strictly valid JSON with the following keys: "
        "company_name, business_model, locations, expansion_signals, "
        "technology_indicators, financial_summary, earnings_highlights, "
        "competitor_mentions, strategic_risks, bid_opportunities. "
        "Each value should be a short descriptive string or a JSON array of strings. "
        "Do not include any markdown, code fences, or extra text outside the JSON object."
    )
    user_content = (
        f"Company website: {website}\n\n"
        f"Crawled content:\n{crawl_text[:6000]}"
    )

    raw = ""
    try:
        raw = await _chat(system_prompt, user_content, max_tokens=1500)
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON response for company research; storing raw text")
        return {"raw_response": raw}
    except Exception as exc:
        logger.error("Grok company research failed: %s", exc)
        raise


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
        "conference_appearances, charity_involvement, communication_style, conversation_angles. "
        "Each value is a string or list of strings. "
        "Do not include any markdown or extra text outside the JSON array."
    )
    user_content = (
        f"Company: {company_name}\n\n"
        f"Leadership content:\n{exec_text[:4000]}"
    )

    try:
        raw = await _chat(system_prompt, user_content, max_tokens=1200)
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
        if isinstance(result, dict):
            result = [result]
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for executive profiles")
        return []
    except Exception as exc:
        logger.error("Grok executive research failed: %s", exc)
        raise


async def extract_news_signals(company_name: str, news_text: str) -> list[dict[str, Any]]:
    """
    Use Grok to classify and summarise news articles into structured signals.

    Returns a list of dicts with keys: title, summary, category, published_at.
    """
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

    try:
        raw = await _chat(system_prompt, user_content, max_tokens=1000)
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for news signals")
        return []
    except Exception as exc:
        logger.error("Grok news extraction failed: %s", exc)
        raise


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
    try:
        raw = await _chat(system_prompt, user_content, max_tokens=3000)
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("Grok returned non-JSON for blog post; wrapping raw text")
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:80]
        return {
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
