# Contributing to gotime

Thanks for considering a contribution!

## Quick start

```bash
git clone https://github.com/mgeiger/gotime.git
cd gotime
uv venv --python 3.13
source .venv/bin/activate
uv pip install --editable ".[dev]"
```

At this point `gotime --version` prints a development version derived from
`hatch-vcs` (e.g. `2026.1.0.dev4+gabc1234`). That's expected — do not try to
"fix" it by editing `src/gotime/_version.py`; the file is regenerated on
every build and is gitignored.

## Before you push

All of these are enforced by CI. Running them locally will save you a round
trip — see also the `### Running CI locally` section in the README for tiers
of fidelity (including `act` for running the raw workflows).

```bash
black --check src tests
ruff check src tests
mypy
pytest                                            # >=90% line coverage
sphinx-build -W -b html docs docs/_build/html
```

## CHANGELOG

Every user-visible change must come with a `CHANGELOG.md` entry under
`## [Unreleased]`, using
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) subsection headings:

- `### Added` — new features.
- `### Changed` — behavior changes that aren't breaking.
- `### Deprecated` — soon-to-be-removed features.
- `### Removed` — features removed in this release.
- `### Fixed` — bug fixes.
- `### Security` — vulnerability fixes.

The `changelog` CI job fails on PRs that touch `src/gotime/`, `alembic/`, or
`pyproject.toml` without updating `CHANGELOG.md`. Pure documentation or
tooling-only changes can apply the `skip-changelog` label to bypass the
check.

## Commit messages

- One topic per commit.
- Imperative mood in the subject: "add", "fix", "remove".
- Reference issues and PRs by number when relevant.

## Review

- Keep PRs small and scoped; large refactors are easier to land in pieces.
- Add tests for every new code path. Fix CI before requesting review.
- Once review is green, a maintainer will merge.

## Releasing

Don't edit `_version.py`, `pyproject.toml`'s `version` field (there isn't
one — it's dynamic), or tag yourself. The release runbook lives in
[`docs/release.md`](docs/release.md).

## Security

For security-sensitive reports, please open a private
[GitHub Security Advisory](https://github.com/mgeiger/gotime/security/advisories/new)
instead of a public issue.
