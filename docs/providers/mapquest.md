# MapQuest Directions

- **Product home**: <https://developer.mapquest.com/>
- **API reference**: <https://developer.mapquest.com/documentation/directions-api/route/get/>
- **Traffic**: yes (the `realTime` field in the route body).

## Endpoint

`GET https://www.mapquestapi.com/directions/v2/route`

## Parameters used

| Key | Value |
| --- | --- |
| `key` | API key |
| `from` | origin `"lat,lon"` |
| `to` | destination `"lat,lon"` |
| `unit` | `k` (kilometers — we convert to meters) |
| `routeType` | `fastest` |
| `doReverseGeocode` | `false` |

## Response fields we persist

- `route.time` → `duration_seconds`
- `route.realTime` → `duration_in_traffic_seconds` (falls back to `time`)
- `route.distance` (km → m) → `distance_meters`
