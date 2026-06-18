# Threads Channel Playbook

Single source of truth for `@gyu_in_black`.

## Positioning

```text
자체구축 AI 에이전트로 논문을 읽고 쓰는 대학생 개발자
```

Promise:

```text
연구자와 대학생을 위한 AI 논문 작업법.
프롬프트가 아니라 읽기, 요약, 레퍼런스, 초안, 검증 흐름을 설계한다.
```

Target reader:

```text
논문을 읽고 정리하고 써야 하는 대학생, 대학원생, junior researcher.
ChatGPT, Claude, NotebookLM, Elicit, Deep Research를 쓰지만 결과를 어떻게 검증할지 불안한 사람.
```

Editorial thesis:

```text
AI로 논문을 잘 쓰는 사람은 "써줘"라고 하지 않는다.
읽기 -> 비교 -> 구조화 -> 초안 -> citation 검증 -> reviewer critique 흐름을 설계한다.
```

## Topic Filter

Pick topics that satisfy at least 3 of 5:

- helps a researcher read, summarize, compare, draft, cite, or review papers
- turns a vague AI request into a concrete research workflow
- can become a checklist, prompt template, evidence matrix, or bad-vs-good example
- uses credible sources: papers, official docs, named expert posts, research tools
- teaches a reusable agent architecture: reader, synthesizer, reviewer, editor

Prefer:

- 논문 요약, literature review, evidence matrix, related work, 초안 구조, reference 검증
- source-grounded workflow over tool news
- concrete prompts and review criteria over generic AI productivity advice
- famous-person or official-source lessons only when they become a workflow readers can copy

Avoid:

- generic AI news summaries
- fake guru tone
- unverifiable "최고", "무조건", "혁명" claims
- AI가 논문을 대신 써준다는 식의 과장
- source names without full URLs

## Series Strategy

Primary series:

```text
AI로 논문 쓰는 법
```

Use the series internally for planning and history, but keep the public first line natural unless the post benefits from a visible series label.

Default first arc:

1. 논문 요약 자동화
2. Related Work 자동화
3. Evidence Matrix 만들기
4. AI로 논문 초안 쓰기
5. Citation 검증 자동화
6. 연구자를 위한 AI Agent

Strong public themes to rotate:

- AI로 논문 쓰는 법
- 연구자를 위한 AI Agent
- 논문 읽기 자동화
- Literature Review 프롬프트
- Evidence Matrix 템플릿
- Citation mismatch 찾는 법
- AI Reviewer 만드는 법

Do not repeat the old winning angle too closely:

```text
만약 AI에게 논문을 써달라고 하면...
"이 주제에 대해 서론만 써줘"
```

The topic may return to paper drafting, but the solution must be different: evidence matrix before drafting, problem-gap-contribution outline, reviewer critique, or citation alignment.

## Novelty Rules

Track every post by topic fingerprint:

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

Block exact repeats:

- same `failure_mode` + same `solution_pattern`
- same `bad_request` with the same practical fix
- same source URL/name unless intentionally updating an older post

Allow useful variation:

- same `topic_pillar` with a different `workflow_stage`
- same broad theme with a different failure mode
- same tool/source with a different research workflow lesson

Series rule:

- If a post overlaps with a prior topic, make it an explicit next step in the workflow.
- Keep continuity in the internal metadata, not necessarily in the public first line.
- A series post must still stand alone for readers seeing it first.

## Content Pillars

1. Paper reading
   - contribution, method, evidence, limitation 추출
   - figure/table/ablation 중심 요약
   - claims vs evidence 표

2. Literature review
   - research question별 evidence matrix
   - related work를 논문 나열이 아니라 차이의 지도로 만들기
   - survey paragraph 구조 분해

3. Draft writing
   - problem-gap-contribution-outline
   - 초안 작성 agent와 비판 agent 분리
   - 문체보다 claim order 먼저 검증

4. Citation discipline
   - DOI/title/author/venue/year 확인
   - AI가 만든 reference를 그대로 믿지 않기
   - 각 문단의 주장과 근거 연결 확인

5. Research agent architecture
   - Reader: paper에서 claim/evidence/limitation 추출
   - Synthesizer: 여러 논문의 공통점과 차이 정리
   - Reviewer: 초안의 과장, 빈 근거, citation mismatch 찾기
   - Editor: 문장 다듬기만 담당

## Thread Rules

- Automated chain: exactly 4 parts, main + 3 replies.
- Each part must stay under 500 characters.
- Main should usually stay under 350 Korean characters.
- Use one useful idea per thread.
- Split long ideas into follow-up posts.

Default chain:

```text
Main: natural or 만약형 hook + 나쁜 요청 1개 + 좋은 요청 4개 + plain principle
Reply 1: 좋은 요청 4개가 각각 좋은 이유 + 실제 활용 시점
Reply 2: 좋은 요청 4개에 대응하는 복사 가능한 예시 프롬프트
Reply 3: 오늘 주제와 직접 연결되는 한국어 기술 블로그/GitHub 사례 + full URL + 볼 부분
```

Do not publish these labels:

```text
Reply 1:
Reply 2:
Reply 3:
[한 줄 원칙:]
한 줄 원칙:
[초안 작성 모드]
```

Do not use JSON or fenced code blocks for prompt examples. Use natural quoted Korean instructions.

## Proven Format

```text
AI에게 논문 요약을 맡길 때
"이 논문 요약해줘"라고 쓰면
초록을 다시 쓴 글이 나올 가능성이 큽니다.

나쁜 요청:
"이 논문 요약해줘"

좋은 요청:
"1. 이 논문의 핵심 기여를 3개로 분리해줘"
"2. 기존 방법과 비교해 무엇을 바꿨는지 설명해줘"
"3. 주장을 뒷받침하는 표·그림·실험을 연결해줘"
"4. 저자가 밝힌 한계와 추가로 의심할 점을 나눠줘"

좋은 요약은 짧은 글이 아니라
주장·근거·한계를 다시 확인할 수 있는 연구 노트입니다.
---
왜 좋은 요청일까요?
1. 핵심 기여를 분리하면 배경 설명과 저자의 새 주장을 혼동하지 않습니다.
- 활용: 읽을 논문 선별, related work 후보 정리
2. 기존 방법과의 차이를 물으면 실제 변화점을 찾습니다.
- 활용: 구현 범위와 재현 포인트 확인
3. 주장과 표·그림·실험을 연결하면 원문에서 검증할 수 있습니다.
- 활용: 발표 자료와 인용 전 사실 확인
4. 명시된 한계와 추가 의문을 나누면 사실과 AI의 해석이 섞이지 않습니다.
- 활용: 후속 연구 질문과 리뷰 의견 만들기
---
예시 프롬프트:
"핵심 기여 3개를 문제-제안-효과 형식으로 써줘. 각 항목의 근거 위치도 표시해줘."
"기존 방법과 제안 방법을 입력, 구조, 학습, 비용 기준으로 비교표로 만들어줘."
"주요 주장마다 근거가 되는 Figure, Table, Experiment와 핵심 수치를 연결해줘."
"저자가 밝힌 한계와 실험 설계상 추가로 의심할 점을 분리하고, 후자는 AI의 해석이라고 표시해줘."
---
참고해서 볼 만한 것들:
AI 논문 요약의 맹점과 도구별 결과 비교
https://blog.naver.com/crazibiza/223976153740
- 볼 부분: 요약에서 누락된 분석과 후속 질문을 비교하는 방식
딥러닝 논문 리뷰·요약·코드 실습 저장소
https://github.com/gagyeomkim/Deep-Learning-Paper-Review-and-Practice
- 볼 부분: 원문을 리뷰, 요약 PDF, 코드 실습으로 이어가는 기록 구조
```

## Hook Rules

Good hooks:

- `AI에게 논문 요약을 맡길 때 "요약해줘"라고 쓰면 제일 중요한 근거가 빠집니다.`
- `만약 AI에게 related work를 써달라고 하고 있다면, 논문을 나열하게 만들고 있는 겁니다.`
- `논문 초안에서 AI를 작가로 쓰면 문장은 좋아지지만 근거 추적이 약해집니다.`

Hook formula:

1. Name a common research-AI mistake.
2. Show why the output becomes hard to trust.
3. Replace it with a workflow: read, compare, draft, verify.

## Source Rules

Use primary or credible sources:

- official docs/blogs from OpenAI, Anthropic, Google, tool makers
- arXiv or published papers
- original writing by named researchers, e.g. Andrej Karpathy
- official docs for research tools such as NotebookLM, Elicit, Zotero, Semantic Scholar

Separate:

- Source facts: what the source directly says.
- Our interpretation: how to turn it into a research workflow.

Use short quotes only and link the original. For the final reply, prefer an actual
Korean article or GitHub repository that demonstrates today's workflow. Add
`- 볼 부분:` so the reader knows what to inspect and reuse. Do not substitute a
generic product homepage for an example.

## Optional Quote Policy

Famous-person quotes are optional. The post must remain complete when the quote is removed.

Use a quote only when:

- it is present in `data/verified-quotes.json`
- its relevance score is at least 8
- the exact Korean text and verified primary-source URL are available
- no quote was used in the previous 3 published posts
- it directly strengthens the workflow lesson rather than decorating the hook

Use no more than one quote per chain. Keep Korean technical blogs and GitHub repositories
as the practical references. If a verified quote is used, add its non-Korean primary
source separately under `인용 원문:`.

Default to no quote when the fit is ambiguous.

Useful sources to mine:

- Korean technical blogs that show a paper review or research workflow
- Korean GitHub repositories that connect the original paper to notes, summaries, or code
- Andrej Karpathy, A Survival Guide to a PhD
  https://karpathy.github.io/2016/09/07/phd/
- OpenAI Deep Research guide
  https://developers.openai.com/api/docs/guides/deep-research
- Anthropic context engineering
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Elicit
  https://elicit.com/

## Reaction Learning

Optimize for research usefulness, not views alone:

```text
save_rate + reply_rate + follow_rate + asks_for_template + asks_for_example
```

Comment labels:

```text
asks_for_prompt
asks_for_paper_summary_example
asks_for_literature_review_template
asks_for_citation_check
wants_deeper_research_agent
confused
disagrees
```

Turn signals into decisions:

- `asks_for_prompt` -> next post is a copyable prompt.
- `asks_for_paper_summary_example` -> show one paper teardown.
- `asks_for_literature_review_template` -> make an evidence matrix post.
- `asks_for_citation_check` -> write reference verification workflow.
- `wants_deeper_research_agent` -> explain reader/synthesizer/reviewer/editor split.
