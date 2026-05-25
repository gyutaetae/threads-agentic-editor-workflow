# Threads Channel Operating System

This is the always-reference operating guide for `@gyu_in_black`.

## Positioning

Concept:

> 프로 개발자의 AI agent 작업을 훔쳐보는 계정

Benchmark blend:

- CHOI style: fast, strong opening.
- AI Trend style: saveable cards.
- Our edge: developer-practical depth.

Core promise:

> Codex, Claude Code, subagent, harness engineering, and AI automation을 실제 개발자 워크플로우 관점으로 쉽게 풀어준다.

## Default Post Format

Do not write long one-block posts by default.

Default structure:

1. Main post: strong hook + one clear idea.
2. Reply 1: concrete example.
3. Reply 2: practical checklist or framework.
4. Reply 3: caveat, source, or next question.

Use reply chains when:

- post exceeds 350 Korean characters
- there are 2+ examples
- there is a checklist
- a source/caveat would make the main post less punchy

The main post should be strong enough to stand alone.

## Image Rule

Use images when they are saveable or explain structure.

Good images:

- bad request vs good request
- agent workflow diagram
- subagent architecture diagram
- checklist card
- GitHub repo teardown card
- before/after workflow

Bad images:

- generic robot
- abstract AI glow
- unrelated stock photo
- decorative image with no takeaway

Default image style:

- vertical 4:5 card
- high contrast
- one strong title
- one framework/checklist
- no tiny text
- @gyu_in_black footer

## Tone

Write like a developer showing real working notes.

Good:

- "잘 쓰는 사람들은 이렇게 쪼갠다"
- "이건 agent 문제가 아니라 작업 설계 문제다"
- "실전에서는 여기서 터진다"

Avoid:

- "미쳤습니다" overuse
- fake guru tone
- generic AI summary
- unverifiable claims
- investment prediction

## Series

1. 프로들은 이렇게 씀
2. Agent 구조 뜯어보기
3. AI 퇴근 치트키
4. GitHub 인기 레포 해부
5. Karpathy 코멘트 개발자식 번역

## First Post Standard

The first post should introduce the account's angle:

> AI agent 시대의 실력은 프롬프트가 아니라 작업 분해에서 나온다.

Always attach a saveable card when possible.

## Automation Policy

Allowed:

- AI generates candidates
- human approves
- script publishes approved post
- script chains replies
- script publishes image if a public image URL exists

Not allowed:

- fully automatic unreviewed publishing
- publishing claims without a source when factual
- posting local-only image paths to Threads API

## Technical Constraint

Threads API image posts require a public image URL.

Local files like:

```text
C:\Users\kym70\threads-first-post-card.png
```

cannot be posted directly via API unless they are uploaded to public HTTPS hosting first.
