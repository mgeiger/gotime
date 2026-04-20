# Architecture

gotime separates **HTTP adapters** (`gotime.providers.*`) from **data models**
(`gotime.models`, `gotime.db`) and **user-facing surface** (`gotime.cli`). Each
layer has a narrow contract so we can swap parts without cascading rewrites.

```{mermaid}
flowchart LR
    CLI["gotime CLI (Typer)"] --> Svc["services.query"]
    SDK["Library users"] --> Svc
    Svc --> Prov["BaseProvider subclasses"]
    Svc --> DB["SQLAlchemy persistence"]
    Prov -->|HTTPS| APIs["Google / Bing / TomTom /<br/>HERE / MapQuest / Mapbox / Azure"]
    DB -->|SQL| Store[(SQLite / Postgres)]
```

## Layers

### Providers (`gotime/providers`)

- Each provider is a class with a `directions(origin, destination)` method
  returning a `TripResult`.
- They share an `httpx.Client` by default (constructed once per instance) and
  support being reused inside an integration loop via a context manager.
- Failures of any kind are surfaced as `ProviderError` — transport, non-200,
  non-JSON, or shape-mismatch payloads. Multi-provider queries never raise
  eagerly.

### Services (`gotime/services`)

- `query_providers` fans out across multiple providers and collects a dict
  that may contain either `TripResult` or `ProviderError`.
- `persist_trip` writes a normalized trip into SQLAlchemy-managed tables.
  The raw response payload is only written to `trip_api_logs.raw_json` when
  the operator explicitly opts in (`GOTIME_STORE_RAW_RESPONSES=true` or the
  `store_raw=` kwarg) — see [compliance](compliance.md) for why.
- `verify_keys` probes each configured provider with a short deterministic
  directions call and classifies the response as one of ``ok`` / ``missing``
  / ``invalid`` / ``rate_limited`` / ``unreachable`` / ``error``.

### Persistence (`gotime/db`)

- Declarative SQLAlchemy 2.x models targeting SQLite (default) and Postgres (>= 16).
- Alembic migrations live under `alembic/`.

### CLI (`gotime/cli.py`)

- Typer app exposing `providers list`, `providers verify`, `verify-keys`
  (top-level alias), `db info`, and `query`.
- Rich-rendered tables plus `--json` for machine consumption.
- Never prints credentials.

## Verifying keys

```bash
gotime providers verify                          # all providers, table output
gotime providers verify --provider google --json # one provider, JSON output
gotime verify-keys --timeout 5                   # top-level alias
```

The command exits non-zero if any probed provider reports ``invalid``,
``unreachable`` or ``error``, so it's safe to drop into a deploy gate.
``missing`` (no key configured) and ``rate_limited`` (key accepted but
throttled) are treated as passing — you still learn about them in the
output, they just don't fail the run.

## Configuration

All configuration is env-driven (`gotime.config.load_settings`). Values come
from the process environment with a `.env` file loaded automatically if present.
See `.env.example` for the recognized variables.
