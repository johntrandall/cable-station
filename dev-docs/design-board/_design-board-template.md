---
_human_verdict:           # the lane, first so the human finds it: his (`yes, show me`, `yes, just do it`, no, revise proposal, revise card, snoozed, later, after POC, after MVP, talk; he may set it here or drag the card) or the agent's (documents to review, new decisions, returning decisions, agents drafting, agent working, agent waiting, agent scheduled, processed), moved only by `watchbill decide`
title: ""                 # short, at most 60 characters (about eight words): a noun phrase or a short question naming the decision, never its options; the H1 repeats it
type: decision
kind: decision            # decision | approval
attention_weight: quick   # quick or big (0.10.102: the key was weight): a big card (a document review, a design or ADR approval) is presented in `documents to review`
asks:                     # approval: the card asks him to approve its subject document as a whole (his yes writes the approval record on it); blank: a yes answers the question and approves no document (0.10.58)
system: "cable-station"       # registry name
question: ""              # one line: the card's title; one decision per card (split a question with independent parts)
options: []               # closed choices, short labels: each becomes a lane on the board; empty for yes/no
recommendation: ""        # one option, or yes/no; reasoning in the body
unblocks: ""              # item id, task, cycle
asked_by: ""              # seat name
asked_at: ""              # 2026-10-19T12:40:00-04:00
asked_via: chat           # chat | ask-user-question | board | track-changes
status: open              # draft | open | provisional | answered | applied | withdrawn
applied_at: ""
applied_how: ""           # what was applied: a design change, a landing SHA, a configuration line
undo: ""                  # provisional only: how to undo what was rolled forward
source: ""                # chat | board | relay
recorded_where: ""
relayed_by: ""
spawned: ""               # ADR-NNNN when the answer set a rule
subject: ""               # the files the card is about, relative to the home (comma-separated)
subject_fingerprint: ""   # written by `watchbill decide`; `--reopen` refuses while it is unchanged
human_note:               # the human's field
human_words:              # verbatim; written only by `watchbill decide --answered-in-chat`
snooze_until:             # the human's: on a snoozed card, the date it comes back (returning) through `watchbill decisions sweep`
previous_verdict:         # the human's verdict, kept when an agent moves the card into its lanes
moved_at:
moved_by:
working_by:               # with the agent working lane: the agent on the card right now (`--move "agent working" --by NAME`); cleared when it leaves
waiting_on:               # with the waiting lane
revisit_when:             # with the scheduled lane: a date (ISO) or a condition
revisit_of:               # a revisit card: the card it revisits
revisits: []              # the original: its revisit cards
review_marks: []          # a Track Changes review card: the suggestions it waits on (`decide --await-review`); the sweep script answers the card from what the human does in the document
---
# [fill in: the title, at most 60 characters]

> [!todo] Your move · [the system] · [the seat]
> Written by `watchbill decide` from the card's fields on every write (what he is looking at, the exact action, what happens next); never edited by hand.

## The question

[fill in: one plain question, phrased so that yes accepts the recommendation; no double negatives]

- **Problem:** [fill in: the problem this solves: why he might want it, in a sentence]
- **Proposal:** [fill in: what the card proposes, in a sentence: the recommendation as a change]
- **From:** [fill in: where the question comes from (his words with the time and the channel, a card, a report), with its link; or delete this line when the card cites no source]

## Why this is being asked

**Start here.** [fill in: what this is about, for a reader coming to it cold a month from now, and what waits on the answer; how it arose goes in History]

**Terms.**
- [fill in: every term, id, acronym, seat name and file this card uses, defined before it is used]

## Design impact

[fill in: for each document, tool or seat the answer changes: its link, what it says or does today, what it will say or do after a yes; or `No design change:` and the reason]

[fill in, when the card proposes or changes a field, switch, flag or setting: a section here laying each out, for example:]

**`the_field`**
  - *What it is:* [fill in]
  - *Values:*
    - `value_a`: [fill in: what it does, what it allows, when to use it]
    - `value_b`: [fill in]
  - *Who reads it:* [fill in]
  - *Default:* [fill in]

[fill in, when the card asks about a changed diagram (a C4 view, a workflow, any approved picture): the review render with the changes since the last approval colour-coded (added, changed, removed) and its legend, the change table, a link to a viewer showing it in context (for C4: the model's `workspace.html`), and the clean render as it would be approved]

**Binds:** [fill in: the seats whose behaviour changes] · **Your part:** [fill in: what he does after a yes, blocking or queued; or nothing new; when it changes a gate or a field, the steward's records step comes before the landing] · **Does not change:** [fill in: what a reader might assume changes]

## Unknowns

- (none: a fact the decision depends on that nobody has checked is added with `watchbill decide --unknown CARD WHAT --test TEXT --cheap|--expensive --why TEXT`; a cheap test is run before the card reaches the human and filled with `decide --result CARD U1 TEXT --mark Verified|Observed|Inferred`; an expensive one is put to him first, why in the line)

## Options and consequences

Any number of options, combinations allowed; each labelled recommended, fallback, viable or not viable, with the reason. A simple yes/no card needs only yes and no.

- **yes** ([fill in: recommended, fallback, viable or not viable]): [fill in: what happens, what it costs, what undoing it would cost, and why it has that label]
- **no** ([fill in: label]): [fill in: what happens, what it costs, what undoing it would cost]

## Recommendation

**[fill in: one option, or yes/no; never a no: invert the question instead].** [fill in: its strength, strong, moderate or weak, and why in one clause: the evidence's mark (Verified, Observed or Inferred), how close the alternatives are, or whether the human's preference rather than the facts should decide.] [fill in: the reason, in a sentence or two; what the seat does on a yes]

## History

[fill in: how the question arose, at most five lines: the human's words verbatim with the time and the channel; earlier rounds; who was consulted]

## Links

- [fill in: every document that bears on it, each labelled with what it is]

## The human's words

## Talk to the agent

## Card log

One line per edit: when, who (name, role, session), what.

## John's comments

Type under the last *John* heading, or answer in chat; drag the card to **revise** when you want the agent to act on what you wrote.

### John
