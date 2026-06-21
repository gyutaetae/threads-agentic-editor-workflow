# ADR: Threads Editorial Harness Decisions

## Status

Accepted as current editorial architecture for `@arxiv.ai`.

## Context

Recent posts leaned too heavily on a fixed teaching-card structure: strong hook, bad request, good requests, bracketed replies, prompt pack, source reply. That shape is useful sometimes, but repeated use makes posts feel automated even when the topic is useful.

The account should instead show how a researcher can use AI agents to make paper work more concrete, verifiable, and reusable.

## Decision 1: Replace Default Chain With Format Router

Use a `format router` instead of one always-on 4-part chain.

The router chooses among:

- `workflow_observation`
- `failed_agent_run`
- `better_prompt_pattern`
- `research_checklist`
- `agent_role_split`
- `tiny_source_case`
- `weekly_review_advice`

Selection considers:

- `human_signal_type`
- `workflow_stage`
- `failure_mode`
- recent format fingerprints
- required reusable unit

### Rationale

A fixed structure optimizes consistency but creates sameness. A router preserves utility while making posts feel authored and adapted to the research problem.

### Consequences

- Chain length is flexible: one post, main plus one reply, or longer chains are allowed.
- The old bad-request/good-request pattern becomes one occasional tactic, not the default.
- Drafting tools must record fingerprints so variety is enforceable.

## Decision 2: Require A Reusable Unit In Every Chain

Every chain must include at least one directly reusable unit:

- practical `prompt`
- verification `checklist`
- role-specific AI agent instruction
- short source-to-workflow template

### Rationale

The account should be worth saving, reposting, and following. Posts that only make an interesting point do not satisfy the channel goal unless they also help readers do the work.

### Consequences

- Even observation-style posts need a practical reply.
- Drafting should produce work instructions, not only commentary.
- Reusable reply labels should rotate to avoid becoming another template.

## Decision 3: Treat Human Signal As Editorial State

Represent authorial judgment with `human_signal`.

Manual input can be one line from the user. Automatic mode may infer a signal from sources or workflow bottlenecks, but must not fabricate personal experience.

Persist:

```text
human_signal_source
human_signal_type
workflow_stage
failure_mode
research_problem
```

### Rationale

Posts need visible judgment. The right way to add it is not generic "humanizing" language but a concrete research problem, doubt, verification need, or workflow bottleneck.

### Consequences

- Manual posts can be seeded with a short Korean note.
- Automatic posts must avoid first-person claims such as "직접 해봤다" unless provided by the user.
- Future scoring can compare user-provided and inferred signals.

## Decision 4: Classify Problems Before Drafting

Classify inputs into:

```text
human_signal_type + workflow_stage + failure_mode
```

Initial `human_signal_type` set:

- `summary_suspicion`
- `citation_doubt`
- `literature_overload`
- `draft_without_argument`
- `evidence_missing`
- `agent_role_confusion`
- `reviewer_anxiety`
- `method_understanding_gap`

Derived questions must be practical:

- diagnostic question
- verification question
- next-action question

### Rationale

Classification keeps the system focused on real research problems instead of drifting into abstract commentary. It also makes routing and repetition control more reliable.

### Consequences

- Prompts can be selected based on the problem type.
- Fingerprints become comparable across posts.
- The taxonomy should stay small until real content history shows missing categories.

## Decision 5: Weekly Review Advice Runs Friday Evening

`weekly_review_advice` runs on Friday evening.

Process:

1. Review the previous 7 days of posts.
2. Extract the strongest advice from the actual posts.
3. Find a verified quote that matches the advice.
4. Use the Korean translation only.
5. Put the quote source in the last reply.
6. If no suitable quote exists, publish a general weekly review.

### Rationale

The advice should come from the week's work, not from a preselected famous person. This prevents the account from becoming a quote account and keeps the conclusion grounded in the channel's research workflow.

### Consequences

- Famous people are chosen only when their verified quote fits the derived advice.
- Korean-recognizable figures may be preferred when equally suitable.
- No quote is better than a forced quote.

## Decision 6: Keep Language Mostly Korean

Use Korean for names and general prose. Keep English only where Korean loses technical precision.

Examples:

- Use Korean names: 안드레이 카파시, 젠슨 황, 리사 수, 샘 올트먼, 다리오 아모데이.
- Keep technical terms when useful: `AI agent`, `claim`, `evidence`, `limitation`, `citation`, `reviewer critique`, `workflow`, `prompt`.

### Rationale

The channel is Korean-first, but some research workflow terms are clearer in English.

### Consequences

- Quote text in weekly review is Korean translation only.
- Source links still appear in the final reply.
- English should not be used as decoration.

## Decision 7: Optimize Later, Log Now

Do not overfit to early metrics yet. For now, record enough data to support later learning.

Minimum logging:

- post metadata
- format
- human signal fields
- fingerprint fields
- reusable unit type
- source and quote source if used
- publish metrics when available

### Rationale

The account does not yet have enough stable data for metric-driven optimization. Good logs now will make later decisions credible.

### Consequences

- Success metrics are acknowledged but not the primary routing input yet.
- Future iterations can connect saves, reposts, follows, and comments to formats and problem types.
- Views alone should not drive strategy.

## Decision 8: Add Phase 1 Self-Improvement Loop

Adopt a lightweight GenericAgent-style loop without installing an external framework.

The generation pipeline now records:

- writer prompt and raw model output
- context files and recent history used
- final thread text
- evaluator prompt and evaluator result
- routing and fingerprint metadata

Persistent learning is split by purpose:

- `docs/learnings.md`: compact rules injected near the top of future generation prompts.
- `skills_library/*.md`: crystallized reusable patterns from good runs.
- `daily-editor/runs/*.json`: full execution logs for audit.
- `daily-editor/evaluations/*.eval.json`: evaluator-agent critique logs.

### Rationale

The account needs an improvement loop, but it is too early to let an agent modify code or prompts automatically. Capturing high-quality trajectories and evaluator feedback creates the data needed for later self-improving-agent style PR suggestions.

### Consequences

- Future runs can learn from prior successes without loading every raw log.
- Evaluator output is advisory in phase 1; it records critique but does not automatically rewrite code.
- Phase 2 may add diff/PR suggestions once enough run and evaluation data exists.

## Non-Decisions

- No final implementation choice has been made for LangGraph, Promptfoo, Langfuse, or other orchestration tools.
- No automated metric-weighting model is defined yet.
- No quote database expansion policy is defined beyond requiring verified sources.
- No automatic self-editing PR loop is enabled yet.
