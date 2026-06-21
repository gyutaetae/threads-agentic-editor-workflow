# PRD: Authored Research Workflow Threads

## Product Goal

`@arxiv.ai` should become a Korean Threads account that researchers save, repost, and follow because it gives reusable ways to use AI agents in paper work.

The account is not an AI news, quote, or generic prompt account. Its core promise is:

```text
AI agent로 논문 읽기, 요약, 리서치 정리, 초안 작성, citation 검증을 더 검증 가능한 작업 단위로 바꾼다.
```

## Audience

- 대학생, 대학원생, junior researcher
- 논문을 읽거나 써야 하는 개발자
- AI로 research workflow를 자동화하려는 사람

They need practical help with:

- 논문 요약이 실제 이해로 이어졌는지 확인하기
- 여러 논문을 비교 가능한 기준으로 정리하기
- 초안을 problem-gap-contribution 구조로 만들기
- `claim`, `evidence`, `limitation`, `citation` 연결 확인하기
- 하나의 AI agent에게 모든 일을 맡기지 않고 역할을 나누기

## Product Principles

1. 실제 연구자가 겪을 법한 문제에서 시작한다.
2. 철학적 질문보다 작업 가능한 질문으로 바꾼다.
3. 모든 글에는 저장할 만한 재사용 단위가 있어야 한다.
4. 자동화된 글도 실제 경험을 꾸며내지 않는다.
5. 같은 hook, 구조, 마무리, 수사법을 반복하지 않는다.
6. 유명인 포맷은 주간 회고용이며 명언 계정처럼 쓰지 않는다.

## Reusable Unit Requirement

Every published chain must include at least one reusable unit:

- 적용 가능한 `prompt`
- 검증 `checklist`
- 역할별 AI agent 지시문
- source를 연구 작업에 적용하는 짧은 workflow

Reusable replies may use varied labels to avoid template fatigue:

```text
바로 써볼 프롬프트:
오늘 적용할 문장:
AI agent에게 이렇게 시켜보세요:
논문 읽을 때 붙여 넣을 문장:
다음 요약 전에 써볼 질문:
```

## Human Signal

`human_signal` is the visible trace of judgment that prevents posts from feeling like filled templates.

Manual mode:

- The user may provide one line, such as `논문 요약이 너무 깔끔해서 오히려 의심됐음`.
- The system turns it into a concrete research problem, derives practical questions, chooses a format, and writes the chain.

Automatic mode:

- The system may infer a `human_signal` from a source, topic, or workflow bottleneck.
- It must not invent first-person experiences, emotions, or claims that the user personally tried something.

Allowed automatic signals:

- source에서 예상과 달랐던 점
- reader가 막힐 만한 지점
- 흔한 착각
- 검증이 필요한 지점
- agent workflow상 병목

## Problem Classification

User input and automatic topics should be normalized into:

```text
human_signal_type + workflow_stage + failure_mode
```

Initial `human_signal_type` values:

| Type | Research Problem |
|---|---|
| `summary_suspicion` | AI 요약이 깔끔하지만 실제 이해로 이어졌는지 의심됨 |
| `citation_doubt` | `citation`이 `claim`을 실제로 받치는지 불안함 |
| `literature_overload` | 논문은 많지만 비교 기준이 없어 정리가 안 됨 |
| `draft_without_argument` | 초안은 나왔지만 problem-gap-contribution 논리가 약함 |
| `evidence_missing` | 주장은 있지만 `evidence`가 표, 그림, 실험, 데이터와 연결되지 않음 |
| `agent_role_confusion` | 하나의 AI agent에게 읽기, 비교, 비판, 작성을 다 맡겨 결과가 흐려짐 |
| `reviewer_anxiety` | reviewer가 물을 약점, 반박, `limitation`을 미리 찾지 못함 |
| `method_understanding_gap` | 방법론을 요약했지만 재현 가능한 단계로 설명하지 못함 |

Derived questions should be split into:

- 진단 질문: 문제가 무엇인지 확인한다.
- 검증 질문: AI 결과가 맞는지 확인한다.
- 다음 행동 질문: AI agent에게 무엇을 시킬지 정한다.

## Format Router

There is no default 4-part chain. The system chooses a format based on the research problem, workflow stage, recent fingerprint history, and required reusable unit.

Initial formats:

| Format | Role |
|---|---|
| `workflow_observation` | AI 논문 작업에서 생긴 판단을 짧게 보여준다. |
| `failed_agent_run` | AI agent에게 잘못 맡겼을 때 무엇이 무너지는지 보여준다. |
| `better_prompt_pattern` | 모호한 요청을 구체적인 research prompt로 바꾼다. |
| `research_checklist` | AI 결과물을 사람이 검증할 기준을 준다. |
| `agent_role_split` | reader, synthesizer, critic, editor처럼 agent 역할을 나눈다. |
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

## Weekly Review Advice

Every Friday evening, review the previous 7 days of posts:

1. Find the repeated research problem.
2. Derive the most useful advice from the posts.
3. Search for a verified quote that genuinely matches the advice.
4. If a quote exists, use only the Korean translation and include the source in the last reply.
5. If no suitable quote exists, publish a general weekly review without a famous person.

The person is selected after the advice is known. Do not start from a famous person and force the week into that person's quote.

## Fingerprint Memory

Track repetition as state, not as a feeling.

Minimum fingerprint fields:

```json
{
  "format": "workflow_observation",
  "human_signal_source": "user",
  "human_signal_type": "summary_suspicion",
  "workflow_stage": "summary_verification",
  "failure_mode": "false_fluency",
  "research_problem": "AI 요약이 실제 이해를 만들었는지 검증하기 어렵다",
  "hook_pattern": "clean_output_suspicion",
  "structure_pattern": "observation_to_verification",
  "closer_pattern": "verification_question",
  "reusable_unit_type": "applicable_prompt"
}
```

Initial repetition constraints:

- Same `format`: no more than twice in 7 days.
- Same `hook_pattern`: avoid reuse within 7 days.
- Same `closer_pattern`: avoid reuse within 14 days.
- `bad_request_good_request`: at most once per week.
- `weekly_review_advice`: Friday evening only.

## Scope

In scope:

- Drafting and approving Threads chains for `@arxiv.ai`
- Generating manual or automatic `human_signal`
- Routing formats without a fixed 4-part template
- Keeping source-backed claims and quote sources
- Logging fingerprints for repetition control
- Recording publish and reaction data for later learning

Out of scope for this phase:

- Optimizing based on metrics before enough data exists
- Turning the account into AI news, motivational quotes, or celebrity commentary
- Publishing unverified quotes
- Inventing personal experiences for automatic posts
- Adding broad automation unrelated to research workflow

## Success Criteria

- Posts feel like research-work judgments, not template-filled lessons.
- Each chain contains a reusable prompt, checklist, or agent instruction.
- The same structure, hook, and closer do not dominate a week.
- Manual `human_signal` input can be one line and still produce a practical chain.
- Automatic posts remain honest about inferred context.
- Friday review compresses the week's work into one useful research workflow lesson.
