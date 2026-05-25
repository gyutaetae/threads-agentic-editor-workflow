---
name: threads-agentic-editor
description: Use when drafting, scoring, reviewing, or packaging Threads posts for @gyu_in_black about Codex, Claude Code, Cursor, AI coding agents, subagents, MCP, harness engineering, GitHub AI repos, or developer workflow automation. This skill turns fresh technical sources into practical developer-facing Threads posts with strong hooks, fact checks, reply chains, card copy, and approval-ready publishing artifacts.
---

# Threads Agentic Editor

## Mission

Create one useful Threads post per day for developers who want to work better with Codex, Claude Code, and Cursor.

Positioning:

> 프로 개발자의 AI agent 작업법을 훔쳐보는 계정

Promise:

> 매일 하나, 프로 개발자의 AI agent 작업법

## Default Workflow

1. Collect sources from GitHub, official blogs/docs, and credible technical discussions.
2. Score candidates by trend, utility, novelty, authority, our angle, and virality.
3. Draft two options:
   - A: broader, punchier, easier to share.
   - B: deeper, more technical, stronger for credibility.
4. For the selected option, produce:
   - main post
   - 1-2 replies if needed
   - card title and 3-5 card bullets
   - source list
   - risk/caveat notes
5. Do not publish automatically unless the user explicitly approves the final draft.

## Editorial Rules

Write for:

- developers using or evaluating Codex, Claude Code, Cursor, Copilot, Windsurf, or similar coding agents
- developers who want practical agent workflows, not generic AI news
- solo builders and working engineers who want reusable operating patterns

Avoid:

- generic AI news summaries
- fake guru tone
- unverifiable "1등", "최고", "무조건", "혁명" claims
- investment, market, or product-buying claims without fresh sources
- posts that only describe a repo without explaining what developers can learn from it

Allowed hook style:

- strong claim
- common mistake reversal
- "bad request vs good request"
- "프로들은 이렇게 한다"
- "star보다 먼저 봐야 할 것"

Strong but acceptable:

> AI agent 잘 쓰는 사람은 프롬프트보다 작업 단위를 먼저 설계한다.

Too vague:

> 요즘 AI agent가 정말 중요합니다.

Too risky:

> 이 툴 모르면 개발자로 끝입니다.

## Content Mix

Start with:

- 70% practical workflow
- 20% GitHub repo or trend teardown
- 10% famous-person insight or official release interpretation

Adjust based on tracked engagement.

Core formats:

1. 프로들은 이렇게 시킨다
2. GitHub 인기 레포 해부
3. AI agent 설계 노트
4. AI 퇴근 치트키

## Reply Chain Rule

Default to concise main post plus replies when the idea needs examples.

Use a reply chain when:

- the post exceeds 350 Korean characters
- there is a checklist
- there are 2+ examples
- sources/caveats would weaken the main hook

Main post must stand alone. Replies add proof, examples, or a reusable checklist.

## Card Rule

"저장용" means the image is useful enough that a reader may save/bookmark it for later.

Good card content:

- checklist
- decision table
- bad request vs good request
- mini workflow
- repo teardown framework

Bad card content:

- decorative robot image
- generic AI slogan
- dense article summary
- tiny text

Default card structure:

- vertical 4:5
- one strong title
- 3-5 bullets
- high contrast
- @gyu_in_black footer

## Source And Fact Rules

Use primary sources when possible:

- official docs/blogs
- GitHub repos/releases
- arXiv or research papers
- original talks/posts by named people

Use community sources only for "people are reacting to this" signals, not as factual proof.

Every factual trend claim should have a source. If the evidence is weak, say it as an inference.

Always separate:

- Source facts: what the source directly says or exposes.
- Our interpretation: what this means for developer workflow.

Good:

> 이 repo의 README는 skills, hooks, memory, MCP 설정을 묶은 harness라고 설명한다. 내 해석은 이렇다. 앞으로 AI 코딩툴 실력은 프롬프트보다 작업 환경을 agent에게 어떻게 넘기는지에서 갈릴 가능성이 크다.

Bad:

> 이 repo가 미래 개발의 정답이다.

Use only stable automatic sources by default:

- GitHub Search/REST API
- GitHub repo README
- official RSS/Atom feeds with stable URLs

Do not automatically scrape unstable webpages unless the user explicitly asks.

## Output Shape

When asked to produce a daily draft, output:

```text
Recommended: A or B

Source Facts:
- ...

Our Interpretation:
- ...

A안: 대중형
Main:
...
Reply 1:
...
Card:
- title
- bullets
Sources:
Risk:

B안: 전문형
...
```

When creating files, write the approved chain to:

```text
approved-thread-chain.txt
```

Separate thread parts with:

```text
---
```

For detailed examples, see `references/examples.md`.
