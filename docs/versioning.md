# Versioning policy

`gotime` uses **calendar-anchored semantic versions** of the form
`YYYY.MINOR.MICRO`, derived **from git tags** at build time by
[`hatch-vcs`](https://github.com/ofek/hatch-vcs). Versions are never written
by hand.

```
2026 . 1 . 0
 │     │   │
 │     │   └─ MICRO: bug fixes, docs, dependency bumps
 │     └───── MINOR: new providers, new endpoints, new CLI commands
 └─────────── YEAR: the year the release is cut in
```

The year rolls forward the first time a release is cut on or after January 1st;
`MINOR` resets to `0` at the same time. The scheme is
[PEP 440](https://peps.python.org/pep-0440/)-compliant (`2026.1.0` is a valid
public version identifier), which means pip, PyPI, and the
`packaging.version.Version` comparators all order it correctly.

## Why CalVer + SemVer?

- The year gives users a very fast "is my install fresh?" check.
- `MINOR` still carries traditional "additive but compatible" semantics.
- `MICRO` still carries "no behavior change" semantics.

## How versions are computed (no manual edits)

`pyproject.toml` declares the version as dynamic:

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"
fallback-version = "0.0.0+dev"

[tool.hatch.build.hooks.vcs]
version-file = "src/gotime/_version.py"
```

At build time (`python -m build`, `pip install .`, `pip install --editable .`,
`uv pip install --editable .`, or the release workflow) `hatch-vcs`:

1. Picks up the closest tag matching `YYYY.MINOR.MICRO`.
2. If `HEAD` is the tagged commit, the version is exactly `YYYY.MINOR.MICRO`.
3. If `HEAD` is ahead of the tag, `hatch-vcs` appends a PEP 440
   post/dev segment (e.g. `2026.1.0.dev4+gabc1234`) so every build is
   still uniquely identifiable and installable.
4. The generated `src/gotime/_version.py` is what `gotime/__init__.py`
   imports to expose `gotime.__version__`.

There is **no** `__version__ = "..."` string to bump by hand, and there is
**no** `version = "X.Y.Z"` field in `pyproject.toml`. `src/gotime/_version.py`
is gitignored — it appears locally the first time you build or install the
package and is regenerated on every subsequent build.

## Pre-releases

Pre-releases use PEP 440 suffixes in increasing order of maturity:

- `2026.2.0a1` — alpha
- `2026.2.0b1` — beta
- `2026.2.0rc1` — release candidate

`pip install gotime` will **not** pick up pre-releases unless the user passes
`--pre`. Tag and publish them exactly like stable releases — the release
workflow's tag filter accepts the suffix.

Between tags, `hatch-vcs` automatically emits a PEP 440 dev suffix
(`2026.1.0.dev4+gabc1234`). These builds are installable locally but are
**never** uploaded to PyPI.

## Dealing with broken releases

Once a tag is pushed, the tag itself is immutable. Recovery paths, in order of
preference:

| Scenario                           | Action                                                   |
| ---------------------------------- | -------------------------------------------------------- |
| Release notes wrong                | Edit the GitHub Release body (post-publish editable).    |
| Install broken / regression        | Cut a new `MICRO` with the fix or revert.                |
| Must hide the release from new installs | Yank the PyPI release (pinned installs keep working). |
| Security issue                     | Yank **and** cut a replacement `MICRO` with an advisory. |

Yanked releases stay on PyPI (so pinned consumers still resolve them) but are
excluded from `pip install gotime` without an explicit version pin.

Full rollback procedure is in [`release.md`](release.md).

## Supported Python versions

`gotime` supports the two most recent stable CPython minor versions. The
canonical source of truth is the `Programming Language :: Python :: X.Y`
classifiers in `pyproject.toml`. Dropping a Python version is a `MINOR` bump,
never a `MICRO`.

## Procedure

The authoritative release runbook lives in [`release.md`](release.md).
