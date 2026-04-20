# TomTom Routing

- **Product home**: <https://developer.tomtom.com/products/routing-api>
- **API reference**: <https://developer.tomtom.com/routing-api/documentation/routing/calculate-route>
- **Traffic**: yes (`traffic=true`).

## Endpoint

`GET https://api.tomtom.com/routing/1/calculateRoute/{origin}:{destination}/json`

Coordinates are colon-separated (`lat,lon:lat,lon`).

## Parameters used

| Key | Value |
| --- | --- |
| `key` | API key |
| `traffic` | `true` |
| `travelMode` | `car` |
| `routeType` | `fastest` |

## Response fields we persist

- `routes[0].summary.travelTimeInSeconds` → `duration_in_traffic_seconds`
- `routes[0].summary.travelTimeInSeconds - trafficDelayInSeconds` → `duration_seconds`
- `routes[0].summary.lengthInMeters` → `distance_meters`
