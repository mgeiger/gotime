"""TomTom Routing API adapter.

Docs: https://developer.tomtom.com/routing-api/documentation/routing/calculate-route
"""

from __future__ import annotations

from gotime.models import TripResult, Waypoint
from gotime.providers.base import BaseProvider, ProviderError


class TomTomProvider(BaseProvider):
    name = "tomtom"
    supports_traffic = True
    ENDPOINT = "https://api.tomtom.com/routing/1/calculateRoute/{coords}/json"

    def directions(self, origin: Waypoint, destination: Waypoint) -> TripResult:
        coords = f"{origin.as_pair()}:{destination.as_pair()}"
        params = {
            "key": self.api_key,
            "traffic": "true",
            "travelMode": "car",
            "routeType": "fastest",
        }
        url = self.ENDPOINT.format(coords=coords)
        data = self._get_json(url, params=params)

        try:
            summary = data["routes"][0]["summary"]
            duration = float(summary["travelTimeInSeconds"])
            distance = float(summary["lengthInMeters"])
            traffic_delay = float(summary.get("trafficDelayInSeconds", 0.0))
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("tomtom: malformed response payload") from exc

        return TripResult(
            provider=self.name,
            origin=origin,
            destination=destination,
            duration_seconds=duration - traffic_delay,
            duration_in_traffic_seconds=duration,
            distance_meters=distance,
            raw=data,
        )
