---
name: threads-post-publisher
description: "Validate, dry-run, publish, debug, and record approved @arxiv.ai Threads chains. Use when Codex is asked to upload/post/publish a chain, revise an approved chain for publishing, run the prepublish quality gate, attach an optional image URL, handle Threads API errors, update publish history, or collect metrics."
---

# Threads Post Publisher

## Scope

Prepare, validate, publish, and record approval-ready Threads chains for `@arxiv.ai`. Use `docs/threads-channel-playbook.md` as the editorial source of truth.

## Prepublish Flow

1. Work from the repo root.
2. Read `docs/threads-channel-playbook.md` before revising publishable text.
3. Confirm `approved-thread-chain.txt` contains exactly 4 parts separated by `---`.
4. Keep every part under 500 characters.
5. Preserve metadata from `daily-editor/auto-thread-metadata.json` when available.
6. Run dry-run before live publish unless the user explicitly says to skip it.
7. Publish only after an explicit user request.

Dry run:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 1 -DryRun
```

Publish:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 1
```

Image/card:

```powershell
$env:THREADS_IMAGE_URL = "https://..."
$env:THREADS_ALT_TEXT = "..."
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 1 -CardUsed
```

## Publishable Text Rules

- Do not include metadata, JSON, code fences, or drafting labels.
- Do not put source links in the main post.
- Final reply must explain the source with `- 볼 부분:` or label a verified quote source with `인용 원문:`.
- Current accepted labels include `[먼저 확인할 것]`, `[저장해둘 프롬프트]`, `[참고 논문]`, and `[나의 견해]`.
- If a manual edit changes structure, rerun the quality gate before posting.

## Debug Rules

- Do not ask the user to paste tokens into chat.
- Use existing local env vars or GitHub secrets.
- Preserve and report the Threads API response body when publishing fails.
- If `/threads_publish` says the media/container does not exist, check container readiness and retry logic in `scripts/threads_auto_upload.py`.
- Do not ask for `THREADS_USER_ID` unless `/me` is unavailable.

## Metrics

After publishing, collect snapshots with:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

Use saves, reposts, quotes, audience replies, profile visits, and follows as stronger signals than views alone.
