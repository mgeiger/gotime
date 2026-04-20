# HERE Routing v8

- **Product home**: <https://www.here.com/platform/routing>
- **API reference**: <https://www.here.com/docs/bundle/routing-api-v8-api-reference/page/index.html>
- **Traffic**: yes (the `summary.duration` field reflects traffic when
  `departureTime=any` or a specific time is passed).

## Endpoint

`GET https://router.hereapi.com/v8/routes`

## Parameters used

| Key | Value |
| --- | --- |
| `transportMode` | `car` |
| `origin` | `"lat,lon"` |
| `destination` | `"lat,lon"` |
| `return` | `summary` |
| `departureTime` | `any` |
| `apiKey` | API key |

## Response fields we persist

- `routes[0].sections[0].summary.baseDuration` → `duration_seconds`
- `routes[0].sections[0].summary.duration` → `duration_in_traffic_seconds`
- `routes[0].sections[0].summary.length` → `distance_meters`
