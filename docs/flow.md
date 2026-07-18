# Unified Authoring Flow

## Automatic

1. At the 18:00 KST scheduled run, query Threads for authored top-level posts since KST midnight and sync newly observed manual posts into history.
2. If a post already exists, skip the run. If platform state cannot be verified, fail closed and write a failure record.
3. Collect and rank a source candidate.
4. Build routing metadata and recent-history context.
5. Ask the pinned OpenRouter Gemma model for strict `ThreadCandidate v1` JSON.
6. Derive routing/source metadata in code and build `ThreadSpec v1`.
7. Run the shared contract validator, duplicate checks, editorial scoring, and evaluator review.
8. If any publish gate fails, retain the review draft and artifacts only.
9. Immediately before live publishing, query Threads again. Skip if a manual post appeared while generation was running.
10. Render approved text, run the strict dry-run gate, publish, and record `origin=auto_openrouter`.

## Manual Codex

1. Read the playbook and recent history.
2. Draft the same four semantic parts.
3. Attach the same fingerprint and source metadata.
4. Build and validate `ThreadSpec v1`.
5. Render `approved-thread-chain.txt` only after approval.
6. Use the same publisher as automation.

The manual GitHub Action collects `workflow_stage`, `failure_mode`,
`artifact_type`, `reusable_unit_type`, and `hook_pattern` as required inputs.
It builds `approved-thread-spec.json` before calling the shared strict gate.

## Failure Flow

- Contract error: block generation or publishing.
- Contract warning: keep as review draft; strict publishing blocks it.
- Editorial score below threshold: save for review, never auto-publish.
- Gemma output malformed or unavailable: retry once, then retain a review-only fallback draft or reject; never publish an alternate model's replacement.
- Semantic duplicate borderline: require Codex/human review rather than automatic rejection.
- Threads token/API error: block publishing and save a redacted failure record.
- Manual post found during either guard: sync it to history and skip automatic publishing for that KST day.
