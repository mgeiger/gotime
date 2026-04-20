"""HERE Routing v8 API adapter.

Docs: https://www.here.com/docs/bundle/routing-api-v8-api-reference/page/index.html
"""

from __future__ import annotations

from gotime.models import TripResult, Waypoint
from gotime.providers.base import BaseProvider, ProviderError


class HereProvider(BaseProvider):
    name = "here"
    supports_traffic = True
    ENDPOINT = "https://router.hereapi.com/v8/routes"

    def directions(self, origin: Waypoint, destination: Waypoint) -> TripResult:
        params = {
            "transportMode": "car",
            "origin": origin.as_pair(),
            "destination": destination.as_pair(),
            "return": "summary",
            "departureTime": "any",
            "apiKey": self.api_key,
        }
        data = self._get_json(self.ENDPOINT, params=params)

        try:
            section = data["routes"][0]["sections"][0]
            summary = section["summary"]
            duration = float(summary["baseDuration"])
            duration_in_traffic = float(summary.get("duration", duration))
            distance = float(summary["length"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("here: malformed response payload") from exc

        return TripResult(
            provider=self.name,
            origin=origin,
            destination=destination,
            duration_seconds=duration,
            duration_in_traffic_seconds=duration_in_traffic,
            distance_meters=distance,
            raw=data,
        )
