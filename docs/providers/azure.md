# Azure Maps Route

- **Product home**: <https://azure.microsoft.com/en-us/products/azure-maps>
- **API reference**: <https://learn.microsoft.com/rest/api/maps/route/get-route-directions>
- **Traffic**: yes (`traffic=true`).

## Endpoint

`GET https://atlas.microsoft.com/route/directions/json`

## Parameters used

| Key | Value |
| --- | --- |
| `api-version` | `1.0` |
| `query` | `origin:destination` (`"lat,lon:lat,lon"`) |
| `traffic` | `true` |
| `travelMode` | `car` |
| `subscription-key` | API key |

## Response fields we persist

- `routes[0].summary.travelTimeInSeconds` → `duration_in_traffic_seconds`
- `routes[0].summary.travelTimeInSeconds - trafficDelayInSeconds` → `duration_seconds`
- `routes[0].summary.lengthInMeters` → `distance_meters`
