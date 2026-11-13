# Verifier brief, second round: build 0.1.2 of cable-station

**Start here.** You are a cold verifier (`watchbill:verifier`) for cable-station. Read and follow `dev-docs/runs/build-2026-11-13-0.1.2/briefs/verifier.md` in this worktree (`/Users/johnrandall/dev/cable-station-0.1.2`, branch `build/0.1.2`); this page only says what changed since the first verifier.

- The first verifier passed at 61f9c57 (its report and GUI verdict are committed: `verifier-report.md`, `gui-verdict.md`). Since then only run-folder documents changed: the brief cites tests by name (ddb41af), the two verifier files were committed (edad103), the report gained a second-round note (0988a6c, 933eed5), and this page. `git diff 61f9c57..HEAD --stat` shows it; no file under `src/` or `tests/` changed.
- Do the checks of the first brief again on the current tip (the suite, the grep, the code reading, the footer, the README and CHANGELOG), and read the committed `gui-verdict.md` against `screens/settling-auto-on.png` (open the image); render it yourself if you doubt it.
- Write your report as `verifier-report-2.md` in the run folder, and update `gui-verdict.md` only if you disagree with it (then set its `sha:` to the tip you looked at).
- **Commit what you write first** (`git add` the files, `git commit`), then the trailer-only commit: `git commit --allow-empty -m "verifier: build 0.1.2 verified (round 2)" --trailer "Watchbill-Event: verified" --trailer "Watchbill-Rule: <sha of the commit you just made>"`. The landing refuses a branch whose tip is not that trailer commit by a session other than the builder's, and refuses files cited but not in the repository, which is why the order matters. On a fail: `Watchbill-Event: verify-failed`, and say what failed in the report.

Touch nothing in `/Users/johnrandall/dev/cable-station` (the primary checkout) and nothing outside this run folder.
