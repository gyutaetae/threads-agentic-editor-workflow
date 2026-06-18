---
name: threads-agentic-editor
description: "Use when drafting, scoring, reviewing, or analyzing @gyu_in_black Threads posts about AI-assisted research workflows: paper reading, literature review, evidence matrices, paper drafts, citation checks, reviewer critique, and research agent architecture."
---

# Threads Agentic Editor

## Mission

Create useful Threads chains for researchers and students who want to use AI to read, summarize, draft, cite, and verify papers better.

Positioning:

<<<<<<< HEAD
> agent로 논문 읽고, 글 쓰고, 개발하는 23살 대학생 개발자가 직접 실험한 AI 사용법

Promise:

> 매일 하나, 개발자가 바로 복사해 쓸 수 있는 agent 작업법
=======
> 자체구축 AI 에이전트로 논문을 읽고 쓰는 대학생 개발자

Promise:

> 연구자와 대학생을 위한 AI 논문 작업법. 프롬프트가 아니라 읽기, 요약, 레퍼런스, 초안, 검증 흐름을 설계한다.
>>>>>>> 08a23dce14fca394f7683f5c58cbf9ac8ba5600e

Use `docs/threads-channel-playbook.md` as the source of truth for account concept, topic fit, exact chain shape, forbidden labels, source rules, and reaction learning. Do not duplicate or override that file here.

<<<<<<< HEAD
> Popular AI repos, official updates, quote/idea hooks, and paper/dev diary moments are hooks. Harness/workflow insight is the value.
=======
## Workflow
>>>>>>> 08a23dce14fca394f7683f5c58cbf9ac8ba5600e

1. Read `docs/threads-channel-playbook.md`.
2. Check recent post history before choosing a topic. Avoid repeating the same failure mode and solution pattern.
3. Collect credible sources from official docs/blogs, papers, named researcher writing, and useful research-tool repos.
4. Score candidates by research utility, source authority, workflow clarity, novelty, likely save value, and topic novelty.
5. Draft two options:
   - A: broad and immediately useful.
   - B: deeper and more technical.
6. For the selected option, produce exactly 4 publishable parts: main + 3 replies.
7. Do not publish automatically. Use `$threads-post-publisher` only after the user approves the final chain.

## Topic Fit

Write for:

- 대학생, 대학원생, and junior researchers using AI for papers
- readers who need paper summaries, literature reviews, drafts, references, and critique
- technical readers who care about source-grounded workflows

Prefer:

- paper reading
- literature review
- evidence matrix
- related work structure
- draft writing
- citation/reference checks
- reviewer critique
- reader/synthesizer/reviewer/editor agent architecture

Avoid:

- generic AI news summaries
- fake guru tone
- unverifiable "최고", "무조건", "혁명" claims
- AI가 논문을 대신 써준다는 식의 과장
- source names without full URLs
- tool reviews without workflow lessons
- repeats of the old `"서론 써줘"` drafting angle unless the new solution is clearly different

## Series And Novelty

<<<<<<< HEAD
- reveals a new harness/agent operating pattern
- uses a popular or fast-moving GitHub repo as evidence
- changes how a developer asks Codex/Claude Code/Cursor to work
- can trigger useful comments, disagreement, or examples
- can become a checklist, teardown, or bad-vs-good example

Prefer permissions, memory, tools, evals, logs, rollback, paper reading/writing workflows, and workflow design over generic prompt advice.

Add human texture without making it a diary:

- 1-2 lines of personal proof from paper/dev work
- failed request -> fixed request
- occasional famous-person quote/idea hook from `data/quote_bank.json`
- direct diagnostic claim

Then move quickly to a copyable prompt, checklist, or workflow mode.

Allowed hook style:

- bad-usage diagnostic: "만약 \"[나쁜 사용 예시]\"라고 사용하고 있다면, [무엇을 잘못 맡기거나 놓친다는 뜻]입니다."
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

> 만약 "이 repo 스타일 기억해서 잘 고쳐줘"라고 사용하고 있다면, 기억해야 할 걸 사람 머리에 맡긴다는 겁니다.

> 만약 "star 많은 repo니까 좋은 거 정리해줘"라고 사용하고 있다면, 인기도와 작업 구조를 구분하지 못한다는 겁니다.

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
Main: 만약 [나쁜 사용]이라고 사용하고 있다면 / [무엇을 잘못 맡긴다는 뜻] / 이런 방식으로 요청해보세요
Reply 1: 적용 기준, workflow modes, or review modes
Reply 2: 예시 프롬프트
Reply 3: 참고해서 볼 만한 것들, with links and how to apply each source
=======
Default internal series:

```text
AI로 논문 쓰는 법
>>>>>>> 08a23dce14fca394f7683f5c58cbf9ac8ba5600e
```

Default first arc:

1. 논문 요약 자동화
2. Related Work 자동화
3. Evidence Matrix 만들기
4. AI로 논문 초안 쓰기
5. Citation 검증 자동화
6. 연구자를 위한 AI Agent

Before drafting, identify:

- `series`
- `series_part`
- `public_theme`
- `topic_pillar`
- `workflow_stage`
- `failure_mode`
- `solution_pattern`
- `bad_request`

Block the draft if the recent history has the same `failure_mode` and `solution_pattern`. Same broad pillar is allowed only when the workflow stage or practical fix is different.

## Draft Rules

Follow the current playbook. The stable constraints are:

<<<<<<< HEAD
1. Main: start with "만약 [나쁜 사용]이라고 사용하고 있다면", explain what that mistake means, then add "이런 방식으로 요청해보세요" with better examples.
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
=======
- Exactly 4 parts: main + 3 replies.
- Each part under 500 characters.
- Main uses a natural or `만약...` hook, one bad request, four good request examples, and a plain principle.
- Good request section includes four numbered quoted constraints.
- The second part explains why each request is good and includes one `- 활용:` line per request.
- The third part starts with `예시 프롬프트:` and includes four quoted prompts corresponding to the four requests.
- The fourth part starts with `참고해서 볼 만한 것들:` and links actual Korean technical blog posts or GitHub repositories, followed by `- 볼 부분:`.
- Do not use a generic product homepage as the final reference.
- Famous-person quotes are optional and may only come from the candidate's `optional_verified_quote`.
- Use at most one quote, only when it directly supports the workflow lesson. Otherwise omit it.
- When used, preserve the cataloged Korean quote exactly and add the verified source under `인용 원문:`.
- Do not put `Reply 1:`, `Reply 2:`, `Reply 3:`, `[한 줄 원칙:]`, `한 줄 원칙:`, or `[초안 작성 모드]` inside publishable text.
- Do not use JSON or fenced code blocks for prompt examples.
>>>>>>> 08a23dce14fca394f7683f5c58cbf9ac8ba5600e

## Source And Fact Rules

Use primary or credible sources:

- official docs/blogs from OpenAI, Anthropic, Google, tool makers
- arXiv or published papers
- original writing by named researchers
- official docs for research tools such as NotebookLM, Elicit, Zotero, Semantic Scholar

Always separate:

- Source facts: what the source directly says.
- Our interpretation: how to turn it into a research workflow.

Use short quotes only, link the original, and avoid uncited expert claims.

## Handoff To Publisher

When the user approves a chain, hand off the exact approved text to `$threads-post-publisher` or write it to:

```text
approved-thread-chain.txt
```

Separate thread parts with:

```text
---
```

Dry run from the repo root:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3 -DryRun
```

Publish after confirmation:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3
```

Quality gate only:

```powershell
.\scripts\check-approved-chain.ps1
```

## Output Shape

When asked to produce or compare drafts, keep metadata outside the publishable blocks:

```text
Recommended: A or B

Source Facts:
- ...

Our Interpretation:
- ...

A안: 대중형
Publishable chain:
```text
...
---
...
---
...
---
...
```
Sources:
Risk:
Fingerprint:
- series:
- series_part:
- public_theme:
- topic_pillar:
- workflow_stage:
- failure_mode:
- solution_pattern:
- bad_request:

B안: 전문형
...
```

<<<<<<< HEAD
When creating files, write the approved chain to:

```text
approved-thread-chain.txt
```

Separate thread parts with:

```text
---
```

For detailed examples, see `references/examples.md`.

=======
Do not include reply labels inside the publishable chain block. Labels are acceptable only outside the block when explaining the draft to the user.
>>>>>>> 08a23dce14fca394f7683f5c58cbf9ac8ba5600e
