"""MapQuest Directions API adapter.

Docs: https://developer.mapquest.com/documentation/directions-api/route/get/
"""

from __future__ import annotations

from gotime.models import TripResult, Waypoint
from gotime.providers.base import BaseProvider, ProviderError


class MapQuestProvider(BaseProvider):
    name = "mapquest"
    supports_traffic = True
    ENDPOINT = "https://www.mapquestapi.com/directions/v2/route"

    def directions(self, origin: Waypoint, destination: Waypoint) -> TripResult:
        params = {
            "key": self.api_key,
            "from": origin.as_pair(),
            "to": destination.as_pair(),
            "unit": "k",
            "routeType": "fastest",
            "doReverseGeocode": "false",
        }
        data = self._get_json(self.ENDPOINT, params=params)

        info = data.get("info", {})
        if info.get("statuscode") not in (0, None):
            raise ProviderError(f"mapquest: statuscode={info.get('statuscode')!r}")

        try:
            route = data["route"]
            duration = float(route["time"])
            real_time = float(route.get("realTime", duration))
            distance_km = float(route["distance"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError("mapquest: malformed response payload") from exc

        return TripResult(
            provider=self.name,
            origin=origin,
            destination=destination,
            duration_seconds=duration,
            duration_in_traffic_seconds=real_time,
            distance_meters=distance_km * 1000.0,
            raw=data,
        )
