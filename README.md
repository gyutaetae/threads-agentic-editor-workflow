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

docs/thread-pattern-library.md
  잘된 실행 경로를 결정화한 reusable pattern.

daily-editor/runs/
daily-editor/evaluations/
  실행 로그와 evaluator 로그.

daily-editor/curation/
  Codex가 후보를 고른 이유, 자동 1위 후보를 넘긴 이유, 사용자 취향 신호를 남기는 JSONL 로그.

daily-editor/proposals/
daily-editor/memory/
  자동 생성되는 learning 제안과 weekly metrics memory.
```

## Daily Local Flow

PowerShell에서 날짜를 고정한다:

```powershell
$date = Get-Date -Format "yyyy-MM-dd"
```

후보 수집:

```powershell
.\scripts\run-daily-agentic-editor.ps1 `
  -PerQuery 10 `
  -PerFeed 10 `
  -ReadmeTop 10 `
  -Date $date
```

후보에서 승인용 thread chain 생성:

```powershell
python .\scripts\generate_auto_thread.py `
  --date $date `
  --candidates-path ".\daily-editor\$date-candidates.json" `
  --output-path ".\approved-thread-chain.txt" `
  --metadata-path ".\daily-editor\auto-thread-metadata.json" `
  --metrics-path ".\threads-post-metrics.csv" `
  --posts-per-day 1 `
  --post-slot evening `
  --experiment-group manual_evening
```

실제 업로드 전 검증. `-DryRun`을 붙이면 quality gate와 Threads 문안 검증만 하고 업로드하지 않는다:

```powershell
.\scripts\publish-approved-chain.ps1 `
  -Topic "auto generated" `
  -SourceCount 0 `
  -PostSlot evening `
  -DryRun
```

검증에 문제가 없으면 metadata를 읽어 실제 업로드한다. 이 단계는 Threads에 게시하고 `threads-post-metrics.csv`에 기록한다:

```powershell
$metadata = Get-Content ".\daily-editor\auto-thread-metadata.json" -Raw |
  ConvertFrom-Json

.\scripts\publish-approved-chain.ps1 `
  -Topic $metadata.topic `
  -Format $metadata.format `
  -ContentAxis $metadata.content_axis `
  -FormatType $metadata.format_type `
  -PostGoal $metadata.post_goal `
  -FinalCandidateScore ([string]$metadata.final_candidate_score) `
  -QualityScore ([string]$metadata.quality_score) `
  -SourceType $metadata.source_type `
  -PostSlot $metadata.post_slot `
  -ExperimentGroup $metadata.experiment_group `
  -Model $metadata.model `
  -SourceCount ([int]$metadata.source_count) `
  -SourceName $metadata.source_name `
  -SourceUrl $metadata.source_url `
  -WorkflowStage $metadata.workflow_stage `
  -FailureMode $metadata.failure_mode `
  -ResearchProblem $metadata.research_problem `
  -ArtifactType $metadata.artifact_type `
  -HookPattern $metadata.hook_pattern `
  -ReusableUnitType $metadata.reusable_unit_type
```

## Auto Publish

`Auto Publish Daily Threads Chain` collects candidates, generates a thread, evaluates it, validates it, publishes it, and records history.

Required GitHub secrets:

```text
OPENROUTER_API_KEY
THREADS_ACCESS_TOKEN
```

Optional GitHub variables:

```text
LLM_PROVIDER
OPENROUTER_MODEL
LLM_MAX_OUTPUT_TOKENS
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
daily-editor/proposals/*.pattern.proposed.md
```

Promote only durable rules into:

```text
docs/learnings.md
docs/thread-pattern-library.md
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
