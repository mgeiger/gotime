#!/usr/bin/env bash
# Usage: scripts/prepare-release.sh 2026.1.0
#
# Opens a PR that flips `## [Unreleased]` to `## [<version>] - <today>` and
# updates the link references. That PR is the only manual edit of
# CHANGELOG.md required for a release.
set -euo pipefail

version="${1:?usage: $(basename "$0") <version>}"

if ! [[ "${version}" =~ ^[0-9]{4}\.[0-9]+\.[0-9]+(a[0-9]+|b[0-9]+|rc[0-9]+)?$ ]]; then
    echo "error: version '${version}' does not match YYYY.MINOR.MICRO[(a|b|rc)N]" >&2
    exit 1
fi

if ! git diff --quiet --exit-code; then
    echo "error: working tree not clean" >&2
    exit 1
fi
if ! git diff --cached --quiet --exit-code; then
    echo "error: staged changes present" >&2
    exit 1
fi

current_branch=$(git branch --show-current)
if [[ "${current_branch}" != "main" ]]; then
    echo "error: must run from 'main' (currently on '${current_branch}')" >&2
    exit 1
fi

git pull --ff-only origin main

if ! awk '/^## \[Unreleased\]/{flag=1; next} /^## \[/{flag=0} flag && NF' CHANGELOG.md | grep --quiet '.'; then
    echo "error: ## [Unreleased] section is empty - nothing to release" >&2
    exit 1
fi

today=$(date --utc +%Y-%m-%d)
branch="release/bump-${version}"
git checkout -b "${branch}"

python - "${version}" "${today}" <<'PY'
import pathlib
import re
import sys

version, today = sys.argv[1], sys.argv[2]
path = pathlib.Path("CHANGELOG.md")
text = path.read_text(encoding="utf-8")

text = re.sub(
    r"^## \[Unreleased\][^\n]*\n",
    f"## [Unreleased]\n\n## [{version}] - {today}\n",
    text,
    count=1,
    flags=re.MULTILINE,
)

repo = "https://github.com/mgeiger/gotime"
text = re.sub(
    r"^\[Unreleased\]:.*$",
    f"[Unreleased]: {repo}/compare/{version}...HEAD",
    text,
    count=1,
    flags=re.MULTILINE,
)
if f"[{version}]:" not in text:
    text = text.rstrip() + f"\n[{version}]: {repo}/releases/tag/{version}\n"

path.write_text(text, encoding="utf-8")
PY

git add CHANGELOG.md
git commit --message "chore(release): ${version}"
git push --set-upstream origin "${branch}"
gh pr create --base main --fill --title "chore(release): ${version}"

cat <<DONE

Release PR opened. After merging:

  git checkout main && git pull --ff-only origin main
  git tag --annotate --sign ${version} --message 'Release ${version}'
  git push origin ${version}

Then approve the 'pypi' environment deployment in the GitHub Actions UI.
DONE
