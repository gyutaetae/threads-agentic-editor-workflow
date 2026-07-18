---
name: threads-editor-feedback-loop
description: "Run the @arxiv.ai editorial loop from Korean Threads draft through user feedback and playbook-based revision. Use when Codex is asked to create or revise a draft, collect the user's evaluation, preserve durable preferences, then validate an approval-ready next draft without publishing it."
---

# Threads Editorial Feedback Loop

Use this skill with `threads-agentic-editor` for drafting and `threads-post-publisher` only after the user explicitly asks to publish.

## Workflow

1. Read `docs/threads-channel-playbook.md`, `docs/learnings.md`, and recent `content-history.jsonl`.
2. Draft one `ThreadSpec v1` chain: `hook -> diagnosis -> action -> source`. Keep the canonical Part 1 card: problem hook, `나쁜 요청:` one quote, `좋은 요청:` three or four quotes, and a short judgment closer.
3. Validate with `scripts/thread_spec.py validate --require-metadata --strict`. Present the draft as a draft; do not publish.
4. Ask for concise editorial feedback when it has not yet been supplied: what to keep, what feels repeated or unclear, and what concrete audience/example should appear.
5. Apply direct feedback to the current draft. Re-run the same strict validation. Preserve the same source only when its factual role still fits.
6. Record meaningful user evaluation in `daily-editor/curation/codex-curation-log.jsonl` with the date, selected source, user preference, reason for the revision, and preferred future signals. Do not invent a positive evaluation.
7. Treat one-off wording feedback as a current-draft revision only. Create a learning proposal for repeated or durable preferences; update `docs/learnings.md` or the playbook only after the promotion criteria in `docs/ops.md` are met.
8. Execute the playbook by rechecking topic fit, recent-history overlap, source boundary, four-part contract, and the reusable artifact before handoff. Publishing remains a separate, explicit user decision.

## Feedback Translation

- “This feels like a recent post” → change the failure scene, workflow stage, artifact, and closer; do not only swap synonyms.
- “Make it more useful” → add a specific venue, paper type, benchmark, or reviewer scenario that changes the requested checks.
- “Keep this format” → preserve the canonical Part 1 card but vary the research failure and concrete quoted requests.
- “Use this again” → save it as a proposed learning first; do not silently hard-code it into the playbook.

## Handoff

Return the validated draft, source facts, account interpretation, and fingerprint fields. Do not put those labels inside the publishable chain. Do not publish unless the user separately asks to post it.
