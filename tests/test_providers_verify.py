"""Unit tests for :func:`gotime.services.verify.verify_keys` and
:meth:`BaseProvider.verify` classification logic."""

from __future__ import annotations

import httpx
import pytest
import respx

from gotime.config import Settings
from gotime.providers.base import ProviderError, VerificationResult, _classify_provider_error
from gotime.providers.google import GoogleProvider
from gotime.providers.tomtom import TomTomProvider
from gotime.services.verify import verify_keys


@pytest.fixture
def google_only_settings() -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        google_maps_api_key="g-test",
        bing_maps_api_key=None,
        tomtom_api_key=None,
        here_api_key=None,
        mapquest_api_key=None,
        mapbox_api_key=None,
        azure_maps_api_key=None,
    )


def _google_ok() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "status": "OK",
            "routes": [
                {
                    "legs": [
                        {
                            "duration": {"value": 60},
                            "duration_in_traffic": {"value": 60},
                            "distance": {"value": 100},
                            "steps": [],
                        }
                    ]
                }
            ],
        },
    )


# ---------------------------------------------------------------------------
# _classify_provider_error edge cases
# ---------------------------------------------------------------------------


def test_classify_401_is_invalid():
    result = _classify_provider_error("google", ProviderError("google: HTTP 401: bad key", status_code=401))
    assert result.status == "invalid"


def test_classify_403_is_invalid():
    result = _classify_provider_error("here", ProviderError("here: HTTP 403: forbidden", status_code=403))
    assert result.status == "invalid"


def test_classify_429_is_rate_limited():
    result = _classify_provider_error("tomtom", ProviderError("tomtom: HTTP 429: too many", status_code=429))
    assert result.status == "rate_limited"


def test_classify_google_request_denied_no_status():
    # Google returns HTTP 200 with status=REQUEST_DENIED on bad keys;
    # the GoogleProvider converts that into a ProviderError without a
    # status_code. We still need to flag it as invalid.
    result = _classify_provider_error("google", ProviderError("google: status='REQUEST_DENIED' error='bad key'"))
    assert result.status == "invalid"


def test_classify_upstream_5xx_is_unreachable():
    result = _classify_provider_error("bing", ProviderError("bing: HTTP 503: boom", status_code=503))
    assert result.status == "unreachable"


def test_classify_transport_error_is_unreachable():
    result = _classify_provider_error("azure", ProviderError("azure: HTTP transport error: dns"))
    assert result.status == "unreachable"


def test_classify_unknown_is_error():
    result = _classify_provider_error("mapbox", ProviderError("mapbox: malformed response payload"))
    assert result.status == "error"


# ---------------------------------------------------------------------------
# BaseProvider.verify() on a real adapter (Google)
# ---------------------------------------------------------------------------


@respx.mock
def test_google_verify_ok():
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(return_value=_google_ok())
    with GoogleProvider(api_key="g-test") as p:
        result = p.verify()
    assert result == VerificationResult("google", "ok", None)


@respx.mock
def test_google_verify_request_denied_is_invalid():
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(
            200, json={"status": "REQUEST_DENIED", "error_message": "The provided API key is invalid."}
        )
    )
    with GoogleProvider(api_key="g-test") as p:
        result = p.verify()
    assert result.status == "invalid"


@respx.mock
def test_google_verify_http_401_is_invalid():
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )
    with GoogleProvider(api_key="g-test") as p:
        result = p.verify()
    assert result.status == "invalid"


@respx.mock
def test_google_verify_rate_limited():
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(429, text="Too Many Requests")
    )
    with GoogleProvider(api_key="g-test") as p:
        result = p.verify()
    assert result.status == "rate_limited"


@respx.mock
def test_google_verify_upstream_5xx_is_unreachable():
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(503, text="boom")
    )
    with GoogleProvider(api_key="g-test") as p:
        result = p.verify()
    assert result.status == "unreachable"


@respx.mock
def test_google_verify_transport_error_is_unreachable():
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        side_effect=httpx.ConnectError("dns failure")
    )
    with GoogleProvider(api_key="g-test") as p:
        result = p.verify()
    assert result.status == "unreachable"


@respx.mock
def test_tomtom_verify_ok():
    respx.get(url__regex=r"https://api\.tomtom\.com/routing/1/calculateRoute/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "routes": [
                    {
                        "summary": {
                            "travelTimeInSeconds": 60,
                            "lengthInMeters": 100,
                            "trafficDelayInSeconds": 0,
                        }
                    }
                ]
            },
        )
    )
    with TomTomProvider(api_key="t-test") as p:
        result = p.verify()
    assert result.status == "ok"


@respx.mock
def test_tomtom_verify_unauthorized_is_invalid():
    respx.get(url__regex=r"https://api\.tomtom\.com/routing/1/calculateRoute/.*").mock(
        return_value=httpx.Response(403, text="forbidden")
    )
    with TomTomProvider(api_key="t-test") as p:
        result = p.verify()
    assert result.status == "invalid"


# ---------------------------------------------------------------------------
# service-level verify_keys
# ---------------------------------------------------------------------------


@respx.mock
def test_verify_keys_reports_missing_without_request(google_only_settings):
    # Only google has a key; the others should be reported as 'missing' and
    # MUST NOT hit the network. We assert that by installing no respx routes
    # for them at all.
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(return_value=_google_ok())

    results = verify_keys(google_only_settings, ["google", "bing", "tomtom"])
    by_provider = {r.provider: r for r in results}
    assert by_provider["google"].status == "ok"
    assert by_provider["bing"].status == "missing"
    assert by_provider["tomtom"].status == "missing"


def test_verify_keys_unknown_provider_name(google_only_settings, monkeypatch):
    # Pretend we have a key for a bogus provider so we drop into get_provider
    # lookup; it should classify cleanly as `error` rather than blowing up.
    monkeypatch.setattr(type(google_only_settings), "api_key_for", lambda self, n: "x" if n == "bogus" else None)
    results = verify_keys(google_only_settings, ["bogus"])
    assert len(results) == 1
    assert results[0].provider == "bogus"
    assert results[0].status == "error"


@respx.mock
def test_verify_keys_default_provider_list(google_only_settings):
    # No `providers` arg means 'all registered adapters'. We only expose a key
    # for google, so every other provider must be 'missing'.
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(return_value=_google_ok())
    results = verify_keys(google_only_settings)
    statuses = {r.provider: r.status for r in results}
    assert statuses["google"] == "ok"
    assert all(v == "missing" for k, v in statuses.items() if k != "google")


def test_provider_error_carries_status_code():
    err = ProviderError("x: HTTP 429: throttle", status_code=429)
    assert err.status_code == 429
    plain = ProviderError("x: malformed response")
    assert plain.status_code is None
