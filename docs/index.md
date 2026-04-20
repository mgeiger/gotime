# gotime

**gotime** is a multi-provider driving-directions library with a Typer CLI and
SQL persistence. This site documents the architecture, schema, provider
coverage, pricing / free-tier strategy, compliance posture for persisting
raw responses, and release engineering.

```{toctree}
:maxdepth: 2
:caption: Contents

architecture
schema
storage
compliance
pricing
versioning
release
roadmap
providers/index
```

## Legacy data migration

Older iterations of the project produced SQLite databases, Postgres dumps,
and CSV exports. The turnkey Docker pipeline for consolidating those into
a fresh `gotime` schema lives outside the PyPI package, in the workspace
at `scripts/merge/README.md`. That directory is deliberately not shipped
with the library — operators who need it should grab it from the
[gotime](https://github.com/mgeiger/gotime) repository.

## At a glance

- Tier-1 providers: Google, Bing, TomTom, HERE, MapQuest, Mapbox, Azure.
- Normalized `TripResult` with typed units (seconds, meters, plus helpers).
- SQLAlchemy 2.x schema with Alembic migrations (SQLite + Postgres).
- Black (120-col) + Ruff + mypy + pytest-cov ≥ 90 %.
- Dockerized integration tests and CI via GitHub Actions.

## Install

```bash
pip install gotime
```

## Quick CLI tour

```bash
gotime providers list
gotime db info
gotime query \
  --origin 42.3554,-71.0654 \
  --destination 42.3467,-71.0972 \
  --provider google --provider tomtom --json
```
