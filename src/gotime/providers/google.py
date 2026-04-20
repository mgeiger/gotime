"""Google Maps Directions API adapter.

Docs: https://developers.google.com/maps/documentation/directions/get-directions
"""

from __future__ import annotations

import time

from gotime.models import TripResult, Waypoint
from gotime.providers.base import BaseProvider, ProviderError


class GoogleProvider(BaseProvider):
    name = "google"
    supports_traffic = True
    ENDPOINT = "https://maps.googleapis.com/maps/api/directions/json"

    def directions(self, origin: Waypoint, destination: Waypoint) -> TripResult:
        params = {
            "origin": origin.as_pair(),
            "destination": destination.as_pair(),
            "mode": "driving",
            "traffic_model": "best_guess",
            "departure_time": str(int(time.time())),
            "key": self.api_key,
        }
        data = self._get_json(self.ENDPOINT, params=params)

        status = data.get("status")
        if status != "OK":
            raise ProviderError(f"google: status={status!r} error={data.get('error_message')!r}")

        try:
            leg = data["routes"][0]["legs"][0]
            duration = float(leg["duration"]["value"])
            distance = float(leg["distance"]["value"])
            duration_in_traffic = float(leg["duration_in_traffic"]["value"]) if "duration_in_traffic" in leg else None
            steps = len(leg.get("steps", [])) or None
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("google: malformed response payload") from exc

        return TripResult(
            provider=self.name,
            origin=origin,
            destination=destination,
            duration_seconds=duration,
            duration_in_traffic_seconds=duration_in_traffic,
            distance_meters=distance,
            steps=steps,
            raw=data,
        )
