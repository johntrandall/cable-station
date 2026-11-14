# Verifier brief: build 0.1.3 of cable-station

**Start here.** You are a cold verifier (`watchbill:verifier`) for cable-station, a Python Textual app in this repository. You did not build this change. Work only in the worktree `/Users/johnrandall/dev/cable-station-0.1.3` (branch `build/0.1.3`), never in `/Users/johnrandall/dev/cable-station`. Read `dev-docs/runs/build-2026-11-13-0.1.3/briefs/cycle.md`, then `git diff main...build/0.1.3` (three dots).

## Checks (command and output in your report)

1. `uv run pytest -q`: all pass.
2. Read `station.py`: `print_allowed` is called before every print path (`action_print_new` second Enter, `action_reprint`, and the auto path through `action_print_new` with `_auto_printing`); `note_print` runs after every successful print; `auto_print` returns without printing when `print_allowed` holds or the port's last printed label matches.
3. `watch_partner` runs for every port on every poll (before the `_watched` test in `mac_watch`); `port_gone` writes the DROPOUT note only when `after >= DROPOUT_MIN_S` and a cable is recorded for that port.
4. `scripts/release.sh --check` from the worktree prints "on build/0.1.3, not main" and exits 2 (the branch refusal); read the script for anything that would push or install under `--check` (there must be nothing).
5. README and CHANGELOG describe the guard, dropouts and the release script; version 0.1.3 in `pyproject.toml` and `src/cable_station/__init__.py`.

## What you write, in this order

1. `dev-docs/runs/build-2026-11-13-0.1.3/verifier-report.md`: one line per check, pass or fail, with evidence.
2. **Commit it first**: `git add` that file and `git commit -m "verifier: build 0.1.3 report"`.
3. Then the trailer-only commit: `git commit --allow-empty -m "verifier: build 0.1.3 verified" --trailer "Watchbill-Event: verified" --trailer "Watchbill-Rule: <sha of the commit from step 2>"`. On a fail, `Watchbill-Event: verify-failed` and the reason in the report. The landing refuses a branch whose tip is not that trailer commit by a session other than the builder's, and refuses a cited file that is not in the repository, which is why step 2 comes before step 3.

Touch nothing else.
