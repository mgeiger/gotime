from datetime import UTC, datetime

from gotime.models import TripResult, Waypoint


def test_waypoint_as_pair():
    wp = Waypoint(latitude=42.3554, longitude=-71.0654)
    assert wp.as_pair() == "42.3554,-71.0654"


def test_trip_result_defaults_and_helpers(origin, destination):
    now = datetime(2026, 1, 1, tzinfo=UTC)
    result = TripResult(
        provider="test",
        origin=origin,
        destination=destination,
        duration_seconds=600.0,
        distance_meters=1609.34,
        duration_in_traffic_seconds=720.0,
        steps=7,
        fetched_at=now,
    )
    assert result.duration_minutes == 10.0
    assert result.duration_in_traffic_minutes == 12.0
    assert round(result.distance_miles, 2) == 1.0
    assert result.supports_traffic is True

    no_traffic = TripResult(
        provider="test",
        origin=origin,
        destination=destination,
        duration_seconds=60.0,
        distance_meters=100.0,
    )
    assert no_traffic.duration_in_traffic_minutes is None
    assert no_traffic.supports_traffic is False

    dumped = result.to_dict()
    assert dumped["provider"] == "test"
    assert dumped["origin"]["label"] == "home"
    assert dumped["fetched_at"] == "2026-01-01T00:00:00+00:00"
