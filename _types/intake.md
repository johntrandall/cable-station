---
kind: mdbase.type
name: intake
version: 1
match:
  path_glob: "intake/*.md"
schema:
  dialect: json-schema-2020-12
  value:
    type: object
    additionalProperties: true
    required: [type, system, event, date, from, processed]
    properties:
      type: { const: intake }
      system: { type: string, minLength: 1 }
      project: { type: string }
      event: { type: string, minLength: 1 }
      date: { type: string, pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" }
      from: { type: string, minLength: 1 }
      commit: { type: [string, "null"] }
      processed: { type: [string, "null"] }
      processed_by: { type: [string, "null"] }
      superseded_by: { type: [string, "null"] }
      archived_to: { type: [string, "null"] }
x-watchbill:
  awaiting_human: { field: processed, values: [null] }
---
# intake

An intake note: what an outsider drops in a system's intake folder before ringing its doorbell (`watchbill:intake`). The schema above is the rule; the receiving seat writes `processed`. The fleet's event kinds are `release`, `rename`, `correction`, `request`, `finding` and `proposal`; a system whose contracts define others (a hand-off kind, with the fields its contract names) uses them as they are: `event` is any word and other fields are allowed (0.10.43: the shipped type forbade both, and a system's first `systems init` installed a gate that refused every one of its own records). To pin a system's kinds or fields, edit this file in the system (it is the lead designer's); the plugin never rewrites it once written.

`processed_by` (the commit or design section that absorbed the note), `superseded_by` and `archived_to` are link fields (0.10.59; the copy editor's collection survey, section 10, proposals 2 and 4).
