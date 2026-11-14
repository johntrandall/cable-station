# Build 0.1.3: tape guard, dropouts, release script

**Start here.** The brief of build run `build-2026-11-13-0.1.3` of cable-station (the Textual station that reads USB-C cables and prints their flags). The lead designer (cable-station-lead-designer, session d8571e81) builds it alone on `build/0.1.3` (worktree `../cable-station-0.1.3`); a cold verifier checks it before the landing; `scripts/release.sh` installs it after.

## John's request (chat, 2026-11-13; his words and times in `dev-docs/watch.md`)

- On a run of identical labels, he asked whether a debounce is needed and how to avoid burning tape; the station's log showed no repeated prints, so the guard is preventive.
- Mid-turn (quoted as written in watch.md): "you should auto-install when you make a change." and "or have a release script/process or soemthing".
- 19:17: "60s is too long, but yes, the dropout is a problem. Go, and push, and deploy after testing".

## What is built

1. **Tape guard** (`print_guard`, `print_allowed`, `note_print`): the same flag (text and id) within `REPEAT_GUARD_S` = 10 s, or `BURST_N` = 3 or more prints in `BURST_S` = 30 s, holds the print with the reason in the status line; a second press of the same key (`Enter`, `r`, `w`) prints anyway; auto mode never overrides. Auto mode also holds when the port reads the same label as the cable last printed from it.
2. **Dropouts** (`watch_partner`, `port_gone`): every port's partner is tracked; a partner gone within `DROPOUT_MIN_S` = 60 s of appearing is a swap (logged only); longer is a DROPOUT: a red main-box line, a status line, and a `DROPOUT <time>: <device> vanished after <n> s on port N` note on the cable last printed from that port (`port_printed`, cleared when a different label settles on the port).
3. **`scripts/release.sh`**: version consistency (pyproject, `__init__`, CHANGELOG top), clean main, suite, tag `v<version>`, push main and tag, `uv tool install --reinstall --force .`, and a check that `cable-station --version` is the released one. `--check` stops after the suite.
4. README (tape guard, dropouts, Releasing), CHANGELOG 0.1.3, version 0.1.3, `uv.lock`.

## The gate

1. `uv run pytest -q` green on the merged result (43 tests at the ready commit).
2. The guard: the test `test_print_guard_holds_a_repeat_and_a_burst` and `test_a_held_print_needs_a_second_press_and_auto_never_overrides` in `tests/test_station.py`.
3. Dropouts: the test `test_a_dropout_is_written_into_the_printed_cable_and_a_swap_is_only_logged` in `tests/test_station.py`.
4. `scripts/release.sh --check` on main passes after the landing (it refuses on a branch by design).
5. GUI: no new screen, only new text in the existing main box and status line (`gui: none`); `security: none` (no trust boundary).

Deploy: after the landing, `scripts/release.sh` on main; John's go for the deploy is the 19:17 line above ("deploy after testing").
