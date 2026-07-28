# ThreadSpec v1

The machine-readable schema is `schemas/thread-spec-v1.schema.json`.

## Persisted Contract

```text
spec_version: "1.0"
origin: auto_openrouter | auto_groq | manual_codex | manual_human | legacy_import
parts[4]:
  role: hook | diagnosis | action | source
  text: publishable text only
metadata:
  topic
  format
  workflow_stage
  failure_mode
  artifact_type
  reusable_unit_type
  hook_pattern
  source_name
  source_urls[]
generation:
  provider
  requested_model
  actual_model
  prompt_contract_version
```

The `hook` role contains the complete main post, not only its opening sentence: problem hook, `나쁜 요청:` with one quoted request, `좋은 요청:` with three or four quoted requests, and a short judgment closer.

## Ownership

- Threads API owns published IDs, timestamps, and final platform text.
- `ThreadSpec` owns editorial intent and fingerprints.
- Metrics snapshots own time-windowed reactions.

## Compatibility

Legacy `approved-thread-chain.txt` remains accepted as input. It is parsed into the four canonical roles before validation. New automatic runs also emit `approved-thread-spec.json`.

Prevalidated daily-guarantee reserves use the same `ThreadSpec v1` contract. Each available item has a metadata JSON plus a companion text file under `daily-editor/reserve/available/`; successful publication moves both files to `daily-editor/reserve/used/`.

## ThreadCandidate v1

The model-facing schema is `schemas/thread-candidate-v1.schema.json`. It is intentionally smaller than `ThreadSpec`: the model returns exactly `hook`, `diagnosis`, `action`, `source`, `quote_used`, and `quote_id`. Topic, format, source URL, workflow fingerprint, provider, and model identity are derived from trusted routing data in code.

## Publication history

`content-history.jsonl` is the local projection of the platform ledger. New records carry an `origin` such as `auto_openrouter`, `manual_human`, or `external_manual`, plus known post IDs, permalink, main text, model, and editorial metadata. Direct platform posts that cannot be fully classified use `manual_metadata_pending=true` rather than invented metadata.

## Failure records

Automation failures are written to `daily-editor/failures/YYYY-MM-DD-STAGE-TYPE.json`. Records contain the KST date, failure timestamp, stage, categorized error type, and a redacted error message. Access tokens are never persisted.
