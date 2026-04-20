"""Azure Maps Route Directions adapter.

Docs: https://learn.microsoft.com/rest/api/maps/route/get-route-directions
"""

from __future__ import annotations

from gotime.models import TripResult, Waypoint
from gotime.providers.base import BaseProvider, ProviderError


class AzureProvider(BaseProvider):
    name = "azure"
    supports_traffic = True
    ENDPOINT = "https://atlas.microsoft.com/route/directions/json"

    def directions(self, origin: Waypoint, destination: Waypoint) -> TripResult:
        query = f"{origin.as_pair()}:{destination.as_pair()}"
        params = {
            "api-version": "1.0",
            "query": query,
            "traffic": "true",
            "travelMode": "car",
            "subscription-key": self.api_key,
        }
        data = self._get_json(self.ENDPOINT, params=params)

        try:
            summary = data["routes"][0]["summary"]
            duration = float(summary["travelTimeInSeconds"])
            distance = float(summary["lengthInMeters"])
            traffic_delay = float(summary.get("trafficDelayInSeconds", 0.0))
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("azure: malformed response payload") from exc

        return TripResult(
            provider=self.name,
            origin=origin,
            destination=destination,
            duration_seconds=duration - traffic_delay,
            duration_in_traffic_seconds=duration,
            distance_meters=distance,
            raw=data,
        )
