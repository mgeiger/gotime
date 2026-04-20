# Google Maps Directions

- **Product home**: <https://mapsplatform.google.com/maps-products/>
- **API reference**: <https://developers.google.com/maps/documentation/directions/get-directions>
- **Traffic**: yes (via `traffic_model=best_guess` + `departure_time`).

## Endpoint

`GET https://maps.googleapis.com/maps/api/directions/json`

## Parameters used

| Key | Value |
| --- | --- |
| `origin` | `"lat,lon"` |
| `destination` | `"lat,lon"` |
| `mode` | `driving` |
| `traffic_model` | `best_guess` |
| `departure_time` | `now (unix seconds)` |
| `key` | API key |

## Response fields we persist

- `routes[0].legs[0].duration.value` → `duration_seconds`
- `routes[0].legs[0].duration_in_traffic.value` → `duration_in_traffic_seconds`
- `routes[0].legs[0].distance.value` → `distance_meters`
- `len(routes[0].legs[0].steps)` → `steps`

## Caveats

- Without `departure_time`, Google will not return `duration_in_traffic`.
- Responses can be very large (step geometry). Consider `fields=` masking in
  future versions to stay lean.
