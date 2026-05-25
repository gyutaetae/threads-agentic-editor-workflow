# Threads Agentic Editor Architecture

## Positioning

Target reader:

```text
Codex, Claude Code, Cursor로 일 잘하고 싶은 개발자
```

Promise:

```text
매일 하나, 프로 개발자의 AI agent 작업법
```

Account concept:

```text
프로 개발자의 AI agent 작업법을 훔쳐보는 계정
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

Default review set:

```text
Candidate 1: broad reach
Candidate 2: developer credibility
Candidate 3: timely repo/trend hook
```

Each candidate should show:

```text
Source facts
Our interpretation
Risk/caveat
```

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

After 24 hours, update the row manually or append a follow-up note.

## Open Questions

1. How aggressive should hooks be after the first 10 posts?
2. Which format wins: A안 reach or B안 trust?
3. Should metrics be updated manually from Threads UI or later automated through API if available?
