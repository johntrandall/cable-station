---
kind: mdbase.type
name: decision
version: 1
match:
  path_glob: "dev-docs/design-board/*.md"
schema:
  dialect: json-schema-2020-12
  value:
    type: object
    additionalProperties: false
    patternProperties:  # 0.10.73: a system's own fields, x_ and lower case; watchbill's stay closed
      "^x_[a-z][a-z0-9_]*$": {}
    required: [type, kind, system, question, status, asked_by, asked_at]
    properties:
      type: { const: decision }
      kind: { enum: [decision, approval, discussion, cycle, task] }
      attention_weight: { enum: [quick, big, null] }
      weight: { enum: [quick, big, null] }  # 0.10.102: the old key of attention_weight, admitted for one release; the refresh renames it
      asks: { enum: [approval, null] }
      system: { type: string, minLength: 1 }
      title: { type: [string, "null"], maxLength: 60 }
      question: { type: string, minLength: 1 }
      options: { type: [array, "null"], items: { type: string } }
      recommendation: { type: [string, "null"] }
      unblocks: { type: [string, "null"] }
      asked_by: { type: string, minLength: 1 }
      asked_at: { type: string, minLength: 1 }
      asked_via: { enum: [chat, ask-user-question, board, track-changes] }
      status: { enum: [draft, open, provisional, answered, applied, withdrawn] }
      applied_at: { type: [string, "null"] }
      applied_how: { type: [string, "null"] }
      undo: { type: [string, "null"] }
      source: { type: [string, "null"] }
      recorded_where: { type: [string, "null"] }
      relayed_by: { type: [string, "null"] }
      spawned: { type: [string, "null"] }
      subject: { type: [string, "null"] }
      subject_fingerprint: { type: [string, "null"] }
      presented_hash: { type: [string, "null"] }
      _human_verdict: { type: [string, "null"] }
      human_verdict: { type: [string, "null"] }
      human_note: { type: [string, "null"] }
      human_words: { type: [string, "null"] }
      snooze_until: { type: [string, "null"] }
      previous_verdict: { type: [string, "null"] }
      moved_at: { type: [string, "null"] }
      moved_by: { type: [string, "null"] }
      working_by: { type: [string, "null"] }
      editing_from: { type: [string, "null"] }  # 0.10.67: the lane an agent editing card goes back to
      waiting_on: { type: [string, "null"] }
      revisit_when: { type: [string, "null"] }
      revisit_of: { type: [string, "null"] }
      topic: { type: [string, "null"] }  # 0.10.94: the group of related cards it is worked in (D4 section 12)
      topic_order: { type: [integer, string, "null"] }  # 0.10.94: its reading position in the topic, 1 up
      built_in: { type: [string, "null"] }  # 0.10.93 (A6): the version whose build carries the applied card; 0.10.94 declares it
      released_in: { type: [string, "null"] }  # 0.10.93 (A6): the release that shipped it; 0.10.94 declares it
      revisits: { type: [array, "null"], items: { type: string } }
      review_marks: { type: [array, "null"], items: { type: string } }
      check_applied: { type: [string, "null"] }  # 0.10.98 D16: `decisions check-applied --record` writes it (`pass`, or `missing: …`)
      check_applied_comments: { type: [string, "null"] }  # 0.10.98 D16: the stamp of his comments the record was made against
      processed_by: { type: [string, "null"] }
      superseded_by: { type: [string, "null"] }
      archived_to: { type: [string, "null"] }
x-watchbill:
  awaiting_human: { field: status, values: [open, provisional] }
---
<!-- watchbill: the plugin's text, rewritten whole by `systems init --refresh-bases`; write your own below the end line -->
# decision (substantive)

One substantive decision for the human, tied to no item (ADR-0001): a file in `dev-docs/design-board/`, the `_design-board.base` kanban as the view, `human_*` fields the human's alone. Shipped by the watchbill plugin (`watchbill systems init`); `watchbill decide` writes these records.

`_human_verdict` is a lane (0.10.50, `references/decisions.md`, "The lanes"): the human's (`snoozed`, `yes, show me`, `yes, just do it` (0.10.68: the two flavours of yes; a plain `yes` is read as `yes, show me` for one release and `--refresh-bases` migrates it), `no`, `revise proposal`, `revise card`, `later`, `after POC`, `after MVP`, `talk`, `done` and `can't` (0.10.99: a task's answers), or one of the card's own `options`) or the agent's (`cycle operations` (0.10.94: a card of `kind: cycle`, in front of him), `to do` (0.10.99: a card of `kind: task`, or a decision whose next step is his, in front of him), `documents to review`, `new decisions`, `returning decisions`, `agents drafting`, `agent working`, `agent waiting`, `agent scheduled`, `processed`, `moot` (0.10.94: closed by `decide --moot`, never applied), `agent editing` (0.10.67: held while an agent writes a card from his lanes; `editing_from` keeps the lane it goes back to)), so the schema takes any string and `watchbill decide` checks a verdict against the card's options. An agent writes the field only through the `watchbill decide` verbs, which keep the human's verdict in `previous_verdict`. A system that adds properties of its own keeps them across `systems init --refresh-bases`. A system's own field on a card is an `x_*` key (0.10.73: lower case after `x_`; the schema admits it, the sweep script and the lint ignore it, a Base can read it, the verbs keep it, and `watchbill decide --set x_<key>=<value> CARD` writes one); every watchbill field stays closed. The key was `human_verdict` before 0.10.50; the schema still allows it for one release, `watchbill` reads it as `_human_verdict`, and `--refresh-bases` renames it on every card. `attention_weight` is `quick` or `big` (0.10.50; the key was `weight` before 0.10.102, admitted for one release and renamed on every card by `--refresh-bases`): a big card (a document under Track Changes review, a design or ADR approval, or one the seat marks big with `decide --attention-weight big`) is presented in `documents to review`, a quick one in `new decisions` and then `returning decisions`; his drag between `new decisions` and `documents to review` sets it. `snooze_until` is the human's: an ISO date he may type on a snoozed card, on which `watchbill decisions sweep` brings it back as returning.

`topic` and `topic_order` (0.10.94, D4 section 12) place a card in a group of related cards worked in one sitting, and in its reading position there; `watchbill decide --topic NAME [--topic-order N] CARD` writes them, `watchbill topic recount` renumbers them, and the board's view 0 groups by them. A card in no topic carries neither key.

`processed_by`, `superseded_by` and `archived_to` (0.10.59; the copy editor's collection survey, section 10, proposals 2 and 4) are link fields an agent may set by hand: the commit or design section that absorbed a processed card, the card or record that replaces it, and where it went when archived. `watchbill decide` does not write them.
<!-- watchbill: end of the plugin's text -->
