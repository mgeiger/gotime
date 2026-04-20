"""Engine/session helpers.

Keeping this ultra-thin lets tests swap in SQLite without spinning up Postgres
while production deployments point at a real database via ``GOTIME_DATABASE_URL``.
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from gotime.db.models import Base


def create_engine_from_url(url: str, *, echo: bool = False) -> Engine:
    """Build a SQLAlchemy engine for the given URL and ensure tables exist."""

    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(url, echo=echo, future=True, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return engine


def make_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False, future=True)
