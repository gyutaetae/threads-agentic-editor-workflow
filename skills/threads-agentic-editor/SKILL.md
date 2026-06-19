---
name: threads-agentic-editor
description: "Use when drafting, scoring, reviewing, or analyzing @arxiv.ai Threads posts about AI research workflows: paper reading, literature review, evidence matrices, paper drafts, citation checks, reviewer critique, and research agent architecture."
---

# Threads Agentic Editor

## Mission

Create useful Threads chains for `@arxiv.ai`: a Korean account about using AI to read papers, summarize evidence, draft research text, verify citation links, and design small research-agent workflows.

Use `docs/threads-channel-playbook.md` as the source of truth for concept, tone, topic fit, chain shape, source rules, and reaction learning. Do not duplicate that strategy here.

## Workflow

1. Read `docs/threads-channel-playbook.md`.
2. Check recent `content-history.jsonl` entries before picking a topic.
3. Pick sources from papers, official docs/blogs, named researcher writing, useful repos, or Korean technical posts with actual workflow detail.
4. Score candidates by research utility, source authority, practical workflow value, novelty, save value, and reply potential.
5. Draft two options only when useful:
   - A: broad and immediately usable.
   - B: deeper and more technical.
6. Produce exactly 4 publishable parts: main + 3 replies.
7. Do not publish automatically unless the user directly asks to publish/upload now.

## Draft Rules

- Main post: strong hook, one bad request, four unnumbered good requests, one principle.
- Reply 1: start with `[핵심 한 줄]`, then use `실전에서는 ...` and a 4-item framework.
- Reply 2: start with `[핵심 한 줄]`, then `예시 프롬프트:` and four quoted prompts.
- Reply 3: start with `[핵심 한 줄]`, then `참고해서 볼 만한 것들:` with full URLs and `- 볼 부분:`.
- Every part must stay under 500 characters.
- Do not include `Reply 1:`, `Reply 2:`, `Reply 3:`, `[한 줄 원칙:]`, `한 줄 원칙:`, `[초안 작성 모드]`, JSON, or fenced code blocks inside publishable text.
- Use academic/technical English only when Korean would blur the meaning: for example `claim`, `evidence`, `limitation`, `citation`, `reviewer critique`, `agent`.
- Avoid factory-like repetition. Keep the structure stable, but vary the hook, framework names, final principle, failure mode, and source mix.
- A symbolic person image is allowed when it strengthens the main hook. Use public-domain or clearly licensed images and keep the image contextual, not evidentiary.

## Fact Rules

Separate:

- Source facts: what the source directly says.
- Our interpretation: how to turn it into a research workflow.

Use short quotes only with source links. Famous-person quotes are optional, at most one, and only from `data/verified-quotes.json`.

## Handoff

When the user approves a chain, write only the publishable text to:

```text
approved-thread-chain.txt
```

Separate parts with:

```text
---
```

Dry run:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3 -DryRun
```

Publish after explicit approval/request:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 3
```

Quality gate only:

```powershell
.\scripts\check-approved-chain.ps1
```

## Output Shape

Keep metadata outside the publishable block:

~~~text
Recommended: A or B

Source Facts:
- ...

Our Interpretation:
- ...

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
- public_theme:
- topic_pillar:
- workflow_stage:
- failure_mode:
- solution_pattern:
- bad_request:
~~~

Do not put labels inside the publishable chain. Labels are acceptable only outside the block when explaining drafts to the user.
