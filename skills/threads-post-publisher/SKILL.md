---
name: threads-post-publisher
description: Prepare, validate, publish, and record approved Threads reply chains for @gyu_in_black. Use when Codex is asked to upload/post/publish a Threads chain, revise an approved chain for publishing, run the prepublish quality gate, fix Threads API publish errors, or collect post metrics for the AI agent/harness developer channel.
---

# Threads Post Publisher

## Scope

Publish only approval-ready Threads chains for `@gyu_in_black`. Keep this skill operational: use repo docs for editorial context, repo scripts for execution, and avoid restating the channel strategy here.

Default repo:

```text
C:\Users\kym70\threads-agentic-editor-workflow
```

## Load Only What Is Needed

Read these repo docs only when relevant:

- `docs/threads-channel-operating-system.md`: account concept, topic fit, first-line hook, reply-chain shape.
- `docs/threads-agentic-editor-architecture.md`: source-to-draft-to-publish workflow and decision intent.
- `docs/threads-reaction-learning-architecture.md`: metrics/comments collection and channel learning.
- `docs/threads-api-autopost-setup.md`: API setup or auth troubleshooting.

Use `$threads-agentic-editor` for full drafting/scoring. Use this skill for final packaging, publishing, API debugging, and metrics.

## Prepublish Flow

1. Work from the repo root.
2. If drafting or revising, apply the docs' current rule: first line names a common mistake, then reframes the better agent/harness criterion.
3. Write the approved chain to `approved-thread-chain.txt`.
4. Separate each Threads post/reply with exactly:

```text
---
```

5. Run:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "agent repo reading" -SourceCount 3 -DryRun
```

6. Fix any quality gate or length issue before publishing.

## Publish

Publish only when the user explicitly approves or directly asks to publish/upload now.

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "agent repo reading" -SourceCount 3
```

The wrapper should:

- run the quality gate
- verify the current Threads account from `THREADS_ACCESS_TOKEN`
- publish each reply in order
- append the first post to `threads-post-metrics.csv`

Do not ask for `THREADS_USER_ID` unless `/me` is unavailable. A stale user ID causes misleading API errors.

## Debug Rules

- If the API fails, preserve and report the response body.
- If `/threads_publish` says the media/container does not exist, check container readiness and retry logic in `scripts/threads_auto_upload.py`.
- If credentials are missing from Codex's shell, give the exact command for the user's terminal instead of asking for secrets.

## Metrics

After publishing, collect snapshots with:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

Use reaction docs before suggesting channel direction changes. Optimize for useful replies, shares, follows, and comment quality, not views alone.
