"""Deduplication Engine – detects when multiple articles refer to the same infrastructure project.

Uses fuzzy string matching (rapidfuzz) to identify duplicate project signals.
Assigns a canonical project_id to grouped duplicates.
"""

import logging
import re
from typing import Any

logger = logging.getLogger("align.deduplication")

# Attempt to import rapidfuzz; fall back to simple string matching if unavailable.
try:
    from rapidfuzz import fuzz
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False
    logger.warning("rapidfuzz not installed; using basic string similarity fallback")


_SIMILARITY_THRESHOLD = 85  # Minimum score (0-100) to consider two records duplicates


def _normalise(text: str) -> str:
    """Normalise text for comparison: lowercase, strip punctuation, collapse spaces."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def similarity_score(a: str, b: str) -> float:
    """Return a similarity score between two strings (0-100)."""
    na, nb = _normalise(a), _normalise(b)
    if _HAS_RAPIDFUZZ:
        return fuzz.token_sort_ratio(na, nb)
    # Fallback: Jaccard similarity on word sets
    set_a = set(na.split())
    set_b = set(nb.split())
    if not set_a and not set_b:
        return 100.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return (intersection / union) * 100


def find_duplicates(
    records: list[dict[str, Any]],
    title_key: str = "title",
    id_key: str = "id",
) -> list[list[int]]:
    """Group record IDs that likely refer to the same project.

    Args:
        records: List of dicts each with at least `id_key` and `title_key` fields.
        title_key: Key containing the text to compare.
        id_key: Key containing the record identifier.

    Returns:
        List of groups, each group being a list of IDs for duplicate records.
    """
    groups: list[list[int]] = []
    assigned: set[int] = set()

    for i, rec_a in enumerate(records):
        if rec_a[id_key] in assigned:
            continue
        group = [rec_a[id_key]]
        for j, rec_b in enumerate(records):
            if i == j or rec_b[id_key] in assigned:
                continue
            score = similarity_score(str(rec_a[title_key]), str(rec_b[title_key]))
            if score >= _SIMILARITY_THRESHOLD:
                group.append(rec_b[id_key])
                assigned.add(rec_b[id_key])
        if len(group) > 1:
            assigned.update(group)
            groups.append(group)

    return groups


async def run_deduplication(db) -> dict[str, Any]:
    """Run deduplication over InfrastructureProject records.

    Flags duplicate projects and sets a canonical_id reference.
    Returns summary statistics.
    """
    from backend.models.projects import InfrastructureProject

    projects = db.query(InfrastructureProject).filter(
        InfrastructureProject.is_duplicate.is_(False)
    ).all()

    records = [{"id": p.id, "title": p.name, "location": p.location or ""} for p in projects]

    # Use combined name + location for better matching
    for r in records:
        r["title"] = f"{r['title']} {r['location']}"

    groups = find_duplicates(records)

    duplicates_found = 0
    for group in groups:
        # First ID in group becomes canonical
        canonical_id = group[0]
        for duplicate_id in group[1:]:
            project = db.query(InfrastructureProject).get(duplicate_id)
            if project:
                project.is_duplicate = True
                project.canonical_project_id = canonical_id
                duplicates_found += 1

    db.commit()

    return {
        "total_projects": len(projects),
        "duplicate_groups": len(groups),
        "duplicates_flagged": duplicates_found,
    }
