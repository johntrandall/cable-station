# Build lead's report: 0.1.3 ready for verification

**Start here.** The lead designer of cable-station built 0.1.3 on `build/0.1.3` (worktree `../cable-station-0.1.3`) and reports it ready for the cold verifier. Brief: `briefs/cycle.md`; verifier's brief: `briefs/verifier.md`.

- One change commit (tape guard, dropout watch, release script, tests, docs, version). Suite: 43 passed.
- Readings the builder took: the repeat guard is 10 s (John: 60 s too long); auto mode holds rather than asks on any guard; a dropout is a partner up 60 s or more, so cable swaps at the bench stay quiet.
- `scripts/release.sh --check` refuses on the branch by design; it is run on main after the landing, then the full release installs 0.1.3 (John, 19:17: "deploy after testing").
