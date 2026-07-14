# Thread Pattern Library

Durable reusable patterns for `@arxiv.ai` generation. This file is loaded by the automatic generator as pattern context. Keep it compact and promote only patterns that repeatedly help publishable posts.

## How Patterns Are Promoted

Human edits are not automatically saved here. The loop is:

```text
draft -> user revision -> run/evaluation evidence -> proposal -> human promotion -> this file
```

Automatic proposal files live in `daily-editor/proposals/`. They are not generation rules until a human promotes the useful part into this file or `docs/learnings.md`.

Promote a pattern here when:

- it solves a repeatable paper-work failure,
- it gives a reusable prompt, checklist, table, matrix, protocol, role instruction, or revision rule,
- it does not force one fixed post template,
- it keeps source facts separate from @arxiv.ai interpretation.

## Cross-Pattern Rule: Concrete Anchors

Use this rule inside existing patterns; do not create a separate post format just to use a famous name.

Strong posts often turn a generic AI instruction into a concrete paper-writing situation by naming a recognizable anchor:

- venue or review context: `ICML`, `NeurIPS`, `ACL`, `reviewer`, `AC`, `camera-ready`
- paper type: `method paper`, `benchmark paper`, `survey`, `system paper`, `LLM eval`
- evaluation criterion: `soundness`, `novelty`, `ablation`, `baseline`, `citation support`
- respected source: official docs, reviewer instructions, named researcher writing, widely used benchmark or eval framework

The anchor should make the prompt more usable:

```text
Weak:
"리뷰어처럼 평가해줘."

Better:
"ICML 기준으로 soundness를 흔들 반례 질문을 써줘."
"AC가 볼 때 치명적인 약점을 우선순위로 표시해줘."
"표현 지적과 reject 근거가 될 구조적 약점을 나눠줘."
```

Avoid name-dropping. If the anchor does not change the reader's next action, remove it.

## Citation Verification

Use when `human_signal_type` is `citation_doubt` or `workflow_stage` is `citation_verification`.

Research problem:

```text
AI-generated citations can look safe because they are formatted cleanly. The real question is whether each citation directly supports the claim.
```

Strong shape:

1. Open with the false-safety problem: a citation exists, but support is unverified.
2. Separate existence, relevance, source location, and support strength.
3. Give a reusable prompt that asks for a claim-citation-evidence table.
4. Put source links in the final reply with `- 볼 부분:`.

Reusable prompt pattern:

```text
아래 초안의 모든 claim을 표로 뽑아줘.
각 claim마다 연결된 citation, 근거 위치, 근거 강도를 표시해줘.
citation이 claim을 직접 지지하지 않으면 '검증 필요'로 표시해줘.
존재 여부와 claim 지지 여부를 분리해서 판단해줘.
```

Fingerprint:

- `human_signal_type`: `citation_doubt`
- `workflow_stage`: `citation_verification`
- `failure_mode`: `claim_reference_mismatch`
- `reusable_unit_type`: `verification_checklist`

## Thread Evaluation

Use after a draft is produced.

Evaluate for:

- Does the draft solve a real research workflow problem?
- Is there a reusable prompt, checklist, agent instruction, or workflow template?
- Are source facts separated from account interpretation?
- Does the draft avoid invented personal experience?
- Does it avoid recent hook, structure, and closer repetition?
- Would a researcher save or repost it because it helps with paper work?

Scoring:

- `90-100`: publishable with minor copy edits.
- `75-89`: useful, but revise hook, reusable unit, or source framing.
- `0-74`: do not publish without rewriting.

Learning rule:

```text
Only promote a lesson into docs/learnings.md or this file when it is durable and likely to improve future runs.
Keep raw evidence in daily-editor/runs/*.json and daily-editor/evaluations/*.eval.json.
```
