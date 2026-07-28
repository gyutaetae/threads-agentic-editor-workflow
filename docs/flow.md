# Unified Authoring Flow

## Automatic

1. At the 18:17 KST primary run, query Threads for authored top-level posts since KST midnight and sync newly observed manual posts into history. Watchdogs repeat at 19:17-23:17 KST.
2. If a post already exists, skip the run. If platform state cannot be verified, fail closed and write a failure record.
3. The primary run collects and ranks source candidates, then removes every source already present in publication history. If no unused source remains, select an unused prevalidated reserve ThreadSpec.
4. Build routing metadata and recent-history context.
5. Ask the pinned OpenRouter Gemma model for strict `ThreadCandidate v1` JSON, including the canonical bad/good-request main card.
6. Derive routing/source metadata in code and build `ThreadSpec v1`.
7. Run the shared contract validator, duplicate checks, editorial scoring, and evaluator review.
8. Publish a clean 85+ candidate immediately. For a 70-84 soft failure, revise once with the pinned writer and reevaluate. If it still cannot publish, use an unused prevalidated reserve. Contract errors and uncertain platform state are never bypassed.
9. Immediately before live publishing, query Threads again. Skip if a manual post appeared while generation was running.
10. Render approved text, run the strict dry-run gate, publish, and verify the top-level post through the Threads API. Record generated posts as `origin=auto_openrouter` and reserve posts as `origin=reserve_codex`.
11. After a reserve publish succeeds, move its spec and text from `daily-editor/reserve/available/` to `daily-editor/reserve/used/`. Warn when three or fewer unused reserves remain.

## Manual Codex

1. Read the playbook and recent history.
2. Draft the same four semantic parts, with the canonical bad/good-request card in Part 1.
3. Attach the same fingerprint and source metadata.
4. Build and validate `ThreadSpec v1`.
5. Render `approved-thread-chain.txt` only after approval.
6. Use the same publisher as automation.

The manual GitHub Action collects `workflow_stage`, `failure_mode`,
`artifact_type`, `reusable_unit_type`, and `hook_pattern` as required inputs.
It builds `approved-thread-spec.json` before calling the shared strict gate.

## Failure Flow

- Contract error: block that candidate and route to a strictly valid reserve; never lower the contract.
- Contract warning: keep as review draft; strict publishing blocks it.
- Editorial score 70-84: revise once, then publish only with strict contract plus evaluator approval; otherwise route to reserve.
- Gemma output malformed or unavailable: retry once, retain its deterministic fallback as review-only, and publish a prevalidated reserve. Never publish an alternate model's live replacement.
- Semantic duplicate borderline: require Codex/human review rather than automatic rejection.
- Threads token/API error: block publishing and save a redacted failure record.
- Manual post found during either guard: sync it to history and skip automatic publishing for that KST day.
- Post still absent after a publish attempt: fail the run so a later watchdog can retry. The 18:00-20:00 window is the target; watchdogs may recover through 23:17 KST.
