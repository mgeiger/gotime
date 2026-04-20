# Mapbox Directions (driving-traffic)

- **Product home**: <https://www.mapbox.com/navigation>
- **API reference**: <https://docs.mapbox.com/api/navigation/directions/>
- **Traffic**: yes — we use the `driving-traffic` profile, which bakes live
  traffic into the top-level `duration`.

## Endpoint

`GET https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{coords}`

Coordinates are `lon,lat;lon,lat` (note: **longitude first** — opposite of
most other providers).

## Parameters used

| Key | Value |
| --- | --- |
| `alternatives` | `false` |
| `overview` | `false` |
| `steps` | `false` |
| `access_token` | API key |

## Response fields we persist

- `routes[0].duration` → both `duration_seconds` and `duration_in_traffic_seconds`
- `routes[0].distance` → `distance_meters`

## Caveats

- There is no separate "free-flow" duration on the driving-traffic profile.
  Downstream analytics that care about congestion percentage should compute
  it from the `driving` profile (not currently implemented in gotime).
