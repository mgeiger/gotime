"""Version-parity tests for the gotime package.

These checks ensure that the ``__version__`` string exposed by
``gotime`` is exactly what ``importlib.metadata`` sees for the
installed distribution, that it is a valid PEP 440 identifier, and
that release builds conform to the ``YYYY.MINOR.MICRO`` shape
documented in ``docs/versioning.md``.
"""

from __future__ import annotations

import re
from importlib import metadata

import pytest

import gotime

DEV_MARKERS = ("dev", "+dev", "local", "a0")


def _is_release_like(version: str) -> bool:
    """Return True if ``version`` looks like a real tagged release.

    Development / unreleased builds produced by hatch-vcs include
    ``.devN`` or ``+g<sha>`` segments; CI and editable installs should
    still satisfy the installed-metadata check below but don't have to
    match the CalVer prefix.
    """

    return not any(marker in version for marker in DEV_MARKERS)


def test_version_string_exists() -> None:
    """The package must expose a non-empty ``__version__``."""

    assert isinstance(gotime.__version__, str)
    assert gotime.__version__


def test_version_matches_installed_metadata() -> None:
    """``gotime.__version__`` must equal the installed distribution version."""

    try:
        installed = metadata.version("gotime")
    except metadata.PackageNotFoundError:
        pytest.skip("gotime is not installed as a distribution in this environment")

    assert gotime.__version__ == installed, (
        f"gotime.__version__={gotime.__version__!r} disagrees with "
        f"importlib.metadata.version('gotime')={installed!r}"
    )


def test_version_is_pep440() -> None:
    """The version must be a parseable PEP 440 public identifier.

    We rely on ``packaging`` if available (it's a transitive dep of
    most of our tooling); otherwise fall back to a permissive regex
    that still rules out obviously broken strings.
    """

    try:
        from packaging.version import InvalidVersion, Version
    except ImportError:  # pragma: no cover
        pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+!-]*$")
        assert pattern.match(gotime.__version__), f"not PEP 440-ish: {gotime.__version__!r}"
        return

    try:
        Version(gotime.__version__)
    except InvalidVersion as exc:
        raise AssertionError(f"gotime.__version__={gotime.__version__!r} is not PEP 440: {exc}") from exc


def test_release_versions_match_calver_shape() -> None:
    """Tagged releases must match ``YYYY.MINOR.MICRO``.

    Dev builds (``0.0.0+dev``, ``YYYY.MINOR.MICRO.devN+g<sha>``) are
    allowed to skip this check so that fresh checkouts don't fail CI.
    """

    version = gotime.__version__
    if not _is_release_like(version):
        pytest.skip(f"{version!r} looks like a dev build; CalVer shape check skipped")

    calver = re.compile(r"^\d{4}\.\d+\.\d+([abrc]\d+)?$")
    assert calver.match(version), f"Tagged release {version!r} must match YYYY.MINOR.MICRO (see docs/versioning.md)"
