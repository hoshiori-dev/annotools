# Execution-agent tool contract

Three tools, implemented in the project's `src/` with the SDK's tool mechanism (`agent-vision-tools`
shows the SDK wiring). All coordinates normalized 0–1 relative to the uncropped source.

## record_annotation
Input: `item_uri`, `kind`, `key` (default `""`), `label`, `payload` (object per kind), `confidence`
(0–1, optional), `rounds` (int, optional), `status` (`draft` | `final` | `needs_review`, default
`final`).
Behaviour: resolve `item_uri` → `items.id` (error if unknown); upsert on `(item_id, run_id, kind,
key)` with `ON CONFLICT DO UPDATE` setting payload/label/confidence/rounds/status/updated_at; the
`run_id` is fixed by the pipeline, never chosen by the agent. Validate payload shape per kind
(bbox: 4 numbers in [0, 1] with min < max; polygon: even count ≥ 6; keypoints: triples; rbox: 8).
Return: `{"annotation_id": int, "status": str}`.

## update_annotation
Input: `annotation_id`, any of `label`, `payload`, `confidence`, `rounds`, `status`.
Behaviour: only rows of the current run may change; `final → draft` is refused (the loop must
create a new final via `record_annotation` in a later round); bumps `updated_at`.
Return: the updated row.

## mark_reviewed
Input: `annotation_id`, `verdict` (`accept` | `reject` | `fix`), `note`.
Behaviour: inserts into `reviews`; `reject` sets the annotation `status = 'rejected'`; `fix` sets
`needs_review`.
Return: `{"review_id": int}`.

## Guardrails
- Tools take URIs, never bytes; the agent has no file-write tool outside `data/interim/`.
- Every tool logs `run_id`, `item_uri`, and the caller's round counter for auditing.
- Reject writes for items outside the run's item list (prevents cross-workspace writes).
