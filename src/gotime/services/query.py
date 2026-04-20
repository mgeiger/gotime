"""Query one or more providers for the same trip and (optionally) persist."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.orm import Session

from gotime.config import Settings
from gotime.db.models import Location, Provider, Trip, TripApiLog
from gotime.models import TripResult, Waypoint
from gotime.providers.base import BaseProvider, ProviderError
from gotime.providers.registry import get_provider


def query_providers(
    origin: Waypoint,
    destination: Waypoint,
    providers: Iterable[str],
    settings: Settings,
    *,
    client_factory: type[BaseProvider] | None = None,
) -> dict[str, TripResult | ProviderError]:
    """Query every provider in ``providers`` for the same origin/destination.

    Returns a dict keyed by provider name where the value is either a
    :class:`TripResult` (success) or a :class:`ProviderError` (failure). This
    keeps the high-level API honest about partial failures instead of raising
    eagerly and masking otherwise-successful results.

    ``client_factory`` is only used by tests that need to inject a stub
    provider class.
    """

    out: dict[str, TripResult | ProviderError] = {}
    for name in providers:
        key = settings.api_key_for(name)
        if key is None:
            out[name] = ProviderError(f"{name}: no API key configured")
            continue
        try:
            provider_cls = client_factory or get_provider(name)
        except KeyError as exc:
            out[name] = ProviderError(str(exc))
            continue

        try:
            with provider_cls(api_key=key) as provider:
                out[name] = provider.directions(origin, destination)
        except ProviderError as exc:
            out[name] = exc
    return out


def persist_trip(
    session: Session,
    result: TripResult,
    *,
    user_id: int | None = None,
    store_raw: bool | None = None,
    settings: Settings | None = None,
) -> Trip:
    """Persist a single :class:`TripResult`.

    The normalized ``Trip`` row is always written. A companion
    ``TripApiLog`` row carrying the raw provider payload is **only** written
    when the operator has explicitly opted in, because several providers'
    terms of service (Mapbox, Bing, Google, Azure) restrict or forbid
    long-term storage of raw responses. See ``docs/compliance.md`` for the
    per-provider posture.

    The opt-in resolves in this order:

    1. Explicit ``store_raw`` kwarg (used by tests and internal callers).
    2. ``settings.store_raw_responses`` if a :class:`Settings` is passed.
    3. Default: ``False`` (no raw log row).

    :class:`Provider` and :class:`Location` rows are fetched by natural key
    and created on demand, so calling this helper repeatedly for the same
    route does not produce duplicate lookups.
    """

    if store_raw is None:
        store_raw = settings.store_raw_responses if settings is not None else False

    provider = session.query(Provider).filter_by(name=result.provider).one_or_none()
    if provider is None:
        provider = Provider(name=result.provider)
        session.add(provider)
        session.flush()

    start = _upsert_location(session, result.origin, user_id=user_id)
    end = _upsert_location(session, result.destination, user_id=user_id)

    trip = Trip(
        timestamp=result.fetched_at,
        start_location_id=start.id,
        end_location_id=end.id,
        duration=result.duration_minutes,
        duration_in_traffic=result.duration_in_traffic_minutes,
        distance=result.distance_miles,
        steps=result.steps,
        fuel_used=None,
        provider_id=provider.id,
        user_id=user_id,
    )
    session.add(trip)

    if store_raw:
        session.add(
            TripApiLog(
                timestamp=result.fetched_at,
                provider_id=provider.id,
                start_location_id=start.id,
                end_location_id=end.id,
                raw_json=result.raw,
            )
        )
    session.commit()
    return trip


def _upsert_location(session: Session, waypoint: Waypoint, *, user_id: int | None) -> Location:
    nickname = waypoint.label or waypoint.as_pair()
    existing = session.query(Location).filter(Location.nickname == nickname, Location.user_id == user_id).one_or_none()
    if existing is not None:
        return existing
    loc = Location(
        address=nickname,
        latitude=waypoint.latitude,
        longitude=waypoint.longitude,
        nickname=nickname,
        user_id=user_id,
    )
    session.add(loc)
    session.flush()
    return loc
