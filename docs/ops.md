# Operations

Human-facing operating guide for `@arxiv.ai`. Generation agents should not load this file by default.

## What This File Is For

Use this file when deciding whether to publish, pause automation, promote learnings, refresh tokens, or change workflows.

Do not use it as channel voice guidance. Voice and product rules live in `docs/threads-channel-playbook.md`; promoted generation rules live in `docs/learnings.md`.

## Daily Publishing Decision

Before publishing, check:

- The post solves a concrete paper-work problem.
- It includes a reusable `prompt`, checklist, agent instruction, or workflow.
- Source links are in the final reply and say what to inspect.
- Automatic mode does not invent first-person experience.
- The main post is not just AI news, quote commentary, or generic motivation.

Local dry run:

```powershell
.\scripts\publish-approved-chain.ps1 -DryRun
```

Publish:

```powershell
.\scripts\publish-approved-chain.ps1
```

Scheduled guarantee:

- Primary generation runs at 18:17 KST.
- Watchdogs run hourly from 19:17 through 23:17 KST.
- Any authored top-level post, including a manual post, satisfies the day.
- A score of 70-84 triggers one revision. A remaining soft failure uses a prevalidated reserve.
- Model generation falls back in order: OpenRouter, OpenAI, then Groq. Missing provider keys are skipped.
- A missing post after an attempted publish fails the run and leaves the next watchdog eligible.
- Token/API uncertainty remains fail-closed; never risk a duplicate when the platform ledger cannot be read.

GitHub Actions manual publish:

1. Open `Actions`.
2. Run `Publish Threads Chain`.
3. Start with `dry_run = true`.
4. If the preview is correct, rerun with `dry_run = false`.

## When To Pause Automation

Pause scheduled auto-publish when:

- Sources are weak or repeatedly generic.
- Evaluator scores are repeatedly below 85 and reserve usage is accelerating.
- Posts repeat the same hook or structure for several days.
- Threads API errors produce partial or confusing logs.
- The account starts drifting toward news, quotes, or generic prompt content.

To pause quickly, disable the schedule in `.github/workflows/auto-publish-daily-thread.yml` or run only manual workflow dispatch.

## Reserve Operations

Available and consumed reserve chains live at:

```text
daily-editor/reserve/available/
daily-editor/reserve/used/
```

Validate the usable count:

```powershell
python .\scripts\reserve_thread.py remaining
```

Every reserve has separate metadata JSON and publishable text. Do not move an item manually after a failed publish; the publisher moves it only after Threads returns success. Refill with new source URLs before the available count reaches zero.

## Learning Promotion

The self-improvement loop writes proposals, not final rules.

Review:

```text
daily-editor/proposals/learnings.proposed.md
daily-editor/proposals/*.pattern.proposed.md
```

Promote to `docs/learnings.md` when:

- evaluator score is at least 85,
- decision is `publish`, `approved`, or `keep`,
- the rule is durable across more than one post,
- it is not already covered by the playbook or existing learnings.

Promote to `docs/thread-pattern-library.md` when:

- the execution path can be reused,
- it contains a practical prompt/checklist/agent instruction pattern,
- it does not force a single fixed post template.

Do not promote one-off wording fixes.

## Metrics Decision

Use `threads-post-metrics.csv` as weak guidance until at least 20 posts have 24h/72h metrics.

Prefer:

- saves
- reposts
- quotes
- audience replies
- profile visits
- follows gained

Treat views and likes as weaker signals. If a post gets low reach but strong saves/reposts, keep the format under observation instead of discarding it.

Weekly memory is generated at:

```text
daily-editor/memory/weekly-editorial-memory.md
```

Use it to ask: "What should we try next week?" not "What must every post become?"

## Threads API Setup

Required Meta app scopes:

```text
threads_basic
threads_content_publish
```

Optional for analytics:

```text
threads_manage_insights
```

Set local environment values only in PowerShell or local ignored env files:

```powershell
$env:THREADS_APP_ID = "YOUR_THREADS_APP_ID"
$env:THREADS_APP_SECRET = "YOUR_THREADS_APP_SECRET"
$env:THREADS_REDIRECT_URI = "YOUR_REGISTERED_REDIRECT_URI"
```

Token flow:

```powershell
python .\scripts\threads_auto_upload.py auth-url
python .\scripts\threads_auto_upload.py exchange-code --code "CODE_FROM_REDIRECT_URL"
python .\scripts\threads_auto_upload.py long-token
python .\scripts\threads_auto_upload.py me
```

Set the long-lived token:

```powershell
$env:THREADS_ACCESS_TOKEN = "LONG_LIVED_ACCESS_TOKEN"
```

Never commit access tokens. GitHub Actions uses the `THREADS_ACCESS_TOKEN` repository secret.

## Useful Commands

Generate daily candidates:

```powershell
.\scripts\run-daily-agentic-editor.ps1
```

Generate a thread from candidates:

```powershell
python .\scripts\generate_auto_thread.py --date 2026-06-22 --candidates-path ".\daily-editor\2026-06-22-candidates.json"
```

Propose self-improvement learnings:

```powershell
python .\scripts\propose_learnings.py
```

Update weekly memory:

```powershell
python .\scripts\update_weekly_editorial_memory.py
```

Collect metrics:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```
