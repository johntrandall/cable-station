# Verifier brief: build 0.1.2 of cable-station

**Start here.** You are a cold verifier (`watchbill:verifier`) for the cable-station system, a Python Textual app in this repository that reads USB-C cables on a Mac and prints their flags on a P-touch printer. You did not build this change. Check it against its brief and report pass or fail per check with script evidence; then write two things on the build branch: `gui-verdict.md` in this run folder and one trailer-only commit. Write nothing else.

## What to read

- The brief: `dev-docs/runs/build-2026-11-13-0.1.2/briefs/cycle.md` (John's words and the gate).
- The change: `git diff main...build/0.1.2` (three dots). Work in the worktree `/Users/johnrandall/dev/cable-station-0.1.2` (branch `build/0.1.2`), never in the primary checkout `/Users/johnrandall/dev/cable-station`.

## Checks (each with the command and its output in your report)

1. `cd /Users/johnrandall/dev/cable-station-0.1.2 && uv run pytest -q`: every test passes.
2. `grep -rn "confirm the drive" src tests` prints nothing.
3. Read `station.py`: `action_print_new` and `action_write_into` refuse a pending reading whose `settled` is False; `mac_watch` stages a reading provisionally and reports it settled only after `SETTLE_S`; `auto_print` holds a `PWR ONLY` verdict and never runs in tester mode (`source` must be `mac` or `lightning`).
4. Footer: `BINDINGS` shows exactly enter, a, r, n, w, x, s, q; each shown binding has a tooltip; 1 to 4 have `show=False`.
5. GUI: look at `dev-docs/runs/build-2026-11-13-0.1.2/screens/settling-auto-on.png` (read the image). It must show the mode bar with `AUTO ON`, a yellow SETTLING line with a countdown, a pending `new?` row, and a footer with short names and no mode keys. If you can, also render it yourself: the script pattern is in `tests/test_station.py` (`CableStation(...).run_test()` then `app.save_screenshot(...)`).
6. README and CHANGELOG describe the settle gate, auto mode and the footer; version is 0.1.2 in `pyproject.toml` and `src/cable_station/__init__.py`.

## What you write

1. `dev-docs/runs/build-2026-11-13-0.1.2/gui-verdict.md` on the branch, with frontmatter `verdict: pass` or `verdict: fail`, `sha: <the branch tip you checked>`, `looked_at: the station's main screen with auto mode on and a settling reading (screens/settling-auto-on.png), rendered by Textual's run_test`, `screenshot: dev-docs/runs/build-2026-11-13-0.1.2/screens/settling-auto-on.png`, and one paragraph of what you saw.
2. Your report at `dev-docs/runs/build-2026-11-13-0.1.2/verifier-report.md` on the branch: one line per check, pass or fail, the command and the evidence.
3. Commit both on `build/0.1.2` with `git commit` in the worktree (message: `verifier: build 0.1.2 report and GUI verdict`), then one trailer-only commit: `git commit --allow-empty -m "verifier: build 0.1.2 verified" --trailer "Watchbill-Event: verified" --trailer "Watchbill-Rule: <sha of the commit you just made>"`. On a fail, use `Watchbill-Event: verify-failed` instead and say in the report what failed.

Do not touch `main`, the primary checkout, or any file outside this run folder. Your session id is your own; that is why you, not the lead designer, make the verified commit.
