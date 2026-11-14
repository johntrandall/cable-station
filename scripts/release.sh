#!/usr/bin/env bash
# Release cable-station from a clean main: version check, suite, tag, push, reinstall the uv tool copy.
# Usage: scripts/release.sh [--check]   (--check: the checks only, nothing pushed or installed)
# John, 2026-11-13, in chat: "you should auto-install when you make a change." / "or have a release script/process or soemthing"
set -euo pipefail
cd "$(dirname "$0")/.."
check_only=0; [ "${1:-}" = "--check" ] && check_only=1

version=$(sed -nE 's/^version = "([^"]+)"/\1/p' pyproject.toml | head -1)
init_version=$(sed -nE 's/^__version__ = "([^"]+)"/\1/p' src/cable_station/__init__.py)
changelog_version=$(sed -nE 's/^## ([0-9][^ ]*) .*/\1/p' CHANGELOG.md | head -1)
[ -n "$version" ] || { echo "release: no version in pyproject.toml" >&2; exit 2; }
[ "$version" = "$init_version" ] || { echo "release: pyproject $version but __init__ $init_version" >&2; exit 2; }
[ "$version" = "$changelog_version" ] || { echo "release: pyproject $version but CHANGELOG's top entry is $changelog_version" >&2; exit 2; }
branch=$(git rev-parse --abbrev-ref HEAD)
[ "$branch" = "main" ] || { echo "release: on $branch, not main" >&2; exit 2; }
[ -z "$(git status --porcelain)" ] || { echo "release: the tree is not clean" >&2; git status --short >&2; exit 2; }
echo "release: $version on main at $(git rev-parse --short HEAD)"
uv run pytest -q
[ "$check_only" = 1 ] && { echo "release: checks pass (--check: nothing tagged, pushed or installed)"; exit 0; }

tag="v$version"
if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
  echo "release: tag $tag exists at $(git rev-parse --short "$tag")"
else
  git tag -a "$tag" -m "$version"
  echo "release: tagged $tag"
fi
git push origin main "$tag"
uv tool install --reinstall --force . >/dev/null
installed=$(cable-station --version)
echo "release: installed: $installed"
[ "$installed" = "cable-station $version" ] || { echo "release: installed copy is not $version" >&2; exit 3; }
echo "release: done. The Homebrew formula under Formula/ is a draft outside the tap; not part of this release."
