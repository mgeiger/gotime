"""Bing Maps Routes API adapter.

Docs: https://learn.microsoft.com/bingmaps/rest-services/routes/calculate-a-route
"""

from __future__ import annotations

from gotime.models import TripResult, Waypoint
from gotime.providers.base import BaseProvider, ProviderError


class BingProvider(BaseProvider):
    name = "bing"
    supports_traffic = True
    ENDPOINT = "https://dev.virtualearth.net/REST/v1/Routes/Driving"

    def directions(self, origin: Waypoint, destination: Waypoint) -> TripResult:
        params = {
            "wp.0": origin.as_pair(),
            "wp.1": destination.as_pair(),
            "optimize": "timeWithTraffic",
            "routeAttributes": "routeSummariesOnly",
            "key": self.api_key,
        }
        data = self._get_json(self.ENDPOINT, params=params)

        if data.get("statusCode") != 200:
            raise ProviderError(f"bing: statusCode={data.get('statusCode')!r}")

        try:
            resource = data["resourceSets"][0]["resources"][0]
            duration = float(resource["travelDuration"])
            duration_in_traffic = float(resource.get("travelDurationTraffic", duration))
            distance_km = float(resource["travelDistance"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("bing: malformed response payload") from exc

        return TripResult(
            provider=self.name,
            origin=origin,
            destination=destination,
            duration_seconds=duration,
            duration_in_traffic_seconds=duration_in_traffic,
            distance_meters=distance_km * 1000.0,
            raw=data,
        )
