# Bing Maps Routes

- **Product home**: <https://www.microsoft.com/en-us/maps/bing-maps>
- **API reference**: <https://learn.microsoft.com/bingmaps/rest-services/routes/calculate-a-route>
- **Traffic**: yes (via `optimize=timeWithTraffic`).

## Endpoint

`GET https://dev.virtualearth.net/REST/v1/Routes/Driving`

## Parameters used

| Key | Value |
| --- | --- |
| `wp.0` | origin `"lat,lon"` |
| `wp.1` | destination `"lat,lon"` |
| `optimize` | `timeWithTraffic` |
| `routeAttributes` | `routeSummariesOnly` |
| `key` | API key |

## Response fields we persist

- `resourceSets[0].resources[0].travelDuration` → `duration_seconds`
- `resourceSets[0].resources[0].travelDurationTraffic` → `duration_in_traffic_seconds`
- `resourceSets[0].resources[0].travelDistance` (km → m) → `distance_meters`

## Caveats

- `travelDuration` is in seconds but `travelDistance` is in kilometers — we
  multiply by 1000 at parse time so storage stays in meters.
- Bing is being migrated into Azure Maps; keep an eye on the deprecation
  timeline published on Microsoft Learn.
