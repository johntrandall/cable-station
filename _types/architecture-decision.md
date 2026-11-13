---
kind: mdbase.type
name: architecture-decision
version: 1
match:
  path_glob: "dev-docs/decisions/ADR-*.md"
schema:
  dialect: json-schema-2020-12
  value:
    type: object
    additionalProperties: false
    required: [number, title, status, proposed_by, proposed_at]
    properties:
      number: { type: integer, minimum: 1 }
      title: { type: string, minLength: 1 }
      system: { type: [string, "null"] }
      status: { enum: [proposed, accepted, implemented, superseded] }
      proposed_by: { type: string, minLength: 1 }
      proposed_at: { type: string, minLength: 1 }
      accepted_at: { type: [string, "null"] }
      accepted_how: { type: [string, "null"] }
      supersedes: { type: [string, "null"] }
      superseded_by: { type: [string, "null"] }
      from_decision: { type: [string, "null"] }
      said_in: { type: [string, "null"] }
      spawned: { type: [string, "null"] }
      implemented_at: { type: [string, "null"] }
      implemented_how: { type: [string, "null"] }
      migrated_from: { type: [string, "null"] }
      depicted_in: { type: [string, "null"] }
      archived_to: { type: [string, "null"] }
      review: { enum: [whole, delta, card, null] }
      approved_by: { type: [string, "null"] }
      approved_at: { type: [string, "null"] }
      approved_via: { type: [string, "null"] }
      approved_sha: { type: [string, "null"] }
      approved_hash: { type: [string, "null"] }
      approved_whole_sha: { type: [string, "null"] }
      amended: { type: [string, "null"] }
x-watchbill:
  awaiting_human: { field: status, values: [proposed] }
---
<!-- watchbill: the plugin's text, rewritten whole by `systems init --refresh-bases`; write your own below the end line -->
# architecture-decision (ADR)

An architecture decision record in `dev-docs/decisions/`, `status: proposed` until the human accepts it (ADR-0001), `accepted` once he has, `implemented` once the work landed, `superseded` when a later ADR replaces it; `_decisions.base` is the view. `watchbill land --approved ADR-NNNN` sets `implemented`, `implemented_at` (the landing's time) and `implemented_how` (the landing SHA) on an accepted ADR, so no agent types them. The other keys: `system` (the registry name, 0.10.41: both boards filter on it, so a system's ADRs stay its own through the cross-system queue vault; `watchbill systems init --refresh-bases` stamps it on ADRs that lack it), `supersedes` / `superseded_by` (ADR numbers as strings), `from_decision` (the substantive decision it came from), `said_in` (where the human said it), `spawned` (what it spawned), `migrated_from` (where a migrated record came from). Shipped by the watchbill plugin (`watchbill systems init`); the key set was agreed with the consumer lead designers on 2026-10-20 (cycle 2026-10-20-queued).

`depicted_in` (the design document that depicts the ADR) and `archived_to` (where it went when archived) are link fields (0.10.59; the copy editor's collection survey, section 10, proposals 2 and 3).

`review` and the `approved_*` keys (0.10.69; garbage-chore-tracker's intake of 2026-10-23): an ADR can be the subject of a card that asks for its approval (`decide --asks approval --subject dev-docs/decisions/ADR-NNNN-….md`); the approval step then writes `review: whole` on it while the card is in front of the human and the approval record (`approved_by`, `approved_at`, `approved_via`, `approved_sha`, `approved_hash`, `approved_whole_sha`, `amended`) through the Track Changes tool's `approve` on his yes, as on a design document. The type carries them so the schema gate accepts what the step writes; `--refresh-bases` keeps a system's own added properties (a trailing `# comment` on the line included).
<!-- watchbill: end of the plugin's text -->
