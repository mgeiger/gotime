# Compliance: persisting provider responses

`gotime` talks to commercial map/routing APIs. Most vendors' Terms of Service
restrict — or outright forbid — long-term storage of their raw responses.
This page documents the posture we've adopted and the knobs you can turn.

> **This page is an operator-facing summary written in April 2026 and is not
> legal advice.** Always confirm against the vendor's current ToS, AUP, and
> Data Processing Agreement before relying on it in production. Links to the
> authoritative documents are included below.

## Default behaviour

- **Normalized trips** — `trips` rows (duration, distance, steps, …) are
  always written. The normalized view is derived data about *your own*
  routes and is what the dashboards and statistics use.
- **Raw provider JSON** — `trip_api_logs.raw_json` is **not written** by
  default. Turning it on requires an explicit opt-in:
  - Environment: `GOTIME_STORE_RAW_RESPONSES=true` (truthy values:
    `1`, `true`, `yes`, `on`, case-insensitive).
  - Programmatic: `persist_trip(session, result, store_raw=True)` — the
    kwarg overrides the environment and is useful in tests.

The opt-in is intentional: several providers below explicitly prohibit the
kind of persistence a naïve `raw_json` column represents.

## Per-provider summary

| Provider | Raw-response storage | Cap | Notes |
| --- | --- | --- | --- |
| **Google Maps Platform** | Restricted | Lat/lon ≤ 30 days; Place IDs indefinite | Caching limits live in the [Directions API policies](https://developers.google.com/maps/documentation/directions/policies) and [Service Specific Terms](https://cloud.google.com/maps-platform/terms/maps-service-terms). Full response payloads are effectively not permitted long-term. |
| **Mapbox** | **Prohibited** | n/a | The [Mapbox Terms of Service](https://www.mapbox.com/legal/tos) state "you may not cache, store, or export any map content from the Services." Do not flip the opt-in on for Mapbox without a separate commercial agreement. |
| **Bing Maps** | **Prohibited** | n/a | The [Bing Maps End User ToS](https://www.microsoft.com/en-us/maps/bing-maps/product/enduserterms) forbid copying, caching, or retaining maps, routes, images, or other data provided by the service. |
| **Azure Maps** | Restricted (latency cache only) | shorter of header TTL or **6 months** | See the [Azure Maps product terms](https://www.microsoft.com/en-us/maps/product/terms) and the [Microsoft Q&A on caching policy](https://learn.microsoft.com/en-us/answers/questions/214472/azure-maps-caching-policy). Storage is allowed only to reduce application latency, not to redistribute or re-use across users. |
| **TomTom** | Unclear from public docs | — | See the [TomTom Developer ToC](https://developer.tomtom.com/terms-and-conditions) and the [data residency FAQ](https://developer.tomtom.com/knowledgebase/apis/faq/api-data-residency). Developer/Freemium plans generally do not grant long-term storage rights; confirm with TomTom support if you need it. |
| **HERE** | Unclear from public docs | — | See the [HERE Platform Terms](https://legal.here.com/en-gb/terms/here-platform/terms-may-2021) and the Acceptable Use Policy / Data Processing Agreement linked from it. Freemium plans typically forbid long-term storage of raw responses. |
| **MapQuest** | Standard plan restricted; Extended Rights available | — | See the [MapQuest Terms of Use](https://developer.mapquest.com/legal) and the [Extended Rights Geocoding](https://developer.mapquest.com/plans) add-on. Directions persistence rules are not spelled out publicly; conservative default is "don't store". |

## If you opt in

When you turn on `GOTIME_STORE_RAW_RESPONSES`, consider:

1. **Scope it per provider.** If some of your providers forbid storage,
   route their calls through a separate `gotime` instance (or a custom
   fork of `persist_trip`) with the flag off. The built-in toggle is
   process-wide, not per-provider.
2. **Implement a retention job.** The tightest common cap is Google's
   30-day lat/lon rule. A weekly job such as
   ```sql
   DELETE FROM trip_api_logs WHERE timestamp < NOW() - INTERVAL '30 days';
   ```
   keeps you inside that envelope. The normalized `trips` table is
   untouched.
3. **Re-check annually.** Vendor terms change. The links in the table
   above are authoritative; the matrix is just a human-readable index.

## Related

- Default behaviour and retention discussion: [`storage.md`](storage.md).
- Database schema, including the `trip_api_logs` table: [`schema.md`](schema.md).
- Live key-validity checks: run `gotime providers verify` (see
  [`architecture.md`](architecture.md)).
