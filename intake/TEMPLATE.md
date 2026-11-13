---
type: intake
system: "cable-station"
project: ""                      # only where the system's intake is per project
event: "<what kind of thing this is: release | rename | correction | request | finding | proposal>"
date: YYYY-MM-DD
from: "<your system or project, and your $CLAUDE_SESSION_ID>"
commit: "<the commit, tag or URL this is about, if any>"
urgency: ""                      # "urgent" only when it is: blocked, breaking, or a deadline within about a day (D9 §3)
urgent_because: ""               # with urgency: urgent, "blocked: <why>", "breaking: <why>" or "deadline: <when and why>"
processed: null                  # the receiving seat writes: "YYYY-MM-DD: <what became of it>"
---

## What this is

One paragraph: what happened or what you are asking for, in plain terms, with links (repo, release, record). Facts the receiving system cannot find on its own come first.

## Why it is this system's

One or two sentences: which of the things this system takes in this is (see `watchbill systems list --intake`).

## Facts that make an existing record wrong

Bullets: the record (path or URL) and what is wrong now. You report it here; you do not change the record. Leave the heading when there is nothing.

## Proposed text or action (optional)

Exact words or steps you would take, under a heading naming where they go. The receiving seat treats them as proposals under its own rules; the human approves what needs approving.

## Out of scope / do not say

What you would rather the system did not promise, compare or repeat.
