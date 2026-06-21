# @arxiv.ai Threads Workflow

AI로 논문을 읽고, 요약하고, 초안을 만들고, citation을 검증하는 `@arxiv.ai` 운영 workflow.

```text
AI agent로 논문 작업을 더 검증 가능한 작업 단위로 바꾼다.
```

## Core Files

```text
docs/threads-channel-playbook.md
  채널 컨셉, format router, human_signal, source rule, self-improvement 원칙.

docs/learnings.md
  다음 글 생성 prompt 상단에 넣는 짧은 durable rule.

docs/ops.md
  사람이 publish, pause, learning promotion, token/API 운영을 결정할 때 보는 문서.

skills_library/
  잘된 실행 경로를 결정화한 reusable skill.

daily-editor/runs/
daily-editor/evaluations/
  실행 로그와 evaluator 로그.

daily-editor/proposals/
daily-editor/memory/
  자동 생성되는 learning 제안과 weekly metrics memory.
```

## Daily Local Flow

Generate candidates:

```powershell
.\scripts\run-daily-agentic-editor.ps1
```

Generate an approved chain from candidates:

```powershell
python .\scripts\generate_auto_thread.py --date 2026-06-22 --candidates-path ".\daily-editor\2026-06-22-candidates.json"
```

Dry run:

```powershell
.\scripts\publish-approved-chain.ps1 -DryRun
```

Publish:

```powershell
.\scripts\publish-approved-chain.ps1
```

## Auto Publish

`Auto Publish Daily Threads Chain` collects candidates, generates a thread, evaluates it, validates it, publishes it, and records history.

Required GitHub secrets:

```text
GROQ_API_KEY
THREADS_ACCESS_TOKEN
```

Optional GitHub variables:

```text
GROQ_MODEL
THREADS_IMAGE_URL
THREADS_ALT_TEXT
POSTS_PER_DAY
```

## Self-Improvement Loop

Current phase:

```text
generate -> evaluate -> log -> propose learnings -> human promotion -> next generation
```

Run proposals manually:

```powershell
python .\scripts\propose_learnings.py
```

Review:

```text
daily-editor/proposals/learnings.proposed.md
skills_library/*.proposed.md
```

Promote only durable rules into:

```text
docs/learnings.md
skills_library/*.md
```

## Metrics

Collect metrics:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

`audience_replies` is preferred over raw `replies`:

```text
audience_replies = replies - chain_replies - own_replies
```

Use metrics as weak guidance until enough 24h/72h data exists. Prefer saves, reposts, quotes, audience replies, profile visits, and follows over views alone.
