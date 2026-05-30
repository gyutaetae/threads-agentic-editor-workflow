# Threads Agentic Editor Architecture

## Positioning

Target reader:

```text
Codex, Claude Code, Cursor로 일 잘하고 싶은 개발자
```

Promise:

```text
매일 하나, 개발자가 바로 훔쳐 쓸 수 있는 AI agent 작업법
```

Account concept:

```text
프로 개발자의 AI agent 작업법을 훔쳐보는 계정
```

Decision intent:

```text
GitHub stars and fast-moving repos are the hook.
Harness/workflow insight is the value.
Comments and metrics decide what we repeat.
```

The channel should make developers think:

```text
"이 repo 재밌네" -> "내 agent workflow에도 이 구조를 써볼 수 있겠네"
```

## Workflow

```text
Sources
  Stable only by default: GitHub repos, GitHub README, official RSS/Atom feeds
    ↓
Collector
  agentic_daily_pipeline.py
    ↓
Scorer
  trend, utility, novelty, authority, our_angle, virality
    ↓
Editor Skill
  $threads-agentic-editor
    ↓
Drafts
  A안: 대중형
  B안: 전문형
    ↓
Human Approval
  approved-thread-chain.txt
    ↓
Card Generation
  saveable checklist/workflow card
    ↓
Image Hosting
  GitHub raw URL
    ↓
Threads Publish
  threads_auto_upload.py
    ↓
Metrics
  threads-post-metrics.csv
    ↓
Strategy Memory
  channel-strategy-memory.md
```

## A/B Drafts

A안:

- broader
- stronger hook
- more accessible
- best for reach

B안:

- deeper
- more technical
- stronger credibility
- best for developer trust

C안 is not needed for now. The "saveable" function should be handled inside the card copy, not as a third full post draft.

Generate multiple candidates per day, but only publish one approved post at first.

Default candidate set:

```text
Candidate 1: broad reach hook
Candidate 2: deep harness insight
Candidate 3: GitHub repo/trend teardown
```

Each candidate should show:

```text
Source facts
Our interpretation
Mistake-first hook
Risk/caveat
Why developers will comment
```

Hook policy:

```text
Open by naming a common mistake, then reveal the better criterion.
"만약 [흔한 행동]하고 있다면, [진짜 기준]을 잘못 쓰고 있는 겁니다."
```

This keeps reach tied to the channel concept: the hook exposes a missed workflow/harness decision, not generic outrage.

Prefer candidates that satisfy at least 3:

- reveals harness/agent operating pattern
- uses popular or fast-moving repo as evidence
- changes Codex/Claude Code/Cursor usage
- invites useful disagreement or examples
- can become checklist/teardown/bad-vs-good

## Saveable Card

"저장용" means the reader may bookmark or save the image because it is useful later.

Good card:

- checklist
- decision table
- bad request vs good request
- workflow diagram
- repo teardown framework

Bad card:

- generic AI slogan
- decorative robot image
- article summary with tiny text

## Automation Policy

Now:

```text
auto collect
auto score
auto draft
auto card
auto upload
human approve
auto publish
```

Later:

```text
auto publish only after repeated formats prove engagement
```

## Metrics

Record each post in:

```text
threads-post-metrics.csv
```

Fields:

```text
date
post_id
thread_url
format
topic
hook
source_count
card_used
posted_at
views
likes
replies
reposts
quotes
follows_gained
notes
```

Use:

```powershell
.\record-thread-metrics.ps1 `
  -Topic "agent 작업 분해" `
  -Hook "AI 코딩툴 잘 쓰는 사람은 프롬프트보다 작업 단위를 먼저 설계한다" `
  -Format "A" `
  -SourceCount 2 `
  -CardUsed true
```

After publishing, collect snapshots:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

Use `reply_rate`, `share_rate`, and `follow_rate` to update `channel-strategy-memory.md`.

## Open Questions

1. Which hook style earns useful comments, not only views?
2. Which repo teardown formats convert to follows?
3. Which topics should be repeated or paused in next week's scoring?
