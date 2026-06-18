---
name: threads-post-publisher
description: "Prepare, validate, publish, and record approved Threads reply chains for @gyu_in_black. Use when Codex is asked to upload/post/publish a Threads chain, revise an approved chain for publishing, run the prepublish quality gate, fix Threads API publish errors, or collect post metrics for the AI-assisted research workflow channel."
---

# Threads Post Publisher

## Scope

Prepare, validate, publish, and record only approval-ready Threads chains for `@gyu_in_black`. Keep this skill operational: use repo docs for editorial context, repo scripts for execution, and avoid restating the channel strategy here.

Default repo:

```text
C:\Users\user\Desktop\threads-agentic-editor-workflow
```

## Load Only What Is Needed

Read these repo docs only when relevant:

- `docs/threads-channel-playbook.md`: account concept, topic fit, first-line hook, reply-chain shape, length limits, metrics/comments learning.
- `docs/threads-api-autopost-setup.md`: API setup or auth troubleshooting.

Use `$threads-agentic-editor` for full drafting/scoring. Use this skill for final packaging, publishing, API debugging, and metrics.

## Prepublish Flow

1. Work from the repo root.
2. Read `docs/threads-channel-playbook.md` before revising, packaging, or validating any chain.
3. If drafting or revising, preserve the current channel pivot: AI-assisted paper reading, literature review, paper drafting, citation verification, and research-agent architecture.
4. Keep publishable text clean:
   - exactly 4 parts separated by `---`
   - no `Reply 1:`, `Reply 2:`, `Reply 3:`
   - no `[한 줄 원칙:]`, `한 줄 원칙:`, or `[초안 작성 모드]`
   - no JSON or fenced code blocks
   - full `https://...` URLs in the source reply
5. Preserve or pass topic fingerprint metadata when available:
   - `Series`
   - `SeriesPart`
   - `PublicTheme`
   - `TopicPillar`
   - `WorkflowStage`
   - `FailureMode`
   - `SolutionPattern`
   - `BadRequest`
6. Do not invent missing approval. If the user only asks for a dry run, do not publish.
7. Write the approved chain to `approved-thread-chain.txt`.
8. Separate each Threads post/reply with exactly:

```text
---
```

9. Run:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3 -DryRun
```

10. Fix any quality gate or length issue before publishing.

## Approved Chain File

The file should contain only publishable text:

```text
main post text
---
first reply text
---
second reply text
---
third reply text
```

Do not add Markdown headings, reply labels, metadata, analysis, or notes to `approved-thread-chain.txt`.

## Publish

Publish only when the user explicitly approves or directly asks to publish/upload now.

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3
```

The wrapper should:

- run the quality gate
- verify the current Threads account from `THREADS_ACCESS_TOKEN`
- publish each reply in order
- append the first post to `threads-post-metrics.csv`

Do not ask the user to paste tokens into chat. Use an existing environment variable or tell the user the exact terminal command to set `THREADS_ACCESS_TOKEN` locally. Do not write access tokens to repo files.

Do not ask for `THREADS_USER_ID` unless `/me` is unavailable. A stale user ID causes misleading API errors.

## Debug Rules

- If the API fails, preserve and report the response body.
- If `/threads_publish` says the media/container does not exist, check container readiness and retry logic in `scripts/threads_auto_upload.py`.
- If credentials are missing from Codex's shell, give the exact command for the user's terminal instead of asking for secrets in chat.

## Metrics

After publishing, collect snapshots with:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

Use the channel playbook before suggesting direction changes. Optimize for useful replies, shares, follows, and comment quality, not views alone.
