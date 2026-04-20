#!/usr/bin/env bash
# Usage: scripts/rollback-release.sh 2026.1.0
#
# Interactive rollback walkthrough. Does NOT perform destructive actions on
# your behalf - PyPI yanking must happen in the web UI because OIDC Trusted
# Publishing deliberately does not grant yank permissions.
set -euo pipefail

version="${1:?usage: $(basename "$0") <version>}"

cat <<BANNER
================================================================================
Rolling back gotime ${version}

You are about to:
  1. Mark the GitHub Release ${version} as prerelease (de-emphasizes it on
     the repo landing page; does not delete it).
  2. Print the exact steps to yank the wheel and sdist on PyPI (manual).
  3. Suggest the follow-up: cut the next MICRO release with a revert commit
     and a CHANGELOG entry under "### Fixed" or "### Security".

Nothing is destructive yet. You'll be prompted before each step.
================================================================================
BANNER

read --prompt "Proceed? [y/N] " --silent --number 1 reply
echo
if [[ "${reply}" != "y" && "${reply}" != "Y" ]]; then
    echo "aborted."
    exit 0
fi

gh release edit "${version}" --prerelease

# Compute the suggested next version (bump MICRO).
if [[ "${version}" =~ ^([0-9]{4})\.([0-9]+)\.([0-9]+)$ ]]; then
    next_version="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.$((BASH_REMATCH[3] + 1))"
else
    next_version="<next MICRO>"
fi

cat <<PYPI

--- Yanking on PyPI (manual) ------------------------------------------------
  1. Open https://pypi.org/manage/project/gotime/release/${version}/
  2. Scroll to "Yank release".
  3. Provide a short reason (user-visible in pip output).
  4. Confirm.

  OIDC Trusted Publishing does NOT grant yank permissions, so this step has
  to be performed from a browser session authenticated as a project
  maintainer. No API token is created just for rollback.
-----------------------------------------------------------------------------

Next:
  scripts/prepare-release.sh ${next_version}
  # (after landing your revert / fix on main)
PYPI
