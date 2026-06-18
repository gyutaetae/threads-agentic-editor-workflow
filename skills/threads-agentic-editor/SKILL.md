---
name: threads-agentic-editor
description: "Use when drafting, scoring, reviewing, or analyzing @gyu_in_black Threads posts about AI-assisted research workflows: paper reading, literature review, evidence matrices, paper drafts, citation checks, reviewer critique, and research agent architecture."
---

# Threads Agentic Editor

## Mission

Create useful Threads chains for researchers and students who want to use AI to read, summarize, draft, cite, and verify papers better.

Positioning:

> 자체구축 AI 에이전트로 논문을 읽고 쓰는 대학생 개발자

Promise:

> 연구자와 대학생을 위한 AI 논문 작업법. 프롬프트가 아니라 읽기, 요약, 레퍼런스, 초안, 검증 흐름을 설계한다.

Use `docs/threads-channel-playbook.md` as the source of truth for account concept, topic fit, exact chain shape, forbidden labels, source rules, and reaction learning. Do not duplicate or override that file here.

## Workflow

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

Default internal series:

```text
AI로 논문 쓰는 법
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

Do not include reply labels inside the publishable chain block. Labels are acceptable only outside the block when explaining the draft to the user.
