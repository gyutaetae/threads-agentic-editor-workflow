---
name: threads-agentic-editor
description: Use when drafting, scoring, reviewing, packaging, publishing, or analyzing Threads posts for @gyu_in_black about Codex, Claude Code, Cursor, AI coding agents, subagents, MCP, harness engineering, GitHub AI repos, or developer workflow automation. This skill turns fresh technical sources into practical developer-facing Threads posts with stronger hooks, fact checks, reply chains, source/repo explanations, approval-ready publishing artifacts, one-command publishing, and reaction-based channel learning.
---

# Threads Agentic Editor

## Mission

Create one useful Threads post per day for developers who want to work better with Codex, Claude Code, and Cursor.

Positioning:

> 프로 개발자의 AI agent 작업법을 훔쳐보는 계정

Promise:

> 매일 하나, 개발자가 바로 훔쳐 쓸 수 있는 AI agent 작업법

Editorial thesis:

> Popular AI repos are the hook. Harness/workflow insight is the value.

Do not stop at "this repo is trending." Explain what the repo reveals about how serious developers structure agent work.

## Default Workflow

1. Collect sources from GitHub, official blogs/docs, and credible technical discussions.
2. Score candidates by trend, utility, novelty, authority, our angle, and virality.
3. Draft two options:
   - A: broader, punchier, easier to share.
   - B: deeper, more technical, stronger for credibility.
4. For the selected option, produce:
   - main post
   - 1-3 replies if needed
   - card title and 3-5 card bullets
   - source list
   - risk/caveat notes
5. Do not publish automatically unless the user explicitly approves the final draft.
6. After approval, publish with the repo's one-command publisher rather than manually assembling Python flags.

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

Topic must satisfy at least 3 of 5:

- reveals a new harness/agent operating pattern
- uses a popular or fast-moving GitHub repo as evidence
- changes how a developer asks Codex/Claude Code/Cursor to work
- can trigger useful comments, disagreement, or examples
- can become a checklist, teardown, or bad-vs-good example

Prefer permissions, memory, tools, evals, logs, rollback, and workflow design over generic prompt advice.

Allowed hook style:

- mistake-first diagnostic: "만약 [흔한 행동]하고 있다면, [진짜 기준]을 잘못 쓰고 있는 겁니다."
- strong claim
- common mistake reversal
- "bad request vs good request"
- "프로들은 이렇게 한다"
- "star보다 먼저 봐야 할 것"
- concrete diagnostic checklist

Default first-line rule:

1. Name the reader's likely mistake.
2. Reframe the real criterion.
3. Then explain the better workflow.

Good:

> AI agent에게 긴 프롬프트만 주고 있다면, agent를 잘못 쓰고 있는 겁니다.

> GitHub star부터 보고 있다면, AI repo를 잘못 읽고 있는 겁니다.

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
5. Bad request vs good request

Current proven format to repeat for practical workflow posts:

```text
Main: 나쁜 요청 / 좋은 요청
Reply 1: 적용 기준, workflow modes, or review modes
Reply 2: 예시 프롬프트
Reply 3: 참고해서 볼 만한 것들, with links and how to apply each source
```

Repeat the structure, not the topic. Use it for new workflow problems such as PR review, test fixing, refactor scoping, agent permissions, memory setup, rollback, and verification.

## Reply Chain Rule

Default to concise main post plus replies when the idea needs examples.

Use a reply chain when:

- the post exceeds 350 Korean characters
- there is a checklist
- there are 2+ examples
- sources/caveats would weaken the main hook

Main post must stand alone. Replies add proof, examples, or a reusable checklist. Never use more than 3 replies. If the idea needs more, split it into a follow-up post.

Preferred structure for repo/workflow posts:

1. Main: create curiosity with a concrete claim and a short checklist or "나쁜 요청 / 좋은 요청" contrast.
2. Reply: include a copyable "예시 프롬프트" when the post teaches an agent workflow.
3. Replies 1-N: explain one checklist item or workflow mode per reply when deeper context is needed.
4. Final reply: list source repos/docs/blogs with links only when they help inspection, and explain how to apply each source.

Avoid ending at a bare checklist. Add the "why" or the reader has little reason to care.

Add a natural comment hook when useful:

- "여러분은 agent에게 어디까지 권한을 주나요?"
- "이 기준에서 제일 자주 빠지는 건 몇 번인가요?"
- "이 repo에서 복사할 만한 건 기능보다 구조입니다."

Do not use forced engagement bait.

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

## Publishing Rule

When the user approves a chain, write it to:

```text
approved-thread-chain.txt
```

Separate thread parts with:

```text
---
```

Then use this dry-run command from the repo root:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "agent repo reading" -SourceCount 5 -DryRun
```

After the user confirms, publish with:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "agent repo reading" -SourceCount 5
```

This wrapper checks the approved chain, uses the current `THREADS_ACCESS_TOKEN` to retrieve the correct Threads account ID, publishes the chain in order, and records the first post in `threads-post-metrics.csv`.

Do not ask the user to manually set `THREADS_USER_ID` unless the token verification endpoint is unavailable. A stale user ID causes hard-to-debug `Unsupported post request` errors.

For account concept, topic selection, proven formats, length limits, and reaction learning, use `docs/threads-channel-playbook.md`.

To run the quality gate without publishing:

```powershell
.\scripts\check-approved-chain.ps1
```

To collect metrics for a published post:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

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
