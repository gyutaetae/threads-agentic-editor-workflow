# Threads Channel Playbook

Single source of truth for `@arxiv.ai`. This file replaces the old separate PRD, ADR, and channel playbook.

## Channel

`@arxiv.ai` is a Korean research workflow account for students, junior researchers, and developers who need to read or write papers with AI.

Core promise:

```text
AI agent로 논문 읽기, 요약, 리서치 정리, 초안 작성, citation 검증을 더 검증 가능한 작업 단위로 바꾼다.
```

This is not an AI news account, quote account, or generic prompt account. A good post starts from a real paper-work problem and ends with something reusable.

## Audience Problems

- AI 요약이 실제 이해로 이어졌는지 확인하기 어렵다.
- 논문은 많지만 비교 기준이 없어 literature review가 흐려진다.
- 초안은 나왔지만 problem-gap-contribution 논리가 약하다.
- `claim`, `evidence`, `limitation`, `citation` 연결이 검증되지 않는다.
- 하나의 AI agent에게 읽기, 비교, 비판, 작성을 다 맡겨 결과가 흐려진다.

## Voice

- 한국어로 짧고 구체적으로 쓴다.
- 사람 이름과 일반 설명은 한국어로 쓴다.
- English는 의미가 흐려질 때만 쓴다: `AI agent`, `claim`, `evidence`, `limitation`, `citation`, `reviewer critique`, `workflow`, `prompt`.
- 실제 경험을 꾸며내지 않는다.
- 근거 없는 `무조건`, `혁명`, `논문 끝`, `역대급`, `미친 생산성`, `이거 모르면 뒤처집니다`를 쓰지 않는다.

## Content Pillars

1. Paper reading: contribution, method, evidence, limitation 추출
2. Literature review: 논문 나열을 evidence matrix로 바꾸기
3. Draft writing: problem-gap-contribution outline 먼저 만들기
4. Citation discipline: reference와 claim 연결 확인
5. Research agent architecture: reader, synthesizer, critic, editor 역할 분리

## Topic Filter

Pick a topic only when it satisfies at least three:

- vague AI request를 구체적인 research workflow로 바꾼다.
- 독자가 바로 복사해 쓸 prompt, checklist, agent instruction, workflow가 있다.
- source-grounded: paper, official docs, named researcher writing, useful repo.
- 실제 연구자가 한 번쯤 겪을 failure mode가 있다.
- 최근 글과 다른 `failure_mode`, `hook_pattern`, `solution_pattern`이다.

Block:

- 같은 source URL의 단순 반복
- 같은 `bad_request`와 같은 fix
- 같은 `failure_mode` + 같은 `solution_pattern`
- source fact와 account interpretation이 섞인 주장

## Human Signal

`human_signal` is the visible trace of judgment.

Manual mode:

- User can provide one line.
- Turn it into a concrete research problem, practical questions, format choice, and one reusable unit.

Automatic mode:

- Infer only source surprise, reader friction, common confusion, verification need, or agent-workflow bottleneck.
- Do not claim first-person experience unless the user supplied it.

Normalize every topic into:

```text
human_signal_source
human_signal_type
workflow_stage
failure_mode
research_problem
```

Initial `human_signal_type` values:

- `summary_suspicion`
- `citation_doubt`
- `literature_overload`
- `draft_without_argument`
- `evidence_missing`
- `agent_role_confusion`
- `reviewer_anxiety`
- `method_understanding_gap`

Derived questions must be practical:

- 진단 질문: 지금 문제가 무엇인가?
- 검증 질문: AI 결과가 맞는지 어떻게 확인할 것인가?
- 다음 행동 질문: AI agent에게 맡길 가장 작은 작업은 무엇인가?

## Format Router

There is no default 4-part chain. Pick the format that best fits the research problem, workflow stage, recent fingerprints, and reusable unit.

Thread rules:

- 1 to 4 parts are allowed.
- Every part must stay under 500 chars.
- Main post must not contain source links.
- Links belong in the final reply with `- 볼 부분:` or `인용 원문:`.
- Do not use labels like `Main:` or `Reply 1:`.
- Do not force the old bad-request/good-request card.

Formats:

| Format | Role |
|---|---|
| `workflow_observation` | AI 논문 작업에서 생긴 판단을 짧게 보여준다. |
| `failed_agent_run` | AI agent에게 잘못 맡겼을 때 무엇이 무너지는지 보여준다. |
| `better_prompt_pattern` | 모호한 요청을 구체적인 research prompt로 바꾼다. |
| `research_checklist` | AI 결과물을 사람이 검증할 기준을 준다. |
| `agent_role_split` | reader, synthesizer, critic, editor처럼 역할을 나눈다. |
| `tiny_source_case` | 논문, repo, 문서 하나를 research workflow로 번역한다. |
| `weekly_review_advice` | 금요일 저녁, 지난 7일 글에서 핵심 조언을 뽑아 회고한다. |

Suggested starting mix:

```text
workflow_observation: 22%
failed_agent_run: 18%
better_prompt_pattern: 16%
research_checklist: 18%
agent_role_split: 12%
tiny_source_case: 9%
weekly_review_advice: 5%
```

## Reusable Unit

Every chain must include at least one:

- practical `prompt`
- verification `checklist`
- role-specific AI agent instruction
- source-to-workflow template

Rotate labels:

```text
바로 써볼 프롬프트:
오늘 적용할 문장:
AI agent에게 이렇게 시켜보세요:
논문 읽을 때 붙여 넣을 문장:
다음 요약 전에 써볼 질문:
```

## Weekly Review Advice

Friday evening only:

1. Review the previous 7 days of posts.
2. Derive the strongest advice from the posts first.
3. Find a verified quote only if it genuinely matches.
4. Use Korean translation only.
5. Put quote source under `인용 원문:` in the final reply.
6. If no suitable quote exists, publish a general weekly review.

Do not start from a famous person and force the week into the quote.

## Source And Quote Rules

Use credible sources:

- arXiv or published papers
- official docs/blogs from AI tools
- original writing by named researchers
- GitHub repos or Korean technical posts that show actual workflow

Rules:

- Separate source facts from interpretation.
- GitHub stars are popularity signals only.
- Do not use generic product homepages as source replies.
- Famous-person quotes are optional and only from `data/verified-quotes.json`.
- No quote is better than a forced quote.

## Fingerprint Memory

Track repetition as state:

```text
format
human_signal_source
human_signal_type
workflow_stage
failure_mode
research_problem
hook_pattern
structure_pattern
closer_pattern
reusable_unit_type
```

Initial constraints:

- Same `format`: no more than twice in 7 days.
- Same `hook_pattern`: avoid reuse within 7 days.
- Same `closer_pattern`: avoid reuse within 14 days.
- `bad_request_good_request`: at most once per week.
- `weekly_review_advice`: Friday evening only.

## Self-Improvement Loop

Phase 1 uses a lightweight GenericAgent-style loop:

```text
generate -> evaluate -> publish/log -> propose learnings -> human promotion -> next generation
```

Persistent files:

- `docs/learnings.md`: short promoted rules injected near the top of future generation prompts.
- `skills_library/*.md`: crystallized reusable patterns from good runs.
- `daily-editor/runs/*.json`: full execution logs.
- `daily-editor/evaluations/*.eval.json`: evaluator critique logs.
- `daily-editor/proposals/*.md`: approval queue, not loaded by generation.
- `daily-editor/memory/*.md`: weak metrics memory, not a hard rule.

Do not let the agent rewrite prompts/code automatically yet. Proposal files must be reviewed before promotion.

## Success Criteria

- Posts feel like research-work judgments, not template-filled lessons.
- Each chain contains a reusable prompt, checklist, or agent instruction.
- Automatic posts remain honest about inferred context.
- The same hook, structure, and closer do not dominate a week.
- Friday review compresses the week's work into one useful research workflow lesson.
- Metrics guide weakly until enough 24h/72h data exists; views alone should not drive strategy.
