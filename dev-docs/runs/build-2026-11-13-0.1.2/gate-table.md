# Gate table: build 0.1.2

**Start here.** The gate of build run `build-2026-11-13-0.1.2` (brief: `briefs/cycle.md`), one line per criterion with its evidence. The build landed on main as 7da3947 through `watchbill land`, which ran the suite on the trial merge in its own worktree.

| # | Criterion | Evidence |
|---|---|---|
| 1 | Suite passes on the merged result | `watchbill land` gate on 7da3947: green (the landing printed `landed`); verifier round 1 at 61f9c57: `40 passed in 12.63s` (`verifier-report.md`); round 2 at 9fa1619: pass (`verifier-report-2.md`) |
| 2 | No hedge text in the code | `grep -rn "confirm the drive" src tests` empty (both verifier reports, check 2) |
| 3 | A provisional reading cannot be added or printed | `test_a_provisional_reading_shows_but_cannot_be_added_or_printed` in the 40 passed; the round-1 verifier also pressed Enter while settling in its own render: 0 rows written (`gui-verdict.md`) |
| 4 | Auto mode adds and prints a settled reading, holds power-only | `test_auto_mode_adds_and_prints_a_settled_reading_but_holds_power_only` in the 40 passed |
| 5 | Footer: enter, a, r, n, w, x, s, q with tooltips; no mode keys | `test_footer_names_are_short_with_tooltips_and_no_mode_keys`; FooterKey tooltips read back by the builder (nine keys, each with its text) |
| 6 | GUI looked at | `gui-verdict.md`: verdict pass at 61f9c57 by the round-1 verifier, who also rendered the state itself; `screens/settling-auto-on.png` |

Verified commits on the branch: 6950bf9 (round 1, session 03c7… verify-0-1-2) and 2a6904c (round 2, session 57669ab9 cables-member-verify2). Approval: John's words in `run-record.md` (2026-11-13 09:31 and 09:37, chat).

Not covered by this gate: a live print on the P-touch under auto mode (needs John at the station); the Homebrew formula still points at 0.1.1 until the release.

harvest: two findings already filed with watchbill (intake note b24e2d1c5: the ledger line refused by the quote hook; a verifier leaving its files uncommitted); a third from round 2: the daemon refused to respawn because the first verifier's address `verify-0-1-2` stayed registered as live after it exited, so the fallback spawner was needed.
