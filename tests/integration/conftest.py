"""Shared plumbing for integration tests.

Integration tests hit real provider APIs and are therefore:

* marked with ``@pytest.mark.integration`` (registered in ``pyproject.toml``) so
  they are excluded from the default ``pytest`` run, and
* automatically **skipped** when the corresponding ``<PROVIDER>_API_KEY``
  environment variable is empty or missing, so contributors without keys see
  ``skipped`` instead of ``errored``.
"""

from __future__ import annotations

import os

import pytest

from gotime.models import Waypoint

PROVIDER_TO_ENV = {
    "google": "GOOGLE_MAPS_API_KEY",
    "bing": "BING_MAPS_API_KEY",
    "tomtom": "TOMTOM_API_KEY",
    "here": "HERE_API_KEY",
    "mapquest": "MAPQUEST_API_KEY",
    "mapbox": "MAPBOX_API_KEY",
    "azure": "AZURE_MAPS_API_KEY",
}


@pytest.fixture
def get_key():
    """Return a helper that yields the configured key for a provider or skips."""

    def _get(provider: str) -> str:
        env = PROVIDER_TO_ENV[provider]
        value = os.getenv(env, "").strip()
        if not value:
            pytest.skip(f"{env} not set; skipping {provider} integration test")
        return value

    return _get


@pytest.fixture(scope="session")
def regression_route() -> tuple[Waypoint, Waypoint]:
    """Boston-Cambridge route every provider has good coverage for."""

    origin = Waypoint(latitude=42.360082, longitude=-71.058880, label="Boston City Hall")
    destination = Waypoint(latitude=42.373611, longitude=-71.109733, label="Harvard Square")
    return origin, destination
