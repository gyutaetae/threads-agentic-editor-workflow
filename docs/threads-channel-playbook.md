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

## Default Chain

Exactly 4 parts: main + 3 replies. Each part must stay under 500 chars.

```text
Main: 강한 hook + 나쁜 요청 1개 + 번호 없는 좋은 요청 4개 + 원칙 문장
Reply 1: [핵심 한 줄] + "실전에서는 ..." + 4-item framework
Reply 2: [핵심 한 줄] + 예시 프롬프트 4개
Reply 3: [핵심 한 줄] + 참고 링크 + 볼 부분
```

Main should work as the scroll-stopper. The first post may carry a symbolic person image when it strengthens the idea. The image is context, not proof.

Reply rule:

- Every reply starts with `[핵심 한 줄]`.
- Then explain the point in plain Korean.
- Do not use labels like `Reply 1:`.

## Proven Shape

```text
AI에게 논문 요약을 맡길 때
"이 논문 요약해줘"라고 쓰면
초록을 다시 쓴 글이 나올 가능성이 큽니다.

나쁜 요청:
"이 논문 요약해줘"

좋은 요청:
"핵심 기여를 기존 연구와 분리해줘"
"방법을 재현 가능한 단계로 나눠줘"
"주장을 받치는 표, 그림, 실험을 연결해줘"
"저자가 말한 한계와 내가 의심할 점을 분리해줘"

좋은 요약은 짧은 글이 아니라
검증 가능한 연구 노트입니다.
---
[논문 요약은 4칸으로 나눕니다]
실전에서는 논문 요약을 4칸으로 나눕니다.
1. Contribution: 무엇을 주장했나
2. Method: 어떻게 증명하려 했나
3. Evidence: 어떤 실험/표/그림이 받치나
4. Limitation: 어디까지 믿어야 하나
---
[복사해서 쓸 프롬프트]
예시 프롬프트:
"..."
"..."
"..."
"..."
---
[볼 부분이 있는 링크만 남깁니다]
참고해서 볼 만한 것들:
source title
https://...
- 볼 부분: ...
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
