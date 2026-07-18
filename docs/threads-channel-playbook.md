# Threads Channel Playbook

Single source of truth for `@arxiv.ai`. Keep this compact because generation agents load it as prompt context.

## North Star

`@arxiv.ai` helps Korean students, junior researchers, and developers turn papers into explainable research work.

Core promise:

```text
AI가 논문을 대신 읽어주는 계정이 아니라,
내가 설명할 수 있는 상태로 바꿔주는 계정.
```

Good posts start from a real paper-work failure and end with one reusable work artifact: prompt, checklist, table, protocol, matrix, role instruction, or revision rule. This is not an AI news, quote, or generic prompt account.

## Voice

- Korean first. Use English only when precision improves: `AI agent`, `claim`, `evidence`, `limitation`, `citation`, `reviewer critique`, `workflow`, `prompt`.
- Short, concrete, researcher-facing.
- Do not invent first-person experience in automatic mode.
- Ban hype: `무조건`, `혁명`, `논문 끝`, `역대급`, `미친 생산성`, `이거 모르면 뒤처집니다`.
- Separate source fact from account interpretation.
- Prefer recognizable concrete anchors when they make the workflow feel real: named venues, reviewer roles, named researchers, official docs, famous benchmarks, or widely respected examples. Use them to make the prompt more usable, not to borrow prestige.

## Topic Gate

Publish only when at least three are true:

- Vague AI request becomes a concrete research workflow.
- Reader gets a copyable prompt, checklist, agent instruction, or artifact template.
- Source is grounded: paper, official docs/blog, named researcher writing, useful repo, or Korean technical example.
- A real researcher failure mode is visible.
- Recent history differs in `failure_mode`, `artifact_type`, `hook_pattern`, or `reusable_unit_type`.
- A generic AI tip is converted into a concrete paper-writing context, such as `ICML soundness`, `ACL related work`, `AC decision risk`, `OpenAI Evals`, or another recognizable anchor.

Block when:

- Same source URL is reused without a new angle.
- Same `bad_request` and same fix repeat.
- Same `failure_mode` + same `artifact_type` repeat.
- Source fact and @arxiv.ai interpretation are mixed.

## Artifact Router

Every post owns exactly one research-work artifact. The artifact is what the reader can make after reading.

| failure_mode | artifact_type | reader-test hook |
|---|---|---|
| `false_fluency` | `summary_verification_grid` | 내가 claim/method/evidence/limitation을 설명 못하면 |
| `claim_reference_mismatch` | `citation_support_table` | 내가 citation이 어느 claim을 받치는지 설명 못하면 |
| `claim_evidence_link_missing` | `claim_evidence_map` | 내가 claim을 어떤 실험/표/그림이 받치는지 설명 못하면 |
| `method_steps_not_reproducible` | `reproducibility_protocol` | 내가 method를 재현 순서로 설명 못하면 |
| `comparison_axis_missing` | `literature_comparison_matrix` | 내가 논문 간 차이를 같은 축으로 설명 못하면 |
| `argument_structure_missing` | `problem_gap_contribution_outline` | 내가 problem-gap-contribution을 설명 못하면 |
| `revision_without_rule` | `revision_rule_diff` | 내가 수정 이유를 다음 초안 규칙으로 설명 못하면 |
| `weakness_not_prechecked` | `reviewer_risk_checklist` | 내가 reviewer가 물을 약점을 설명 못하면 |
| `roles_collapsed_into_one_agent` | `agent_role_instruction` | 내가 reader/critic/editor 역할을 나눠 설명 못하면 |

Failure judgment examples:

```text
그건 요약이 아니라 대리 독서입니다.
그건 이해가 아니라 성능 점수 신뢰입니다.
그건 방법론 이해가 아니라 방법론 복사입니다.
그건 검증이 아니라 참고문헌 장식입니다.
그건 literature review가 아니라 논문 목록 정리입니다.
그건 초안 작성이 아니라 문장 생산입니다.
```

Operational rule: if a recent post shares the same broad hook, Part 1 must start from the artifact-specific reader test.

## Explainable Reading Template

Use this compact main-post template for every manual and automatic draft. Rotate the topic, failure, example requests, and judgment—not the skeleton.

```text
AI에게 [research task]를 시킬 때 [vague instruction]이라고 하면 [concrete failure]가 생깁니다.

나쁜 요청:
"..."

좋은 요청:
"..."
"..."
"..."
"..." (optional fourth line)

[Agent/workflow]는 [잘못 기대한 역할]이 아니라
[실제로 맡길 역할]입니다.
```

The labels are exactly `나쁜 요청:` and `좋은 요청:`. Use one standalone quoted bad request, three or four standalone quoted good requests, and a short judgment closer. Keep the main post under 500 characters and link-free.

When writing examples, prefer concrete anchors over generic roles:

```text
Weak:
"리뷰어처럼 평가해줘."

Stronger:
"ICML 기준으로 soundness를 흔들 반례 질문을 써줘."
"AC가 볼 때 치명적인 약점을 우선순위로 표시해줘."
"표현 지적과 reject 근거가 될 구조적 약점을 나눠줘."
```

The anchor can be a venue, role, named person, benchmark, paper type, official rubric, or famous workflow. Keep the post broadly useful for people writing papers with AI; do not make it insider-only.

## Thread Contract

Exactly 4 parts, each under 500 chars:

1. Canonical main post: problem hook -> `나쁜 요청:` 1 quoted line -> `좋은 요청:` 3-4 quoted lines -> short judgment closer. No source link.
2. Diagnosis: 3 concrete checks or criteria tied to the artifact.
3. Reusable action: copyable prompt, checklist, protocol, matrix, or role instruction.
4. Source interpretation: URL + `- 볼 부분:` or `인용 원문:` + source fact vs `[나의 견해]`.

Allowed formats change the emphasis of Parts 2-4, not the main-post skeleton:

| format | emphasis |
|---|---|
| `workflow_observation` | Part 1 judgment |
| `failed_agent_run` | Part 1 failure scene + Part 3 correction |
| `better_prompt_pattern` | Part 2 diagnosis + Part 3 reusable version of the better request |
| `research_checklist` | Part 2 checks |
| `agent_role_split` | Part 3 role instruction |
| `tiny_source_case` | Part 4 source fact vs interpretation |
| `weekly_review_advice` | Friday evening only, advice from last 7 days |

Do not use drafting labels like `Main:` or `Reply 1:`. Avoid repeated generic `[핵심 한 줄]`.

## Source Rules

Use credible sources: arXiv/papers, official docs/blogs, original researcher writing, useful repos, Korean workflow examples.

- Main post has no links.
- Final reply explains why the source belongs with `- 볼 부분:`.
- GitHub stars are popularity only.
- Famous quotes are optional and only from `data/verified-quotes.json`; no quote is better than a forced quote.

## Fingerprint Memory

Track repetition through:

```text
format
human_signal_type
workflow_stage
failure_mode
research_problem
artifact_type
hook_pattern
structure_pattern
closer_pattern
reusable_unit_type
```

Constraints:

- Same `hook_pattern`: avoid within 7 days.
- Same `closer_pattern`: avoid within 14 days.
- Same `failure_mode` + same `artifact_type`: reject or change artifact.
- `weekly_review_advice`: Friday evening only.

## Learning Loop

Generation loop:

```text
generate -> evaluate -> publish/log -> propose learnings -> human promotion -> next generation
```

Human revision loop:

```text
ai-draft.txt -> user-revision.txt -> diff.json -> preference.proposed.md -> docs/learnings.md after repeated evidence
```

Files:

- `docs/learnings.md`: short promoted rules loaded near the top of prompts.
- `docs/thread-pattern-library.md`: crystallized reusable patterns.
- `daily-editor/runs/*.json`, `daily-editor/evaluations/*.eval.json`: execution evidence.
- `daily-editor/curation/codex-curation-log.jsonl`: human/Codex editorial judgment.
- `daily-editor/proposals/*.md`: approval queue, not automatic truth.

Promote only durable preferences. Do not promote one-off wording unless it reveals a repeated pattern.

## Success Criteria

- Post feels like a research-work judgment, not a template lesson.
- Reader can explain one paper-work artifact after reading.
- Source fact and account interpretation stay separate.
- Recent hook, artifact, structure, and closer do not dominate a week.
