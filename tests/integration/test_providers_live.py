"""Live provider smoke tests.

Each test hits the real provider and asserts that:

* the provider responded with ``duration_seconds > 0``,
* the raw payload was captured into ``TripResult.raw``,
* no credential material leaked into any captured log line.

Run locally with::

    export GOOGLE_MAPS_API_KEY=...
    pytest -m integration gotime/tests/integration

Any provider whose key is missing simply skips.
"""

from __future__ import annotations

import logging

import pytest

from gotime import available_providers, configure_logging, get_provider

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("provider_name", sorted(available_providers()))
def test_provider_round_trip(
    provider_name: str,
    get_key,
    regression_route,
    caplog: pytest.LogCaptureFixture,
) -> None:
    key = get_key(provider_name)
    configure_logging(level=logging.DEBUG)
    caplog.set_level(logging.DEBUG)

    origin, destination = regression_route
    provider_cls = get_provider(provider_name)
    with provider_cls(api_key=key) as provider:
        trip = provider.directions(origin, destination)

    assert trip.provider == provider_name
    assert trip.duration_seconds > 0
    assert trip.distance_meters > 0
    assert trip.raw, "raw payload should be captured for archival"

    combined_log = "\n".join(rec.getMessage() for rec in caplog.records)
    assert key not in combined_log, f"{provider_name} leaked its API key into logs"
