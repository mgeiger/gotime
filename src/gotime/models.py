"""Normalized data models shared across providers and persistence.

``TripResult`` is the canonical output every :class:`~gotime.providers.base.BaseProvider`
returns. Fields not supported by a given provider are left as ``None`` so the
downstream storage layer can record provenance without fabricating data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Waypoint:
    """Single latitude/longitude pair used as an origin or destination."""

    latitude: float
    longitude: float
    label: str | None = None

    def as_pair(self) -> str:
        """Return ``"lat,lon"`` formatted for most provider HTTP APIs."""

        return f"{self.latitude},{self.longitude}"


@dataclass(frozen=True, slots=True)
class TripResult:
    """Normalized routing result.

    All durations are in **seconds**; all distances are in **meters**. Use the
    helper properties (:attr:`duration_minutes`, :attr:`distance_miles`) when
    surfacing to humans.
    """

    provider: str
    origin: Waypoint
    destination: Waypoint
    duration_seconds: float
    distance_meters: float
    duration_in_traffic_seconds: float | None = None
    steps: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

    @property
    def duration_minutes(self) -> float:
        return self.duration_seconds / 60.0

    @property
    def duration_in_traffic_minutes(self) -> float | None:
        if self.duration_in_traffic_seconds is None:
            return None
        return self.duration_in_traffic_seconds / 60.0

    @property
    def distance_miles(self) -> float:
        return self.distance_meters * 0.000621371

    @property
    def supports_traffic(self) -> bool:
        return self.duration_in_traffic_seconds is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "origin": {
                "latitude": self.origin.latitude,
                "longitude": self.origin.longitude,
                "label": self.origin.label,
            },
            "destination": {
                "latitude": self.destination.latitude,
                "longitude": self.destination.longitude,
                "label": self.destination.label,
            },
            "duration_seconds": self.duration_seconds,
            "duration_in_traffic_seconds": self.duration_in_traffic_seconds,
            "distance_meters": self.distance_meters,
            "steps": self.steps,
            "fetched_at": self.fetched_at.isoformat(),
        }
