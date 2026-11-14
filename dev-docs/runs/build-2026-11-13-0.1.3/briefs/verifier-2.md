# Verifier brief, round 2: build 0.1.3 of cable-station

**Start here.** You are a cold verifier (`watchbill:verifier`) for cable-station. Follow `dev-docs/runs/build-2026-11-13-0.1.3/briefs/verifier.md` in the worktree `/Users/johnrandall/dev/cable-station-0.1.3` (branch `build/0.1.3`); this page says what changed since round 1.

- Round 1 passed at fb7a9d6 (its report is committed: `verifier-report.md`) with one note: `w` is not behind the new print guard. The lead designer corrected the claim in `briefs/cycle.md`, `CHANGELOG.md` and `README.md` (no code change; `w` keeps its own two-press confirm). `git diff fb7a9d6..HEAD --stat` shows only those documents and the round-1 report.
- Re-run the round-1 checks on the current tip (the suite, the code reading, `scripts/release.sh --check`, the docs) and confirm the three corrected sentences match the code.
- Write `verifier-report-2.md` in the run folder, **commit it first** (`git add`, `git commit -m "verifier: build 0.1.3 report, round 2"`), then the trailer-only commit `git commit --allow-empty -m "verifier: build 0.1.3 verified (round 2)" --trailer "Watchbill-Event: verified" --trailer "Watchbill-Rule: <sha of the report commit>"`. The order matters: the landing refuses a cited file that is not in the repository and a tip that is not the verified commit. If a hook refuses your commit, put its exact message in your report and still make the trailer commit.

Touch nothing in `/Users/johnrandall/dev/cable-station` and nothing outside this run folder.
