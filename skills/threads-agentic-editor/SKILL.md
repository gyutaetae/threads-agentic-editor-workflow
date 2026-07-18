---
name: threads-agentic-editor
description: "Draft, score, revise, or analyze one @arxiv.ai Threads chain about AI research workflows: paper reading, literature review, evidence mapping, citation checks, paper drafting, reviewer critique, and research-agent work design. Use when Codex needs to choose a source, turn it into one publishable Korean thread, avoid recent repetition, or prepare a draft for approval."
---

# Threads Agentic Editor

## Mission

Create one useful Threads chain for `@arxiv.ai`: Korean posts that turn papers into explainable research work. Use `docs/threads-channel-playbook.md` as the source of truth for tone, format, source rules, and publication criteria.

## Workflow

1. Read `docs/threads-channel-playbook.md`.
2. Check recent `content-history.jsonl` before choosing a source or angle.
3. Use credible sources: papers, official docs/blogs, named researcher writing, useful repos, or concrete Korean technical examples.
4. Select one strongest angle and draft one chain.
5. Draft exactly 4 parts: hook, diagnosis, reusable action, source interpretation.
6. Keep every part under 500 characters.
7. Do not publish unless the user directly asks to upload/post/publish.

## Draft Rules

- Start from a real paper-work failure, not AI news or generic prompt advice.
- Make the reader able to produce one artifact: prompt, checklist, table, protocol, matrix, role instruction, or revision rule.
- Part 1 is the canonical compact card: concrete problem hook, `나쁜 요청:` with one standalone quote, `좋은 요청:` with three or four standalone quotes, then a short judgment closer. It has no bracket heading or source link.
- Parts 2-4 use role-specific labels such as `[먼저 확인할 것]`, `[저장해둘 프롬프트]`, `[참고 논문]`, and `[나의 견해]`.
- Put source links only in the final reply, with `- 볼 부분:` or a verified quote source labeled `인용 원문:`.
- Separate source fact from @arxiv.ai interpretation.
- Avoid `Main:`, `Reply 1:`, `[한 줄 원칙]`, `[초안 작성 모드]`, JSON, and fenced code blocks in publishable text.
- Use English only when precision improves: `claim`, `evidence`, `limitation`, `citation`, `workflow`, `prompt`, `AI agent`.
- Use `docs/thread-pattern-library.md` for durable patterns. Vary the research failure, concrete requests, artifact, and closer inside the fixed main-post card.

## Handoff

Write only publishable text to:

```text
approved-thread-chain.txt
```

Separate parts with:

```text
---
```

Dry run:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "research ai workflow" -SourceCount 1 -DryRun
```

Quality gate only:

```powershell
.\scripts\check-approved-chain.ps1
```
