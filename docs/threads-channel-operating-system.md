# Threads Channel Operating System

Always-reference guide for `@gyu_in_black`.

## Core Concept

```text
프로 개발자의 AI agent 작업법을 훔쳐보는 계정
```

We cover harness engineering, AI agents, Codex, Claude Code, Cursor, MCP, subagents, and high-signal GitHub repos. The goal is not AI news. The goal is to turn interesting agent/harness signals into developer workflow insight.

Reader promise:

```text
매일 하나, 개발자가 바로 훔쳐 쓸 수 있는 AI agent 작업법
```

## Editorial Thesis

Developers are curious about popular AI repos, but they stay for the hidden workflow lesson.

Good post:

```text
"이 repo가 뜬다" -> "왜 개발자가 봐야 하나" -> "내 workflow에 뭘 복사할까"
```

Bad post:

```text
"이 repo는 stars가 많다" -> 기능 나열 -> 끝
```

Stars are a hook and trend signal, not proof of quality.

## Topic Selection

Pick topics that satisfy at least 3 of 5:

- reveals a new harness/agent operating pattern
- uses a popular or fast-moving GitHub repo as evidence
- changes how a developer asks Codex/Claude Code/Cursor to work
- creates a useful disagreement or question in comments
- can become a checklist, teardown, or bad-vs-good example

Prefer:

- harness structure over model hype
- permissions, memory, tools, evals, logs, rollback over generic prompts
- "what to copy into your workflow" over "what the repo does"

## Default Chain

1. Main: mistake-first hook + one checklist or contrast.
2. Replies: one idea per reply. If the main has 1-5, explain each item in its own reply.
3. Final reply: source repos with links only when they help inspection; explain each repo's meaning.

The main post must stand alone. Replies should add curiosity, proof, and a reason to comment.

## First-Line Hook

Default opening:

```text
만약 [흔한 행동]하고 있다면, [진짜 기준]을 잘못 쓰고 있는 겁니다.
```

Use this to name a common developer mistake before explaining the better workflow. The first line should create a small diagnostic shock, not insult the reader.

Examples:

- "AI agent에게 긴 프롬프트만 주고 있다면, agent를 잘못 쓰고 있는 겁니다."
- "GitHub star부터 보고 있다면, AI repo를 잘못 읽고 있는 겁니다."
- "Claude Code에게 바로 구현부터 시킨다면, workflow 설계를 건너뛰고 있는 겁니다."

After the hook: explain the missed criterion, give a checklist, then show how to fix it.

## Comment Hooks

End or imply a comment-worthy question when natural:

- "여러분은 agent에게 어디까지 권한을 주나요?"
- "이 기준에서 제일 자주 빠지는 건 몇 번인가요?"
- "이 repo에서 복사할 만한 건 기능보다 구조입니다."

Avoid forced engagement bait. The question should help us learn channel direction.

## Tone

Write like a senior developer showing field notes.

Use:

- "실전에서는 여기서 터집니다"
- "star보다 먼저 볼 건 이겁니다"
- "이건 prompt 문제가 아니라 harness 문제입니다"

Avoid:

- fake guru tone
- generic AI summaries
- unverifiable best/first/revolution claims
- repo links without a workflow lesson

## Formats

- 프로들은 이렇게 씀
- GitHub 인기 repo 해부
- Agent 구조 뜯어보기
- Bad request vs good request
- AI 퇴근 치트키

## Automation Guardrails

- AI may collect, score, draft, check, and prepare.
- Human approves before publishing.
- Publishing uses `scripts/publish-approved-chain.ps1`.
- Metrics and comments should influence future scoring, not blindly chase views.
