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
Reply 1: research workflow 기준/checklist
Reply 2: 예시 프롬프트
Reply 3: 참고해서 볼 만한 것들 + full URL + 적용법
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
"이 논문의 contribution을 3줄로 분리해줘"
"method가 무엇을 새로 바꿨는지 설명해줘"
"결과를 뒷받침하는 evidence만 따로 뽑아줘"
"저자가 인정한 limitation과 내가 의심해야 할 부분을 나눠줘"

논문 요약에서 AI는 압축기가 아니라
주장과 근거를 분리하는 독해 보조자여야 합니다.
---
실전에서는 논문 요약을 4칸으로 나눕니다.
1. Contribution: 무엇을 주장했나
2. Method: 어떻게 증명하려 했나
3. Evidence: 어떤 실험/표/그림이 받치나
4. Limitation: 어디까지 믿어야 하나
---
예시 프롬프트:
"이 논문을 요약하기 전에
contribution, method, evidence, limitation을 표로 나눠줘.
각 evidence는 논문의 figure, table, experiment 이름과 연결해줘.
마지막에 초록만 읽고는 알 수 없는 핵심을 따로 적어줘."
---
참고해서 볼 만한 것들:
Google NotebookLM
https://notebooklm.google/
- 적용: source-grounded 답변처럼, 요약도 원문 근거와 함께 요구하기
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

Use short quotes only, link the original, and always add `- 적용:`.

Useful sources to mine:

- Andrej Karpathy, A Survival Guide to a PhD
  https://karpathy.github.io/2016/09/07/phd/
- OpenAI Deep Research guide
  https://developers.openai.com/api/docs/guides/deep-research
- Anthropic context engineering
  https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Google NotebookLM
  https://notebooklm.google/
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
