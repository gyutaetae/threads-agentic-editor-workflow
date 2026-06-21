# Threads Channel Playbook

Single source of truth for `@arxiv.ai`.

## Account

`@arxiv.ai`는 AI로 논문을 읽고, 요약하고, 초안을 만들고, citation을 검증하는 연구 workflow 계정이다. 독자는 대학생, 대학원생, junior researcher, 논문을 읽어야 하는 개발자다.

Promise:

```text
매일 하나, 논문 작업을 덜 막막하게 만드는 AI research workflow.
```

Editorial thesis:

```text
AI로 논문을 잘 쓰는 사람은 "써줘"라고 하지 않는다.
읽기 -> 비교 -> 구조화 -> 초안 -> citation 검증 -> reviewer critique 흐름을 설계한다.
```

## Voice

- 한국어로 짧게 쓴다.
- academic/technical term은 원래 의미가 흐려질 때만 English로 둔다: `citation`, `evidence matrix`, `reviewer critique`, `agent`, `claim`, `limitation`.
- English term은 장식이 아니라 분류 정확도를 위해 최소한만 쓴다.
- 공장형 문장 금지: 같은 hook, 같은 4칸 이름, 같은 마무리를 반복하지 않는다.
- 강한 첫 문장은 허용하지만 근거 없는 `최고`, `무조건`, `혁명`, `이거 모르면 끝`은 금지한다.

## Content Pillars

1. Paper reading: contribution, method, evidence, limitation 추출
2. Literature review: 논문 나열을 evidence matrix로 바꾸기
3. Draft writing: problem-gap-contribution outline 먼저 만들기
4. Citation discipline: reference와 claim 연결 확인
5. Research agent architecture: reader, synthesizer, reviewer, editor 역할 분리

## Topic Filter

Pick topics that satisfy at least 3:

- vague AI request를 구체적인 research workflow로 바꾼다
- reader가 바로 복사해 쓸 prompt/framework가 있다
- source-grounded: paper, official docs, named researcher writing, useful repo
- comment를 부를 만한 disagreement, failure mode, example이 있다
- 이전 글과 다른 `failure_mode` 또는 `solution_pattern`이다

Block exact repeats:

- same source URL unless intentionally updating
- same `bad_request` with the same fix
- same `failure_mode` + same `solution_pattern`

## Format Router

There is no default 4-part chain. Pick the format that best fits the research problem, workflow stage, recent repetition history, and reusable unit.

Thread length:

- 1 to 4 parts are allowed.
- Every part must stay under 500 chars.
- Links belong in the final reply, not the main post.
- Do not use labels like `Main:` or `Reply 1:`.

Initial formats:

| Format | Use When |
|---|---|
| `workflow_observation` | A concrete judgment from AI-assisted paper work should open the post. |
| `failed_agent_run` | A common AI-agent failure needs to be shown and corrected. |
| `better_prompt_pattern` | A vague request should become a practical research prompt. |
| `research_checklist` | Readers need criteria to verify AI output. |
| `agent_role_split` | One broad task should be split into reader, synthesizer, critic, editor roles. |
| `tiny_source_case` | One paper, repo, or official doc should become a reusable workflow. |
| `weekly_review_advice` | Friday evening review of the previous 7 days. |

Every chain must include one reusable unit:

- practical `prompt`
- verification checklist
- role-specific AI agent instruction
- source-to-workflow template

Reusable reply labels should rotate:

```text
바로 써볼 프롬프트:
오늘 적용할 문장:
AI agent에게 이렇게 시켜보세요:
논문 읽을 때 붙여 넣을 문장:
다음 요약 전에 써볼 질문:
```

The old bad-request/good-request card is allowed only when `better_prompt_pattern` genuinely needs it.

## Human Signal

Posts should feel like a research-work judgment, not a template filled with research vocabulary.

Manual mode:

- A one-line user signal is enough.
- Turn it into a concrete research problem, practical derived questions, and one reusable unit.

Automatic mode:

- Infer only source surprise, reader friction, common confusion, verification need, or agent-workflow bottleneck.
- Do not invent personal experience.

Normalize each topic into:

```text
human_signal_type + workflow_stage + failure_mode
```

## Source Rules

Use credible sources:

- arXiv or published papers
- official docs/blogs from AI tools
- original writing by named researchers
- GitHub repos or Korean technical posts that show an actual workflow

Separate source facts from interpretation. GitHub stars are popularity, not quality. Do not use generic product homepages as references.

## Optional Quote/Image

Famous-person quotes are optional. Use at most one and only from `data/verified-quotes.json`.

Symbolic images are allowed when they help the hook. Prefer public-domain or clearly licensed images. Record `card_used=true` when an image is attached.

## Metadata

Keep these outside publishable text when available:

```text
series
series_part
public_theme
topic_pillar
workflow_stage
failure_mode
solution_pattern
bad_request
```

## Reaction Learning

Optimize for useful replies, saves, shares, follows, and template requests. Views alone are weak.

Useful comment labels:

```text
asks_for_prompt
asks_for_paper_summary_example
asks_for_literature_review_template
asks_for_citation_check
wants_deeper_research_agent
confused
disagrees
```
