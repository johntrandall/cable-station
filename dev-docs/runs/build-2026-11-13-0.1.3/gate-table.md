# Gate table: build 0.1.3

**Start here.** The gate of build run `build-2026-11-13-0.1.3` (brief: `briefs/cycle.md`), one line per criterion with its evidence. The build landed on main as 031721b through `watchbill land` (suite green on the trial merge) and was released with `scripts/release.sh` (tag `v0.1.3`, pushed, installed).

| # | Criterion | Evidence |
|---|---|---|
| 1 | Suite green on the merged result | `watchbill land` gate on 031721b: landed; `scripts/release.sh` on main re-ran it: 43 passed |
| 2 | Tape guard | `test_print_guard_holds_a_repeat_and_a_burst`, `test_a_held_print_needs_a_second_press_and_auto_never_overrides` in the 43; verifier round 1 (`verifier-report.md`) read every print path; its note on `w` led to the corrected claim (5932442) |
| 3 | Dropouts | `test_a_dropout_is_written_into_the_printed_cable_and_a_swap_is_only_logged`; verifier round 2 (`verifier-report-2.md`) re-read `watch_partner` and `port_gone` |
| 4 | `scripts/release.sh --check` passes on main | the full run after the landing: checks, suite, tag `v0.1.3`, push of main and the tag, `cable-station --version` → `cable-station 0.1.3` |
| 5 | GUI and security | no new screen (`gui: none`), no trust boundary (`security: none`) |

Verified commits on the branch: c3e8277 (round 1, verify-0-1-3 by the daemon) and 4ee4ea1 (round 2, cables-member-verify3, session 5b91cbcb). Approval: John, 2026-11-13 19:17, in chat (`dev-docs/watch.md`).

Not covered: a dropout seen on live hardware (the watch is tested with synthetic port states); the first real one will show in a cable's notes.

harvest: for watchbill, both verifiers again left their report uncommitted although the brief ordered the commit first (row 67's other half), and the engine's spawn name collided on a second ready report in 0.1.2; for ptouch-label, an idempotency guard (same image within a few seconds refused unless `--again`), filed as intake.
