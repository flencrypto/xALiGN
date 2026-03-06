"""Lightweight schema migration helper.

Adds new columns to existing tables without dropping data.
SQLAlchemy's create_all() only creates *new* tables; it won't
add new columns to existing ones. This module fills that gap.
"""

import logging

from sqlalchemy import inspect, text

from backend.database import engine

logger = logging.getLogger("align.migrations")

# Each entry: (table_name, column_name, column_def)
# column_def is the SQL fragment after the column name (type + default).
_MIGRATIONS: list[tuple[str, str, str]] = [
    # accounts – new columns added incrementally
    ("accounts", "website",       "VARCHAR(2048)"),
    ("accounts", "logo_url",      "VARCHAR(2048)"),
    ("accounts", "stage",         "VARCHAR(100)"),
    ("accounts", "tags",          "VARCHAR(500)"),
    # company_intel – social / stock fields
    ("company_intel", "stock_ticker",  "VARCHAR(20)"),
    ("company_intel", "stock_price",   "VARCHAR(100)"),
    ("company_intel", "linkedin_posts", "TEXT"),
    ("company_intel", "x_posts",        "TEXT"),
    # call_intelligence – key points extracted from transcript
    ("call_intelligence", "key_points", "TEXT"),
    # intelligence – processing layer fields
    ("infrastructure_announcements", "confidence_score", "REAL"),
    ("infrastructure_announcements", "signal_type",      "VARCHAR(100)"),
    ("news_articles",               "confidence_score", "REAL"),
    ("news_articles",               "signal_type",      "VARCHAR(100)"),
]


def run_migrations() -> None:
    """Add any missing columns declared in _MIGRATIONS."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.connect() as conn:
        for table, column, col_def in _MIGRATIONS:
            if table not in existing_tables:
                continue  # table doesn't exist yet; create_all will handle it

            existing_cols = {c["name"] for c in inspector.get_columns(table)}
            if column in existing_cols:
                continue  # already present

            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                conn.commit()
                logger.info("Migration: added column %s.%s", table, column)
            except Exception as exc:
                logger.warning("Migration skipped for %s.%s: %s", table, column, exc)
