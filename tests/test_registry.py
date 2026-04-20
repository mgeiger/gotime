import pytest

from gotime.providers.base import BaseProvider
from gotime.providers.registry import available_providers, get_provider


def test_available_providers_sorted():
    names = available_providers()
    assert names == sorted(names)
    assert set(names) == {"azure", "bing", "google", "here", "mapbox", "mapquest", "tomtom"}


def test_get_provider_returns_subclass():
    cls = get_provider("GOOGLE")
    assert issubclass(cls, BaseProvider)


def test_get_provider_unknown_raises():
    with pytest.raises(KeyError):
        get_provider("nope")
