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
   - part 1 is the main post
   - parts 2-4 each start with `[핵심 한 줄]`
   - no `Reply 1:`, `Reply 2:`, `Reply 3:`
   - no JSON, fenced code blocks, or metadata
   - full `https://...` URLs in the source reply
4. Preserve metadata when available: topic, format, source count, source name, source URL, image/card flag, and topic fingerprint.
5. If the user only asks for a dry run, do not publish.
6. Write the approved chain to `approved-thread-chain.txt`.
7. Run the dry run and fix any gate or length issue before publishing.

Dry run:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3 -DryRun
```

Publish:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3
```

Optional image/card metadata:

```powershell
$env:THREADS_IMAGE_URL = "https://..."
$env:THREADS_ALT_TEXT = "..."
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3 -CardUsed
```

## Approved Chain File

`approved-thread-chain.txt` should contain only publishable text:

```text
main post text
---
[first reply core line]
first reply text
---
[second reply core line]
second reply text
---
[third reply core line]
third reply text
```

Do not add headings, labels, metadata, analysis, or notes.

## GitHub Actions Publish

Use `Publish Threads Chain` when the user asks to publish through GitHub Actions. Run `dry_run=true` first unless the user explicitly says to skip it.

Important inputs:

- `thread_text`: approved chain, separated with `---`
- `dry_run`: true for validation, false for live publish
- `topic`, `format`, `source_count`, `source_name`, `source_url`
- `image_url`, `alt_text`, `card_used` when the main post uses an image

## Debug Rules

- Do not ask the user to paste tokens into chat.
- Use existing local env vars or GitHub secrets.
- If the API fails, preserve and report the response body.
- If `/threads_publish` says the media/container does not exist, check container readiness and retry logic in `scripts/threads_auto_upload.py`.
- Do not ask for `THREADS_USER_ID` unless `/me` is unavailable.

## Metrics

After publishing, collect snapshots with:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

Use the playbook before suggesting direction changes. Optimize for useful replies, saves, shares, follows, and comment quality, not views alone.
