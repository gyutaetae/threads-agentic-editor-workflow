---
name: threads-post-publisher
description: "Prepare, validate, publish, and record approved Threads reply chains for @arxiv.ai. Use when Codex is asked to upload/post/publish a Threads chain, revise an approved chain for publishing, run the prepublish quality gate, fix Threads API publish errors, or collect post metrics for the AI research workflow account."
---

# Threads Post Publisher

## Scope

Prepare, validate, publish, and record approval-ready Threads chains for `@arxiv.ai`.

Default repo:

```text
C:\Users\kym70\threads-agentic-editor-workflow
```

Use `docs/threads-channel-playbook.md` for editorial rules. Use this skill for packaging, validation, publishing, API debugging, and metrics. Use `$threads-agentic-editor` for full drafting/scoring.

## Prepublish Flow

1. Work from the repo root.
2. Read `docs/threads-channel-playbook.md` before revising or validating any chain.
3. Keep publishable text clean:
   - exactly 4 parts separated by `---`
   - roles are exactly `hook -> diagnosis -> action -> source`
   - Part 1 is the unlabelled canonical card: problem hook, `나쁜 요청:` one quote, `좋은 요청:` three or four quotes, and a short judgment closer
   - Parts 2-4 use the role headings required by the playbook
   - no `Reply 1:`, `Reply 2:`, `Reply 3:`
   - no JSON, fenced code blocks, or metadata
   - full `https://...` URLs in the source reply
4. Preserve metadata when available: topic, format, source count, source name, source URL, image/card flag, and topic fingerprint.
5. If the user only asks for a dry run, do not publish.
6. Build `approved-thread-spec.json` (`ThreadSpec v1`) and render `approved-thread-chain.txt` from it.
7. Run the shared strict gate and fix any contract, quality, or length issue before publishing.

Dry run:

```powershell
.\scripts\publish-approved-chain.ps1 -SpecPath ".\approved-thread-spec.json" -Topic "research ai workflow" -SourceCount 3 -DryRun
```

Publish:

```powershell
.\scripts\publish-approved-chain.ps1 -SpecPath ".\approved-thread-spec.json" -Topic "research ai workflow" -SourceCount 3 -Origin "manual_human"
```

## Debug Rules

- Do not ask the user to paste tokens into chat.
- Use existing local env vars or GitHub secrets.
- If the API fails, preserve and report the response body.
- Redact access tokens before persisting failure details.
- A Threads API/token error must fail closed; never assume that no post exists.
- If `/threads_publish` says the media/container does not exist, check container readiness and retry logic in `scripts/threads_auto_upload.py`.
- Do not ask for `THREADS_USER_ID` unless `/me` is unavailable.

## Metrics

After publishing, collect snapshots with:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

Use the playbook before suggesting direction changes. Optimize for useful replies, saves, shares, follows, and comment quality, not views alone.
