from __future__ import annotations

from datetime import UTC, datetime

import httpx
import respx

from gotime.config import Settings
from gotime.db.models import Location, Provider, Trip, TripApiLog
from gotime.models import TripResult, Waypoint
from gotime.providers.base import ProviderError
from gotime.services.query import persist_trip, query_providers


@respx.mock
def test_query_providers_success_and_partial_failure(all_keys_settings, origin, destination):
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "OK",
                "routes": [{"legs": [{"duration": {"value": 60}, "distance": {"value": 100}, "steps": []}]}],
            },
        )
    )
    respx.get("https://router.hereapi.com/v8/routes").mock(return_value=httpx.Response(500, text="boom"))

    results = query_providers(origin, destination, ["google", "here"], all_keys_settings)
    assert isinstance(results["google"], TripResult)
    assert isinstance(results["here"], ProviderError)


def test_query_providers_missing_key(all_keys_settings, origin, destination):
    settings = all_keys_settings.__class__(
        database_url=all_keys_settings.database_url,
        google_maps_api_key=None,
        bing_maps_api_key=None,
        tomtom_api_key=None,
        here_api_key=None,
        mapquest_api_key=None,
        mapbox_api_key=None,
        azure_maps_api_key=None,
    )
    results = query_providers(origin, destination, ["google"], settings)
    assert isinstance(results["google"], ProviderError)
    assert "no API key" in str(results["google"])


def test_query_providers_unknown_name(all_keys_settings, origin, destination, monkeypatch):
    # Patch settings.api_key_for to pretend we have a key for an unregistered provider.
    monkeypatch.setattr(type(all_keys_settings), "api_key_for", lambda self, name: "x" if name == "bogus" else None)
    results = query_providers(origin, destination, ["bogus"], all_keys_settings)
    assert isinstance(results["bogus"], ProviderError)
    assert "unknown provider" in str(results["bogus"])


def test_persist_trip_creates_rows(db_session, origin, destination):
    tr = TripResult(
        provider="google",
        origin=origin,
        destination=destination,
        duration_seconds=600,
        duration_in_traffic_seconds=720,
        distance_meters=1609.34,
        steps=3,
        raw={"ok": True},
        fetched_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    trip = persist_trip(db_session, tr, user_id=None)
    assert trip.id is not None
    assert db_session.query(Provider).count() == 1
    assert db_session.query(Location).count() == 2
    assert db_session.query(Trip).count() == 1
    # raw_json persistence is opt-in for ToS reasons; the default path must
    # never write a `trip_api_logs` row.
    assert db_session.query(TripApiLog).count() == 0


def test_persist_trip_store_raw_opt_in_kwarg(db_session, origin, destination):
    tr = TripResult(
        provider="google",
        origin=origin,
        destination=destination,
        duration_seconds=600,
        distance_meters=1609.34,
        raw={"ok": True, "nested": {"k": 1}},
        fetched_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    persist_trip(db_session, tr, store_raw=True)
    logs = db_session.query(TripApiLog).all()
    assert len(logs) == 1
    assert logs[0].raw_json == {"ok": True, "nested": {"k": 1}}


def test_persist_trip_store_raw_from_settings(db_session, origin, destination, all_keys_settings):
    opt_in = Settings(
        database_url=all_keys_settings.database_url,
        google_maps_api_key="g",
        bing_maps_api_key=None,
        tomtom_api_key=None,
        here_api_key=None,
        mapquest_api_key=None,
        mapbox_api_key=None,
        azure_maps_api_key=None,
        store_raw_responses=True,
    )
    tr = TripResult(provider="google", origin=origin, destination=destination, duration_seconds=1, distance_meters=1)
    persist_trip(db_session, tr, settings=opt_in)
    assert db_session.query(TripApiLog).count() == 1


def test_persist_trip_kwarg_overrides_settings(db_session, origin, destination, all_keys_settings):
    opt_in = Settings(
        database_url=all_keys_settings.database_url,
        google_maps_api_key="g",
        bing_maps_api_key=None,
        tomtom_api_key=None,
        here_api_key=None,
        mapquest_api_key=None,
        mapbox_api_key=None,
        azure_maps_api_key=None,
        store_raw_responses=True,
    )
    tr = TripResult(provider="google", origin=origin, destination=destination, duration_seconds=1, distance_meters=1)
    persist_trip(db_session, tr, store_raw=False, settings=opt_in)
    assert db_session.query(TripApiLog).count() == 0


def test_persist_trip_reuses_existing_location(db_session, origin, destination):
    # Use distinct timestamps so the uq_trip_dedup constraint (provider,
    # timestamp, start, end) doesn't swallow the second row.
    tr1 = TripResult(
        provider="google",
        origin=origin,
        destination=destination,
        duration_seconds=1,
        distance_meters=1,
        fetched_at=datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
    )
    tr2 = TripResult(
        provider="google",
        origin=origin,
        destination=destination,
        duration_seconds=2,
        distance_meters=2,
        fetched_at=datetime(2026, 1, 1, 8, 5, tzinfo=UTC),
    )
    persist_trip(db_session, tr1)
    persist_trip(db_session, tr2)
    assert db_session.query(Location).count() == 2
    assert db_session.query(Trip).count() == 2
    assert db_session.query(Provider).count() == 1


def test_waypoint_without_label_uses_pair(db_session):
    wp = Waypoint(latitude=1.0, longitude=2.0)
    tr1 = TripResult(
        provider="bing",
        origin=wp,
        destination=wp,
        duration_seconds=1,
        distance_meters=1,
        fetched_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
    )
    tr2 = TripResult(
        provider="bing",
        origin=wp,
        destination=wp,
        duration_seconds=1,
        distance_meters=1,
        fetched_at=datetime(2026, 2, 1, 9, 5, tzinfo=UTC),
    )
    persist_trip(db_session, tr1)
    persist_trip(db_session, tr2)
    # Location dedup still kicks in even when both origin and destination
    # resolve to the same lat/lon pair.
    assert db_session.query(Location).count() == 1
    assert db_session.query(Trip).count() == 2
