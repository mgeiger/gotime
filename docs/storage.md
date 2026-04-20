# Storage & persistence

The `gotime.services.query.persist_trip` helper writes, per successful
provider call:

1. A row in `trips` normalized to minutes/miles/UTC (always).
2. A best-effort upsert of the source/destination in `locations` keyed on
   `(user_id, nickname)` (always).
3. **Opt-in** — a row in `trip_api_logs` containing the *raw* provider JSON
   (JSONB on Postgres). Disabled by default because several providers'
   Terms of Service restrict or forbid long-term storage of raw responses;
   see [`compliance.md`](compliance.md) for the per-provider posture and the
   `GOTIME_STORE_RAW_RESPONSES` / `store_raw=` knobs that turn it on.

## Choosing a backend

- **SQLite** (default): `GOTIME_DATABASE_URL=sqlite:///./gotime.db`. Good for
  local exploration and tests; the trip volume in this project easily fits.
- **PostgreSQL** (production): install the extras (`pip install gotime[postgres]`)
  and set `GOTIME_DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db`.

The JSON blob column uses SQLAlchemy's generic `JSON` type, which maps to
`JSONB` on Postgres and `TEXT` on SQLite. No code changes are needed when you
move between backends.

## Retention & cost

Plan for two kinds of growth:

- **Row growth**: one `trips` row per API call, plus one `trip_api_logs`
  row *only if `GOTIME_STORE_RAW_RESPONSES=true`*. A collector that polls
  every 5 minutes during weekday work hours produces roughly 6,000 normalized
  rows per year. Cheap.
- **Blob growth** (opt-in path only): `raw_json` payloads are 2–10 KB each
  for most providers. The heaviest are Google Directions responses, which
  can be a few hundred KB when step geometry is requested. Configure
  providers to return minimal responses (we already default to summary-only
  where the API supports it).

If you turn on raw-response persistence, pair it with a retention policy
consistent with your chosen providers' ToS — e.g. 30 days for Google, no
long-term storage for Mapbox/Bing at all. See
[`compliance.md`](compliance.md) for the matrix.
