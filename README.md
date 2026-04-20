# gotime

[![PyPI version](https://img.shields.io/pypi/v/gotime.svg)](https://pypi.org/project/gotime/)
[![Python versions](https://img.shields.io/pypi/pyversions/gotime.svg)](https://pypi.org/project/gotime/)
[![Documentation Status](https://readthedocs.org/projects/gotime/badge/?version=latest)](https://gotime.readthedocs.io/en/latest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**gotime** is a multi-provider driving-directions library and Typer-powered
command-line tool. It gives you a single, typed API on top of the major
commercial routing services — Google Maps, Bing Maps, TomTom, HERE, MapQuest,
Mapbox and Azure Maps — along with a SQLAlchemy persistence layer that stores
trips and raw API responses for later analysis.

## Installation

```bash
pip install gotime          # library + CLI
pip install "gotime[postgres]"  # add psycopg2 for Postgres storage
```

You also need API keys for any provider you plan to use; see
[`docs/pricing.md`](docs/pricing.md) for signup links and free-tier guidance.

## Quickstart

```bash
export GOOGLE_MAPS_API_KEY=your-key
gotime providers list
gotime providers verify                         # probe every configured key
gotime query \
    --origin 42.3554,-71.0654 \
    --destination 42.3467,-71.0972 \
    --provider google --provider tomtom
```

The coordinates above are public Boston landmarks (Boston Common and Fenway
Park), included as a recognizable short commute for demo and testing purposes.

`gotime providers verify` (aliased as `gotime verify-keys`) issues a tiny
directions call per provider and classifies the response as `ok`,
`missing`, `invalid`, `rate_limited`, `unreachable` or `error`. Add
`--provider google` to narrow the probe, `--json` for CI consumption, and
`--timeout 5` to shorten the per-call deadline.

Or drop a `.env` file next to where you invoke the CLI:

```bash
cp .env.example .env
$EDITOR .env   # fill in the keys you have
gotime query --origin 42.36,-71.07 --destination 42.35,-71.10
```

### Library usage

```python
from gotime import Waypoint, query_providers
from gotime.config import load_settings

settings = load_settings()
results = query_providers(
    origin=Waypoint(42.3554, -71.0654, label="home"),
    destination=Waypoint(42.3467, -71.0972, label="work"),
    providers=["google", "tomtom"],
    settings=settings,
)

for name, result in results.items():
    if hasattr(result, "duration_minutes"):
        print(name, f"{result.duration_minutes:.1f} min", f"{result.distance_miles:.1f} mi")
    else:
        print(name, "error:", result)
```

## Features

- **Seven Tier-1 providers** with a normalized `TripResult` contract. Providers
  that don't support a field (e.g. duration-in-traffic on Mapbox's base
  `driving` profile) return `None` so you never have to guess.
- **Typer CLI** with rich table / JSON output and no hidden global state.
- **SQLAlchemy 2.x** persistence (`users`, `providers`, `locations`, `trips`,
  `trip_api_logs`) plus Alembic migrations. Swap SQLite ↔ Postgres with a URL.
- **Docker-first tests** with ≥ 90 % line coverage enforced in CI.
- **Typed, Black-formatted, Ruff-linted** Python 3.13 code (3.14 migration tracked in `docs/roadmap.md`).

## Repository layout

```
gotime/
├── src/gotime/          # library source (see docs/architecture.md)
├── tests/               # pytest-cov suite (mocks HTTP via respx)
├── docs/                # Sphinx site published to Read the Docs
├── alembic/             # DB migrations
├── Dockerfile           # slim image for CI integration tests
├── docker-compose.test.yml
├── pyproject.toml       # hatchling build, PEP 621 metadata
└── .github/workflows/   # CI, integration, publish, docs
```

## Development

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install --editable ".[dev]"

black --check src tests
ruff check src tests
pytest               # pytest.ini_options sets --cov-fail-under=90
```

Or run everything in Docker:

```bash
docker compose --file docker-compose.test.yml up --build --abort-on-container-exit
```

### Running CI locally

Three tiers, ordered by fidelity. Pick the one that matches what you're trying
to verify.

**1. Fast loop** — the commands above, annotated with the `.github/workflows/`
step they mirror:

```bash
black --check src tests                        # ci.yml -> lint
ruff check src tests                           # ci.yml -> lint
mypy                                           # ci.yml -> types (non-blocking)
sphinx-build -W -b html docs docs/_build/html  # docs.yml
pytest                                         # ci.yml -> test (sqlite leg)
```

The new `changelog` gate in [`ci.yml`](.github/workflows/ci.yml) can be
previewed locally against the current PR's base branch:

```bash
# Mirrors ci.yml -> changelog
git diff --name-only origin/main... \
  | grep --extended-regexp '^(src/gotime/|alembic/|pyproject\.toml$)' \
  && git diff --name-only origin/main... | grep --fixed-strings 'CHANGELOG.md' \
  || echo "Add a CHANGELOG entry before pushing, or apply the 'skip-changelog' label."
```

**2. Docker fast-path** — covers the Postgres leg that `ci.yml`'s matrix runs:

```bash
docker compose --file docker-compose.test.yml up --build --abort-on-container-exit
```

**3. Full-fidelity via [`act`](https://github.com/nektos/act)** — runs the raw
`.github/workflows/*.yml` files:

```bash
curl --silent --show-error --location \
    https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

./bin/act --list
./bin/act --workflows .github/workflows/ci.yml
./bin/act --workflows .github/workflows/docs.yml
```

Caveats:

- `act` needs Docker (≈500 MB runner image).
- `services:` containers usually need `--container-options "--network host"`.
- Integration secrets (`GOOGLE_MAPS_API_KEY`, …) are not auto-present — supply
  via `--secret-file .secrets` or let `integration.yml` skip (it already
  `skipif`s on missing keys).

## Release process

gotime uses calendar-anchored semantic versioning (`YYYY.MINOR.MICRO`) derived
automatically from git tags via [`hatch-vcs`](https://github.com/ofek/hatch-vcs).
Version strings are never hand-edited.

The full runbook lives in [`docs/release.md`](docs/release.md). In short:

1. Run `scripts/prepare-release.sh 2026.MINOR.MICRO` from `main`. It opens a
   PR whose only change is moving `## [Unreleased]` in `CHANGELOG.md` to the
   new release section.
2. Merge the PR.
3. `git pull --ff-only origin main`, then `git tag --annotate --sign 2026.MINOR.MICRO`
   and `git push origin 2026.MINOR.MICRO`.
4. Approve the `pypi` GitHub Environment deployment. Everything else
   (build, provenance attestation, PyPI publish via OIDC, GitHub Release,
   install smoke-test, Read the Docs rebuild) is automated.

## License

MIT — see [`LICENSE`](LICENSE).
