# Build lead's report: 0.1.2 ready for verification

**Start here.** The lead designer of cable-station built release 0.1.2 on the branch `build/0.1.2` (worktree `../cable-station-0.1.2`) and reports it ready for the cold verifier. The brief with John's words and the gate is `briefs/cycle.md`; the verifier's brief is `briefs/verifier.md`.

- Change commit: 3cc35d9 (settle gate on every Mac reading, auto mode, footer tooltips, no hedge on labels); briefs: bc74c69.
- Suite at the change commit: `uv run pytest -q` → 40 passed.
- Screens looked at by the builder: `screens/settling-auto-on.png` (mode bar with AUTO ON, SETTLING countdown, short footer with no mode keys). A hover screenshot did not capture the tooltip overlay; the tooltip is set on each `Binding` and checked by `test_footer_names_are_short_with_tooltips_and_no_mode_keys`.
- Reading the builder took that the brief left open: auto mode holds a power-only verdict and the CORRECTION? case for `Enter`; tester mode never auto-prints. A card candidate if John wants auto to print power-only too.
- Not in this build: the Homebrew formula (`Formula/`) still points at 0.1.1; it follows the release, not the landing.
