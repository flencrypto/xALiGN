"""Blog auto-writer router with enhanced Grok generation."""

import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import BlogPost, BlogStatus, CompanyIntel
from backend.schemas.intel import (
    BlogGenerateRequest,
    BlogPostRead,
    BlogPostSummary,
    BlogPostUpdate,
)
from backend.services import grok_client
from backend.core.config import settings
from backend.services.integration_requirements import ensure_integration_configured

logger = logging.getLogger("align.blog")

router = APIRouter(prefix="/blog", tags=["Blog"])


def _make_unique_slug(base_slug: str, db: Session, exclude_id: int | None = None) -> str:
    """Ensure slug is unique by appending a counter if needed."""
    slug = base_slug[:80]
    candidate = slug
    counter = 1
    while True:
        q = db.query(BlogPost).filter(BlogPost.slug == candidate)
        if exclude_id:
            q = q.filter(BlogPost.id != exclude_id)
        if not q.first():
            return candidate
        candidate = f"{slug}-{counter}"
        counter += 1


# ── Generate Blog Post (enhanced Grok prompt) ─────────────────────────────────
@router.post(
    "/generate",
    response_model=BlogPostRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a blog post with Grok AI",
)
async def generate_blog_post(payload: BlogGenerateRequest, db: Session = Depends(get_db)):
    """
    Use Grok to write a structured, SEO-ready blog post.
    If company_intel_id is supplied, real intelligence is injected for grounded content.
    Requires XAI_API_KEY.
    """
    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    # Build rich context from company intel if provided
    context = ""
    if payload.company_intel_id:
        intel = db.get(CompanyIntel, payload.company_intel_id)
        if not intel:
            raise HTTPException(status_code=404, detail="Company intel not found")
        parts = [
            f"Company: {intel.company_name or intel.website or 'Unknown'}",
            f"Business model: {intel.business_model or 'N/A'}",
            f"Expansion signals: {intel.expansion_signals or 'N/A'}",
            f"Technology indicators: {intel.technology_indicators or 'N/A'}",
            f"Financial summary: {intel.financial_summary or 'N/A'}",
            f"Trigger signals: {', '.join(intel.trigger_signals) if intel.trigger_signals else 'None'}",
        ]
        context = "\n".join(parts)

    # Call Grok with enhanced prompt (handled in service, but router now passes full context)
    result = await grok_client.write_blog_post(
        topic=payload.topic,
        context=context,
        tone=payload.tone,
        target_persona=payload.target_persona,
        word_count=payload.word_count,
        seo_keywords=payload.seo_keywords,
        cta=payload.cta,
    )

    # Generate unique slug
    raw_slug = result.get("slug") or re.sub(r"[^a-z0-9]+", "-", payload.topic.lower()).strip("-")
    slug = _make_unique_slug(raw_slug, db)

    post = BlogPost(
        company_intel_id=payload.company_intel_id,
        title=result.get("title", payload.topic),
        slug=slug,
        body_markdown=result.get("body_markdown", ""),
        meta_description=result.get("meta_description", "")[:500] if result.get("meta_description") else None,
        seo_keywords=result.get("seo_keywords"),
        linkedin_variant=result.get("linkedin_variant"),
        x_variant=result.get("x_variant"),
        status=BlogStatus.draft,
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    logger.info(f"Generated blog post: {post.title} (slug: {slug})")
    return post


# ── List Blog Posts ───────────────────────────────────────────────────────────
@router.get("", response_model=list[BlogPostSummary], summary="List blog posts")
def list_blog_posts(
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all blog posts (with optional status filter)."""
    q = db.query(BlogPost).order_by(BlogPost.created_at.desc())
    if status_filter:
        q = q.filter(BlogPost.status == status_filter)
    return q.offset(skip).limit(limit).all()


# ── Get, Update, Approve, Publish, Delete ─────────────────────────────────────
@router.get("/{post_id}", response_model=BlogPostRead, summary="Get a blog post")
def get_blog_post(post_id: int, db: Session = Depends(get_db)):
    obj = db.get(BlogPost, post_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return obj


@router.patch("/{post_id}", response_model=BlogPostRead, summary="Update a blog post")
def update_blog_post(post_id: int, payload: BlogPostUpdate, db: Session = Depends(get_db)):
    obj = db.get(BlogPost, post_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Blog post not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{post_id}/approve", response_model=BlogPostRead, summary="Approve a blog post")
def approve_blog_post(post_id: int, db: Session = Depends(get_db)):
    """Mark a draft as approved (ready for publishing)."""
    obj = db.get(BlogPost, post_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Blog post not found")
    if obj.status == BlogStatus.published:
        raise HTTPException(status_code=409, detail="Post is already published")
    obj.status = BlogStatus.approved
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{post_id}/publish", response_model=BlogPostRead, summary="Publish an approved post")
def publish_blog_post(post_id: int, db: Session = Depends(get_db)):
    """Publish an approved post."""
    obj = db.get(BlogPost, post_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Blog post not found")
    if obj.status != BlogStatus.approved:
        raise HTTPException(status_code=409, detail="Post must be approved before publishing")
    obj.status = BlogStatus.published
    obj.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a blog post")
def delete_blog_post(post_id: int, db: Session = Depends(get_db)):
    obj = db.get(BlogPost, post_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Blog post not found")
    db.delete(obj)
    db.commit()
