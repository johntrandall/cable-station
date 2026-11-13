# Verifier report: build 0.1.2 of cable-station

Tip checked: 61f9c57d842759f055754f428a7bec79be406777 (branch build/0.1.2, worktree /Users/johnrandall/dev/cable-station-0.1.2, tree clean at start). Verdict: **PASS on all six checks.**

1. **PASS.** `uv run pytest -q` printed `40 passed in 12.63s`.
2. **PASS.** `grep -rn "confirm the drive" src tests` printed nothing (exit 1). The phrase remains only in CHANGELOG.md, as the description of the removed hedge.
3. **PASS** (read in `git diff main...build/0.1.2 -- src/cable_station/station.py`).
   - `action_print_new` returns with a status message when `pending[0].get("settled", True)` is false, before `next_id` or any write.
   - `action_write_into` has the same refusal.
   - `mac_watch` stages a first-seen signature with `reading_from_port(p, False)`; `settle_left` is `ceil(SETTLE_S - (now - first))`, so the reading is staged settled (`mac_seen = (sig, True)`, `reading_from_port(p, True)`) only once `SETTLE_S` (8) has passed on one unchanged signature; a new signature has its own timer key.
   - `auto_print` returns unless auto is on, the reading is settled, and `source` is `mac` or `lightning` (tester readings have another source, so tester mode never auto-prints); it holds a `PWR ONLY` verdict with a status message. The CORRECTION? branch returns before `auto_print` is called, so it waits too.
   - Tests: test_a_provisional_reading_shows_but_cannot_be_added_or_printed and test_auto_mode_adds_and_prints_a_settled_reading_but_holds_power_only are in the 40 that passed.
4. **PASS.** A script over `CableStation.BINDINGS` printed the shown bindings `enter print, a auto, r reprint, n no chip, w update, x retire, s discard, q quit`, each with a tooltip (all True), and keys 1 to 4 each `show=False`; it asserted exactly that order and printed OK. c, p, u and ctrl+c are also hidden.
5. **PASS.** Read screens/settling-auto-on.png: mode bar with AUTO ON (a), yellow SETTLING line with a 5 s countdown, pending `new? (#1)` row, footer with short names and no mode keys. I rendered it myself with a script in the session scratchpad (App.run_test, then export_screenshot, then headless Chrome to PNG) and the render matches. Enter while settling left the store empty (0 rows). Details in gui-verdict.md.
6. **PASS.** `pyproject.toml` `version = "0.1.2"`; `__init__.py` `__version__ = "0.1.2"`; `uv.lock` cable-station `version = "0.1.2"`. README: Enter row, a row, mode-key note, footer sentence, and a "Settling" paragraph. CHANGELOG 0.1.2 has four bullets (settle gate, hedge removed, auto mode, footer).

## Outside my brief
- Where I deviated from the brief: it says to commit the report and verdict. My own rule (0.10.95) says my report never goes in a commit of mine, so **gui-verdict.md and verifier-report.md are uncommitted files in the run folder for the lead designer to commit.** My only commit is the trailer-only one, whose Watchbill-Rule is the tip I checked (61f9c57d842759f055754f428a7bec79be406777), not a commit of the report.
- Observation, not a failure: in lightning mode there is no settle gate (lightning readings carry no `settled` key, so they count as settled at once), as the brief's design says (the gate is for Mac-path drive and dock readings; auto mode covers lightning).
