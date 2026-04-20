# Changelog

All notable changes to **gotime** are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
a [CalVer-flavoured `YYYY.MINOR.MICRO`](docs/versioning.md) scheme derived
from git tags via `hatch-vcs`. PEP 440 compliance is preserved.

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [2026.1.0] - 2026-04-20

First modern release after a long dormancy. The project was resurrected,
re-architected around a typed provider abstraction, and published back to
PyPI with reproducible, tag-driven builds and Read the Docs integration.

### Added

- Typed `TripResult` / `Waypoint` data model with unit-safe helpers.
- Tier-1 provider adapters: Google, Bing, TomTom, HERE, MapQuest, Mapbox, Azure,
  each going through a shared `BaseProvider` contract.
- Typer CLI: `gotime providers list`, `gotime providers verify`,
  `gotime verify-keys` (top-level alias), `gotime db info`, `gotime query`,
  with rich table and `--json` output modes.
- Live API-key verification (`verify-keys`) that classifies each provider as
  `ok` / `missing` / `invalid` / `rate_limited` / `unreachable` / `error`,
  suitable as a deploy gate.
- SQLAlchemy 2.x schema for `users`, `providers`, `locations`, `trips`,
  `trip_api_logs`, plus Alembic migrations `0001` (initial schema) and `0002`
  (trip dedup unique constraint, timestamp server defaults, hot-path indexes).
  SQLite and Postgres 16+ are both first-class.
- Schema-drift guard (`tests/test_schema_drift.py`) that compares the ORM
  against `scripts/merge/seed_canonical.sql` to prevent silent drift.
- Docker-based integration tests and a `pytest-cov` gate at 90 %.
- Sphinx documentation published to <https://gotime.readthedocs.io/en/latest/>
  with MyST Markdown, Mermaid ER diagrams, and `myst-parser[linkify]` for
  ergonomic cross-references.
- Pull-request template with a Keep-a-Changelog reminder and a
  `skip-changelog` escape hatch.
- CI `changelog` gate that fails PRs touching `src/gotime/`, `alembic/`, or
  `pyproject.toml` without also updating `CHANGELOG.md`.
- `CalVer (YYYY.MINOR.MICRO)` versioning driven entirely by `hatch-vcs` from
  git tags. `src/gotime/_version.py` is gitignored and regenerated on build.
- Tag-driven release pipeline: `verify-tag` (signed annotated, reachable from
  `main`, CHANGELOG section exists) → `build` → SLSA build-provenance
  `attest` → OIDC Trusted Publishing to PyPI behind a required-reviewer
  `pypi` GitHub Environment → GitHub Release (body pulled directly from
  `CHANGELOG.md`) → post-publish install smoke test.
- Operator scripts: `scripts/prepare-release.sh` (opens the
  `chore(release): X.Y.Z` PR) and `scripts/rollback-release.sh`
  (walks the maintainer through PyPI yanking + next-MICRO guidance).
- Runbooks: [`docs/release.md`](docs/release.md),
  [`docs/versioning.md`](docs/versioning.md), and
  [`CONTRIBUTING.md`](CONTRIBUTING.md) covering the full lifecycle.

### Changed

- Raw provider response storage (`trip_api_logs.raw_json`) is now **opt-in**
  via `GOTIME_STORE_RAW_RESPONSES=true` or the `store_raw=` kwarg. The
  default posture respects provider terms of service; see
  [`docs/compliance.md`](docs/compliance.md) for a per-provider matrix and
  authoritative links.
- Entire codebase rewritten. Legacy scripts and data dumps moved to the
  workspace `removal/` directory for operator-controlled archival.

### Security

- API keys live in `.env` files or GitHub Actions secrets — no hard-coded
  credentials anywhere in the shipped package. Ruff `S105`/`S106` rules are
  enabled to prevent regressions.
- Logging is routed through a `RedactingFilter` and `httpx` event hooks so
  keys never appear in logs, even on errors.
- Release tags must be GPG-signed annotated tags reachable from `main` and
  the `pypi` Environment requires a human approver before any artifact
  hits PyPI.

[Unreleased]: https://github.com/mgeiger/gotime/compare/2026.1.0...HEAD
[2026.1.0]: https://github.com/mgeiger/gotime/releases/tag/2026.1.0
