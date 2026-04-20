"""Drift guard between the ORM models and ``scripts/merge/seed_canonical.sql``.

The merge importers in the workspace's ``scripts/merge/`` folder run against
raw SQL — they don't import the ORM. That means the canonical SQL and the
SQLAlchemy models in :mod:`gotime.db.models` have to stay aligned by hand.

This test parses ``seed_canonical.sql`` when it's available (it isn't shipped
in the PyPI package) and asserts that every UNIQUE / INDEX on ``trips`` and
every ``DEFAULT NOW()`` column have a matching counterpart on the ORM side.
If the file isn't there (library-only checkout) the test is skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import Index, UniqueConstraint

from gotime.db.models import Trip, TripApiLog


def _find_seed_sql() -> Path | None:
    """Walk up from this file to find ``scripts/merge/seed_canonical.sql``.

    Returns ``None`` when the file is absent, which is the expected state
    for a library-only checkout (the PyPI sdist doesn't bundle
    ``scripts/``).
    """

    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "scripts" / "merge" / "seed_canonical.sql"
        if candidate.is_file():
            return candidate
    return None


SEED_SQL = _find_seed_sql()
skip_if_missing = pytest.mark.skipif(
    SEED_SQL is None,
    reason="scripts/merge/seed_canonical.sql not present (library-only checkout)",
)


# ---- parsing helpers -------------------------------------------------------


_CREATE_INDEX_RE = re.compile(
    r"CREATE\s+(UNIQUE\s+)?INDEX(?:\s+IF\s+NOT\s+EXISTS)?\s+"
    r"(?P<name>\w+)\s+ON\s+(?P<table>\w+)\s*\((?P<columns>[^)]+)\)",
    re.IGNORECASE,
)
_DEFAULT_NOW_RE = re.compile(
    r"^\s*(?P<column>\w+)\b[^,]*?DEFAULT\s+NOW\(\)",
    re.IGNORECASE | re.MULTILINE,
)


def _parse_indexes(sql: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for match in _CREATE_INDEX_RE.finditer(sql):
        columns = [c.strip() for c in match.group("columns").split(",")]
        out.append(
            {
                "name": match.group("name"),
                "table": match.group("table"),
                "columns": columns,
                "unique": bool(match.group(1)),
            }
        )
    return out


def _parse_default_now_columns(sql: str) -> set[str]:
    return {m.group("column") for m in _DEFAULT_NOW_RE.finditer(sql)}


# ---- ORM introspection -----------------------------------------------------


def _orm_indexes(model: type) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for arg in getattr(model, "__table_args__", ()):
        if isinstance(arg, UniqueConstraint):
            out[arg.name] = {
                "unique": True,
                "columns": [c.name for c in arg.columns],
            }
        elif isinstance(arg, Index):
            out[arg.name] = {
                "unique": bool(arg.unique),
                "columns": [c.name for c in arg.columns],
            }
    return out


# ---- the actual assertions -------------------------------------------------


@skip_if_missing
def test_seed_sql_trips_indexes_are_mirrored_in_orm():
    assert SEED_SQL is not None
    sql = SEED_SQL.read_text(encoding="utf-8")

    sql_indexes = [i for i in _parse_indexes(sql) if i["table"] == "trips"]
    assert sql_indexes, "seed_canonical.sql has no trips indexes; parser drift?"

    orm = _orm_indexes(Trip)
    for entry in sql_indexes:
        name = entry["name"]
        assert name in orm, (
            f"seed_canonical.sql defines `{name}` on trips but the ORM "
            f"does not. Add a matching Index/UniqueConstraint to "
            f"Trip.__table_args__, or drop the SQL side."
        )
        assert (
            orm[name]["unique"] == entry["unique"]
        ), f"unique mismatch for `{name}`: SQL={entry['unique']}, ORM={orm[name]['unique']}"
        assert (
            orm[name]["columns"] == entry["columns"]
        ), f"column-list mismatch for `{name}`: SQL={entry['columns']}, ORM={orm[name]['columns']}"


@skip_if_missing
def test_seed_sql_default_now_columns_have_server_defaults_on_orm():
    assert SEED_SQL is not None
    sql = SEED_SQL.read_text(encoding="utf-8")

    sql_defaults = _parse_default_now_columns(sql)
    assert sql_defaults, "seed_canonical.sql has no DEFAULT NOW() columns; parser drift?"

    for column_name in sql_defaults:
        # Both timestamps today; if canonical SQL adds more, this loop
        # covers them automatically.
        matched = False
        for model in (Trip, TripApiLog):
            column = model.__table__.columns.get(column_name)
            if column is None:
                continue
            matched = True
            assert column.server_default is not None, (
                f"{model.__tablename__}.{column_name} has DEFAULT NOW() in "
                f"seed_canonical.sql but no server_default= on the ORM. "
                f"Add server_default=func.now() to gotime.db.models."
            )
        assert matched, (
            f"seed_canonical.sql has DEFAULT NOW() on `{column_name}` but no "
            f"ORM model (Trip / TripApiLog) declares a column with that name."
        )


@skip_if_missing
def test_seed_sql_references_only_known_tables():
    """Sanity check - the parser should not hallucinate table names."""

    assert SEED_SQL is not None
    sql = SEED_SQL.read_text(encoding="utf-8")
    tables = {i["table"] for i in _parse_indexes(sql)}
    # Everything the SQL indexes should be in the ORM. New tables are fine;
    # they just don't need index-drift coverage yet.
    known = {"trips", "trip_api_logs", "locations", "providers", "users"}
    unexpected = tables - known
    assert not unexpected, f"unexpected tables referenced by indexes: {unexpected}"
