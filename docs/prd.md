# Unified Threads Authoring

## Goal

Make manual Codex drafts and automatic LLM drafts produce the same publishable `@arxiv.ai` chain contract while preserving variation in hooks, wording, and examples.

## Scope

- One versioned `ThreadSpec` for draft text and editorial metadata.
- One structural validator shared by generation, manual quality checks, and publishing.
- Provider/model identity recorded for every generated spec.
- Duplicate prevention that escalates from exact checks to structured and semantic checks.
- One unattended run near 18:00 KST, skipped when an authored top-level post already exists that KST day.
- Platform posts from both Codex/manual and automatic paths reconciled into local history.

## Non-goals

- Publishing today's draft.
- Making all posts use identical wording.
- Treating a model score as a substitute for human approval.
- Backfilling metadata for older manual posts beyond their platform ID, text, timestamp, and permalink.

## Success Criteria

- Both manual and automatic publish paths reject non-four-part chains.
- Every valid chain follows `hook -> diagnosis -> action -> source`.
- Both paths render Part 1 as `problem -> 나쁜 요청 1개 -> 좋은 요청 3-4개 -> judgment closer`.
- Generation emits a `ThreadSpec v1` artifact alongside publishable text.
- The editor skill delegates channel format decisions to the playbook instead of duplicating them.
- Existing generation tests pass and shared contract tests cover manual and automatic callers.
- Automatic generation uses the pinned OpenRouter Gemma slug and strict candidate JSON Schema.
- Manual-post detection is checked both before generation and immediately before publish.
- A quality-gate failure leaves review artifacts only; a Threads token/API failure is recorded and blocks publishing.
