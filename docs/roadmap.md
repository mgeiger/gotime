# Development roadmap

This page tracks the near-term direction for `gotime`. Every item
lives here — not in PM reviews, not in scattered TODO comments — so that a
contributor can open a single document and see what is coming.

## Short term

### Python 3.13 → 3.14 migration

`gotime` currently targets **Python 3.13**. The move to 3.14 is
intentionally deferred because the `scripts/merge/` importer image builds
`pandas` from source on `python:3.14-slim`:

- `pandas` ≤ 2.2.3 does **not** publish a `cp314-manylinux_*` wheel.
- `python:3.14-slim` does not include a C compiler toolchain (`gcc`,
  `g++`, `cc`), so the build fails with
  `ERROR: Unknown compiler(s): [['cc'], ['gcc'], ['clang'], …]`.

Mitigation already shipped: `pandas` was **removed** from the importer
image because the SQLite/CSV importers only rely on the standard library
(`csv`, `sqlite3`) plus `psycopg[binary]` and `sqlalchemy`. The importer
still builds cleanly on 3.14 today.

Upgrade checklist (when `pandas` or any other transitive dep we introduce
ships a 3.14 wheel, or when upstream adds a `gcc`-bearing official slim
variant):

1. Flip `requires-python`, classifiers, `.python-version`, `target-version`
   (`black`, `ruff`, `mypy`), Docker base images, Read the Docs config,
   and CI workflows from `3.13` → `3.14`.
2. Run `uv lock --upgrade` (when we adopt a lockfile) and `pytest`
   against both Python versions in a temporary CI matrix.
3. Delete this section from the roadmap, update `docs/versioning.md`
   compatibility statement, and add a `CHANGELOG.md` entry.

### Documentation polish

- Cross-link every provider doc from the CLI `providers list` output.

## Tier 2 provider integrations

The current Tier 1 providers (Google, Bing, TomTom, HERE, MapQuest, Mapbox,
Azure) cover the commercial routing market. Tier 2 providers will add
open-source / ecosystem-specific options once Tier 1 is stable on 3.14.

| Provider | Status | Notes |
| --- | --- | --- |
| **Apple MapKit (Directions)** | Planned | Requires JWT-based MapKit JS tokens. Needs a dedicated auth flow and private-key handling distinct from the existing API-key model. |
| **Valhalla** (self-hosted or Mapbox-hosted) | Planned | Open source. Unifies nicely with MapTiler / Stadia stacks. |
| **OSRM** | Planned | Open source, fast, no traffic data; useful as a baseline. |
| **GraphHopper** | Stretch | Has a hosted API and open core. |
| **Stadia Maps / Mapillary Routing** | Stretch | Already have partial historical data in the legacy dumps (see `scripts/legacy_data_manifest.md`). |

Tier 2 work is tracked under `docs/providers/tier2-placeholder.md`
(planned) and will land as a single `gotime[tier2]` extras group so that
library users can opt in to heavier dependencies.

## Longer term

- Ship pre-computed trip-delta rollups (hourly / daily) as Postgres
  materialized views managed through Alembic.
