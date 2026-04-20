"""SQLAlchemy ORM models.

Units:
    - ``Trip.duration`` — minutes (seconds / 60)
    - ``Trip.distance`` — miles  (meters * 0.000621371)
    - ``Trip.timestamp`` — UTC, aware

Dialect notes:
    - ``TripApiLog.raw_json`` uses the generic :class:`sqlalchemy.JSON` type.
      On the PostgreSQL dialect this becomes ``JSONB`` (matching the canonical
      ``scripts/merge/seed_canonical.sql``); on SQLite it degrades to ``TEXT``
      with JSON serialization, which keeps the local dev loop simple.
    - ``Trip.timestamp`` / ``TripApiLog.timestamp`` have both a Python-side
      ``default=_utcnow`` (so SQLite inserts without a server default still
      work) and a ``server_default=NOW()`` (so the Postgres schema matches
      the merge importers, which rely on DB-level defaults for idempotency).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Common declarative base shared by all ORM models."""


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    tz: Mapped[str | None] = mapped_column(String)

    locations: Mapped[list[Location]] = relationship(back_populates="user")


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    trips: Mapped[list[Trip]] = relationship(back_populates="provider")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    nickname: Mapped[str | None] = mapped_column(String)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    user: Mapped[User | None] = relationship(back_populates="locations")

    __table_args__ = (UniqueConstraint("user_id", "nickname", name="uq_location_nickname_per_user"),)


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
    start_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    end_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    duration: Mapped[float | None] = mapped_column(Float)
    duration_in_traffic: Mapped[float | None] = mapped_column(Float)
    distance: Mapped[float | None] = mapped_column(Float)
    steps: Mapped[int | None] = mapped_column(Integer)
    fuel_used: Mapped[float | None] = mapped_column(Float)
    provider_id: Mapped[int | None] = mapped_column(ForeignKey("providers.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    start_location: Mapped[Location | None] = relationship(foreign_keys=[start_location_id])
    end_location: Mapped[Location | None] = relationship(foreign_keys=[end_location_id])
    provider: Mapped[Provider | None] = relationship(back_populates="trips")

    __table_args__ = (
        # Dedup guard used by the legacy merge importers' ON CONFLICT logic.
        # Keep the column order and name in sync with
        # scripts/merge/seed_canonical.sql.
        UniqueConstraint(
            "provider_id",
            "timestamp",
            "start_location_id",
            "end_location_id",
            name="uq_trip_dedup",
        ),
        Index("ix_trip_timestamp", "timestamp"),
        Index("ix_trip_provider", "provider_id"),
    )


class TripApiLog(Base):
    __tablename__ = "trip_api_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
    provider_id: Mapped[int | None] = mapped_column(ForeignKey("providers.id"))
    start_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    end_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
