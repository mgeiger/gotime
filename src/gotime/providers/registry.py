"""Central registry for provider adapters.

Keep additions in **alphabetical order** to keep diffs reviewable. Aliases are
useful when a legacy config uses capitalized names (e.g. ``"GOOGLE"``).
"""

from __future__ import annotations

from gotime.providers.azure import AzureProvider
from gotime.providers.base import BaseProvider
from gotime.providers.bing import BingProvider
from gotime.providers.google import GoogleProvider
from gotime.providers.here import HereProvider
from gotime.providers.mapbox import MapboxProvider
from gotime.providers.mapquest import MapQuestProvider
from gotime.providers.tomtom import TomTomProvider

_PROVIDERS: dict[str, type[BaseProvider]] = {
    "azure": AzureProvider,
    "bing": BingProvider,
    "google": GoogleProvider,
    "here": HereProvider,
    "mapbox": MapboxProvider,
    "mapquest": MapQuestProvider,
    "tomtom": TomTomProvider,
}


def available_providers() -> list[str]:
    """Return the sorted list of registered provider names."""

    return sorted(_PROVIDERS.keys())


def get_provider(name: str) -> type[BaseProvider]:
    """Look up a provider class by short name.

    Raises:
        KeyError: if ``name`` is not a known provider.
    """

    key = name.strip().lower()
    if key not in _PROVIDERS:
        raise KeyError(f"unknown provider: {name!r}. Known providers: {available_providers()}")
    return _PROVIDERS[key]
