"""Mapbox Directions API adapter.

Docs: https://docs.mapbox.com/api/navigation/directions/
"""

from __future__ import annotations

from gotime.models import TripResult, Waypoint
from gotime.providers.base import BaseProvider, ProviderError


class MapboxProvider(BaseProvider):
    name = "mapbox"
    supports_traffic = True
    ENDPOINT = "https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{coords}"

    def directions(self, origin: Waypoint, destination: Waypoint) -> TripResult:
        # Mapbox expects ``lon,lat`` (not ``lat,lon``) and a semicolon separator.
        coords = f"{origin.longitude},{origin.latitude};" f"{destination.longitude},{destination.latitude}"
        params = {
            "alternatives": "false",
            "overview": "false",
            "steps": "false",
            "access_token": self.api_key,
        }
        url = self.ENDPOINT.format(coords=coords)
        data = self._get_json(url, params=params)

        if data.get("code") not in ("Ok", None):
            raise ProviderError(f"mapbox: code={data.get('code')!r}")

        try:
            route = data["routes"][0]
            duration = float(route["duration"])
            distance = float(route["distance"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError("mapbox: malformed response payload") from exc

        return TripResult(
            provider=self.name,
            origin=origin,
            destination=destination,
            duration_seconds=duration,
            duration_in_traffic_seconds=duration,
            distance_meters=distance,
            raw=data,
        )
