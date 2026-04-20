"""Extract a single release section from CHANGELOG.md.

Usage:
    python .github/scripts/extract_changelog.py <version>

The script locates ``## [<version>]`` in ``CHANGELOG.md`` (relative to the
current working directory), prints everything up to the next ``## [`` header
to stdout, and exits non-zero if the section is missing or empty. The
release workflow feeds the output to ``softprops/action-gh-release`` so the
GitHub Release body, the PyPI page, and the repo changelog never drift.
"""

from __future__ import annotations

import pathlib
import re
import sys


def extract(version: str, text: str) -> str:
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"No section '## [{version}]' found in CHANGELOG.md")
    body = match.group(1).strip()
    if not body:
        raise SystemExit(f"Section '## [{version}]' is empty in CHANGELOG.md")
    return body


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: extract_changelog.py <version>")
    changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
    print(extract(sys.argv[1], changelog))


if __name__ == "__main__":
    main()
