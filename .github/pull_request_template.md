<!-- Thanks for contributing to gotime! -->

## Summary

<!-- What does this PR do and why? -->

## Changelog entry

<!--
Add your entry under `## [Unreleased]` in CHANGELOG.md using a
Keep-a-Changelog subsection header:

  ### Added      - new features
  ### Changed    - behavior changes that aren't breaking
  ### Deprecated - soon-to-be-removed features
  ### Removed    - features removed in this release
  ### Fixed      - bug fixes
  ### Security   - vulnerability fixes

If this PR is pure docs, CI, or tooling (i.e. ships no user-visible change),
apply the `skip-changelog` label instead of adding an entry.
-->

- [ ] I added an entry under `## [Unreleased]` in `CHANGELOG.md`, OR
- [ ] This PR carries the `skip-changelog` label because it ships no
      user-visible change.

## Test plan

<!-- Commands you ran, edge cases considered, screenshots for UI, etc. -->

- [ ] `pytest` passes locally (>=90% coverage).
- [ ] `black --check`, `ruff check`, `mypy` pass locally.
- [ ] `sphinx-build -W -b html docs docs/_build/html` passes locally
      (only if docs changed).
