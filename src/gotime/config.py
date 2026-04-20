"""Configuration loader.

All user-facing knobs are resolved from environment variables (optionally backed
by a ``.env`` file). Centralizing this avoids the legacy pattern of hard-coding
keys inside scripts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _parse_bool(raw: str | None, *, default: bool = False) -> bool:
    """Parse an env-var string into a bool without raising on unknown values."""

    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY


@dataclass(frozen=True, slots=True)
class Settings:
    """Resolved runtime settings."""

    database_url: str
    google_maps_api_key: str | None
    bing_maps_api_key: str | None
    tomtom_api_key: str | None
    here_api_key: str | None
    mapquest_api_key: str | None
    mapbox_api_key: str | None
    azure_maps_api_key: str | None
    # Off by default for ToS reasons - most providers restrict or forbid
    # long-term storage of raw responses. See docs/compliance.md. Operators
    # can flip `GOTIME_STORE_RAW_RESPONSES=true` to re-enable `trip_api_logs`
    # writes when they've confirmed their plan allows it.
    store_raw_responses: bool = False

    def api_key_for(self, provider: str) -> str | None:
        """Return the API key associated with ``provider`` (normalized to lowercase)."""

        lookup = {
            "google": self.google_maps_api_key,
            "bing": self.bing_maps_api_key,
            "tomtom": self.tomtom_api_key,
            "here": self.here_api_key,
            "mapquest": self.mapquest_api_key,
            "mapbox": self.mapbox_api_key,
            "azure": self.azure_maps_api_key,
        }
        return lookup.get(provider.lower())


def load_settings(env_file: str | os.PathLike[str] | None = None) -> Settings:
    """Read configuration from the environment.

    If ``env_file`` is provided (or a ``.env`` exists next to the CWD), values
    from it are merged into ``os.environ`` — without clobbering anything the
    caller has already set. This keeps CI/prod environments authoritative.
    """

    if env_file is not None:
        load_dotenv(Path(env_file), override=False)
    else:
        load_dotenv(override=False)

    return Settings(
        database_url=os.getenv("GOTIME_DATABASE_URL", "sqlite:///./gotime.db"),
        google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY"),
        bing_maps_api_key=os.getenv("BING_MAPS_API_KEY"),
        tomtom_api_key=os.getenv("TOMTOM_API_KEY"),
        here_api_key=os.getenv("HERE_API_KEY"),
        mapquest_api_key=os.getenv("MAPQUEST_API_KEY"),
        mapbox_api_key=os.getenv("MAPBOX_API_KEY"),
        azure_maps_api_key=os.getenv("AZURE_MAPS_API_KEY"),
        store_raw_responses=_parse_bool(os.getenv("GOTIME_STORE_RAW_RESPONSES"), default=False),
    )
