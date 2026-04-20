"""HTTP-mocked tests covering every Tier 1 provider."""

from __future__ import annotations

import httpx
import pytest
import respx

from gotime.providers.azure import AzureProvider
from gotime.providers.base import BaseProvider, ProviderError
from gotime.providers.bing import BingProvider
from gotime.providers.google import GoogleProvider
from gotime.providers.here import HereProvider
from gotime.providers.mapbox import MapboxProvider
from gotime.providers.mapquest import MapQuestProvider
from gotime.providers.tomtom import TomTomProvider


def test_base_provider_requires_api_key():
    class Dummy(BaseProvider):
        name = "dummy"

        def directions(self, origin, destination):  # pragma: no cover - tested via subclasses
            raise NotImplementedError

    with pytest.raises(ProviderError):
        Dummy(api_key="")


def test_context_manager_closes_owned_client(origin, destination):
    p = GoogleProvider(api_key="k")
    with p as opened:
        assert opened is p
    assert p._client.is_closed is True


def test_context_manager_does_not_close_external_client(origin, destination):
    client = httpx.Client()
    try:
        p = GoogleProvider(api_key="k", client=client)
        p.close()
        assert client.is_closed is False
    finally:
        client.close()


@respx.mock
def test_google_ok(origin, destination):
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "OK",
                "routes": [
                    {
                        "legs": [
                            {
                                "duration": {"value": 600},
                                "duration_in_traffic": {"value": 720},
                                "distance": {"value": 8000},
                                "steps": [{"x": 1}, {"x": 2}],
                            }
                        ]
                    }
                ],
            },
        )
    )
    with GoogleProvider(api_key="k") as p:
        r = p.directions(origin, destination)
    assert r.provider == "google"
    assert r.duration_seconds == 600
    assert r.duration_in_traffic_seconds == 720
    assert r.distance_meters == 8000
    assert r.steps == 2


@respx.mock
def test_google_not_ok_status(origin, destination):
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(200, json={"status": "ZERO_RESULTS"})
    )
    with pytest.raises(ProviderError), GoogleProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_google_malformed_payload(origin, destination):
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(200, json={"status": "OK", "routes": []})
    )
    with pytest.raises(ProviderError), GoogleProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_google_http_error(origin, destination):
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(500, text="boom")
    )
    with pytest.raises(ProviderError), GoogleProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_google_transport_error(origin, destination):
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(ProviderError), GoogleProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_google_non_json_response(origin, destination):
    respx.get("https://maps.googleapis.com/maps/api/directions/json").mock(
        return_value=httpx.Response(200, text="not-json")
    )
    with pytest.raises(ProviderError), GoogleProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_bing_ok(origin, destination):
    respx.get("https://dev.virtualearth.net/REST/v1/Routes/Driving").mock(
        return_value=httpx.Response(
            200,
            json={
                "statusCode": 200,
                "resourceSets": [
                    {
                        "resources": [
                            {"travelDuration": 600, "travelDurationTraffic": 720, "travelDistance": 10},
                        ]
                    }
                ],
            },
        )
    )
    with BingProvider(api_key="k") as p:
        r = p.directions(origin, destination)
    assert r.duration_seconds == 600
    assert r.duration_in_traffic_seconds == 720
    assert r.distance_meters == 10_000


@respx.mock
def test_bing_bad_status(origin, destination):
    respx.get("https://dev.virtualearth.net/REST/v1/Routes/Driving").mock(
        return_value=httpx.Response(200, json={"statusCode": 400})
    )
    with pytest.raises(ProviderError), BingProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_bing_malformed(origin, destination):
    respx.get("https://dev.virtualearth.net/REST/v1/Routes/Driving").mock(
        return_value=httpx.Response(200, json={"statusCode": 200, "resourceSets": []})
    )
    with pytest.raises(ProviderError), BingProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_tomtom_ok(origin, destination):
    respx.get(url__regex=r"https://api\.tomtom\.com/routing/1/calculateRoute/.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "routes": [
                    {"summary": {"travelTimeInSeconds": 720, "lengthInMeters": 9500, "trafficDelayInSeconds": 120}}
                ]
            },
        )
    )
    with TomTomProvider(api_key="k") as p:
        r = p.directions(origin, destination)
    assert r.duration_seconds == 600
    assert r.duration_in_traffic_seconds == 720
    assert r.distance_meters == 9500


@respx.mock
def test_tomtom_malformed(origin, destination):
    respx.get(url__regex=r"https://api\.tomtom\.com/routing/1/calculateRoute/.*").mock(
        return_value=httpx.Response(200, json={"routes": []})
    )
    with pytest.raises(ProviderError), TomTomProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_here_ok(origin, destination):
    respx.get("https://router.hereapi.com/v8/routes").mock(
        return_value=httpx.Response(
            200,
            json={"routes": [{"sections": [{"summary": {"baseDuration": 600, "duration": 720, "length": 9000}}]}]},
        )
    )
    with HereProvider(api_key="k") as p:
        r = p.directions(origin, destination)
    assert r.duration_seconds == 600
    assert r.duration_in_traffic_seconds == 720


@respx.mock
def test_here_malformed(origin, destination):
    respx.get("https://router.hereapi.com/v8/routes").mock(return_value=httpx.Response(200, json={}))
    with pytest.raises(ProviderError), HereProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_mapquest_ok(origin, destination):
    respx.get("https://www.mapquestapi.com/directions/v2/route").mock(
        return_value=httpx.Response(
            200,
            json={
                "info": {"statuscode": 0},
                "route": {"time": 600, "realTime": 720, "distance": 9.0},
            },
        )
    )
    with MapQuestProvider(api_key="k") as p:
        r = p.directions(origin, destination)
    assert r.duration_seconds == 600
    assert r.duration_in_traffic_seconds == 720
    assert r.distance_meters == 9000


@respx.mock
def test_mapquest_bad_status(origin, destination):
    respx.get("https://www.mapquestapi.com/directions/v2/route").mock(
        return_value=httpx.Response(200, json={"info": {"statuscode": 400}})
    )
    with pytest.raises(ProviderError), MapQuestProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_mapquest_malformed(origin, destination):
    respx.get("https://www.mapquestapi.com/directions/v2/route").mock(
        return_value=httpx.Response(200, json={"info": {"statuscode": 0}, "route": {}})
    )
    with pytest.raises(ProviderError), MapQuestProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_mapbox_ok(origin, destination):
    respx.get(url__regex=r"https://api\.mapbox\.com/directions/v5/mapbox/driving-traffic/.*").mock(
        return_value=httpx.Response(
            200,
            json={"code": "Ok", "routes": [{"duration": 600, "distance": 9000}]},
        )
    )
    with MapboxProvider(api_key="k") as p:
        r = p.directions(origin, destination)
    assert r.duration_seconds == 600
    assert r.distance_meters == 9000


@respx.mock
def test_mapbox_bad_code(origin, destination):
    respx.get(url__regex=r"https://api\.mapbox\.com/directions/v5/mapbox/driving-traffic/.*").mock(
        return_value=httpx.Response(200, json={"code": "NoRoute"})
    )
    with pytest.raises(ProviderError), MapboxProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_mapbox_malformed(origin, destination):
    respx.get(url__regex=r"https://api\.mapbox\.com/directions/v5/mapbox/driving-traffic/.*").mock(
        return_value=httpx.Response(200, json={"code": "Ok", "routes": []})
    )
    with pytest.raises(ProviderError), MapboxProvider(api_key="k") as p:
        p.directions(origin, destination)


@respx.mock
def test_azure_ok(origin, destination):
    respx.get("https://atlas.microsoft.com/route/directions/json").mock(
        return_value=httpx.Response(
            200,
            json={
                "routes": [
                    {"summary": {"travelTimeInSeconds": 720, "lengthInMeters": 9000, "trafficDelayInSeconds": 120}}
                ]
            },
        )
    )
    with AzureProvider(api_key="k") as p:
        r = p.directions(origin, destination)
    assert r.duration_seconds == 600
    assert r.duration_in_traffic_seconds == 720


@respx.mock
def test_azure_malformed(origin, destination):
    respx.get("https://atlas.microsoft.com/route/directions/json").mock(
        return_value=httpx.Response(200, json={"routes": []})
    )
    with pytest.raises(ProviderError), AzureProvider(api_key="k") as p:
        p.directions(origin, destination)
