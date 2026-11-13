# Build 0.1.2: settle gate, auto mode, footer tooltips

**Start here.** This is the brief of build run `build-2026-11-13-0.1.2` of the cable-station system (the Textual station that reads USB-C cables and prints their flags). It records what John asked for, what was built, and the gate that decides whether it lands. The lead designer (cable-station-lead-designer, session d8571e81) built it alone on the branch `build/0.1.2` in the worktree `../cable-station-0.1.2`; a cold verifier checks it before the landing.

## John's request (verbatim, in chat, this session; times in the run record)

- 09:31, on the label he had just printed: "why is the label I just printed say "confirm the drive is on the far end". This should never go on a label. Also, should database additions or lable printing be blocked until we are sure the usb exploration has settled?"
- 09:37: "there should be an "auto-add and print" mode that wait for settle, adds and prints. human only touches the labels and the cables. toggleable."
- A message that arrived mid-turn after that (its exact time is not in the transcript tool's reach; it is quoted as written in the run record): "rollovers should explain each menu item (which can allow for shorter names on the bottom. Also, we have duplicate modes on the bottom menu. if they appear on the top they don't need to be there."

## What was built (one commit on the branch, 3cc35d9)

1. **Settle gate.** Every Mac-path reading (drive and dock modes) is staged at once marked SETTLING with a countdown and cannot be added to the database or printed until the port has held one signature (devices, link, e-marker VDOs) for `SETTLE_S` = 8 s; a new signature restarts the clock. `Enter` and `w` are refused meanwhile. This replaces 0.1.1's no-link-only wait (`no_link_wait`, `NO_LINK_SETTLE_S`).
2. **No hedge on labels.** `label_note` for the chipless no-link verdict is empty; the question "is the far end plugged in?" goes to the status line. The label reads `PWR ONLY · no data`.
3. **Auto mode** (`a`, shown in the mode bar as AUTO ON or AUTO off). On, a settled reading in drive, dock or lightning mode is added and printed with no key. Two cases still wait for the human: a power-only verdict (the Mac cannot tell a dead cable from a far end not yet plugged in), and the CORRECTION? case (the port changed its reading within 2 minutes of a print from it). Tester mode is unchanged: readings there need `Enter`.
4. **Footer.** Short names, a tooltip per key on hover, the mode keys 1 to 4 shown in the mode bar only.
5. README (keys table, settling paragraph), CHANGELOG 0.1.2, version 0.1.2 in `pyproject.toml`, `__init__.py` and `uv.lock`.

Files: `src/cable_station/station.py`, `src/cable_station/__init__.py`, `tests/test_station.py`, `tests/test_cli_and_config.py`, `README.md`, `CHANGELOG.md`, `pyproject.toml`, `uv.lock`, and this run folder.

## The gate

Done means every line below holds, with script evidence in `gate-table.md`:

1. `uv run pytest -q` on the merged result: all tests pass (40 at the ready commit).
2. `grep -rn "confirm the drive" src tests` finds nothing: the hedge is gone from the code.
3. A provisional reading (settled False) cannot be added or printed: the test `test_a_provisional_reading_shows_but_cannot_be_added_or_printed` in `tests/test_station.py`.
4. Auto mode adds and prints a settled reading and holds a power-only one: the test `test_auto_mode_adds_and_prints_a_settled_reading_but_holds_power_only` in `tests/test_station.py`.
5. The footer shows exactly the keys enter, a, r, n, w, x, s, q, each with a tooltip, none of the mode keys: the test `test_footer_names_are_short_with_tooltips_and_no_mode_keys` in `tests/test_station.py`.
6. GUI looked at: `screens/settling-auto-on.png` (mode bar with AUTO ON, SETTLING line, footer) and a verdict in `gui-verdict.md` by the cold verifier.

`gui: review`. `security: none` (no trust boundary is crossed: no network, no token, no listener).

Rename gate and design pin: this system has no design set, no rename map and no mocks (dev-docs holds boards and runs only), so the rename gate and the design pin have nothing to check; recorded here rather than run.
