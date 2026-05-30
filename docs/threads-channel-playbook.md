# Threads Channel Playbook

Always-reference guide for `@gyu_in_black`.

## Positioning

```text
프로 개발자의 AI agent 작업법을 훔쳐보는 계정
```

Promise:

```text
매일 하나, 개발자가 바로 훔쳐 쓸 수 있는 AI agent 작업법
```

Target reader:

```text
Codex, Claude Code, Cursor, Copilot, Windsurf 같은 AI coding agent로 실무 생산성을 높이고 싶은 개발자
```

Editorial thesis:

```text
Popular AI repos and official releases are hooks.
Harness/workflow insight is the value.
```

Do not stop at "this repo is trending." Explain what a developer can copy into their own agent workflow.

## Topic Filter

Pick topics that satisfy at least 3 of 5:

- reveals a practical agent/harness operating pattern
- changes how a developer asks an AI coding tool to work
- can become a checklist, template, teardown, or bad-vs-good example
- can trigger useful comments, disagreement, or examples
- has credible sources from GitHub repos, official docs/blogs, papers, or named technical discussions

Prefer:

- permissions, memory, tools, evals, logs, rollback, verification, PR review, tests, and task decomposition
- "what to copy into your workflow" over "what the tool/repo does"
- concrete prompts and review criteria over generic prompt advice
- new Codex, Claude Code, Cursor, Copilot, or Windsurf features only when the post explains how a developer should use the feature in a real workflow

Avoid:

- generic AI news summaries
- fake guru tone
- unverifiable "1등", "최고", "무조건", "혁명" claims
- link dumps without a workflow lesson
- feature announcements that only restate release notes without a concrete usage example

## Length And Thread Rules

Posts must stay short.

- Main post: one clear idea, usually under 350 Korean characters.
- Replies: maximum 3 replies.
- Total chain: main + up to 3 replies.
- Each part must stay under the Threads 500-character limit.
- If an idea needs more than 3 replies, split it into another day's post.
- Prefer one useful thread per day over multiple weaker posts.

Default chain:

```text
Main: hook + useful contrast
Reply 1: 적용 기준 or workflow modes
Reply 2: 예시 프롬프트
Reply 3: 참고해서 볼 만한 것들 + how to apply each source
```

## Proven Format

Use this often for practical workflow posts:

```text
Main:
AI agent에게 [흔한 넓은 요청]을 시키면 결과가 흐려진다.

나쁜 요청:
"..."

좋은 요청:
"..."
"..."
"..."

[한 줄 원칙: 품질은 모델보다 작업 범위/검수 기준/권한 경계에서 갈린다.]
---
Reply 1:
실전에서는 [전체 작업]이 아니라 [모드/범위/기준]을 정한다.
1. ...
2. ...
3. ...
---
Reply 2:
예시 프롬프트:
"..."
---
Reply 3:
참고해서 볼 만한 것들:
[official doc/repo/blog link]
- 적용: 내 workflow에 복사할 구조
```

Repeat the structure, not the topic. Use it for new workflow problems such as PR review, failing test fixes, refactor scoping, agent permissions, memory setup, rollback, and verification.

Why it works:

- "나쁜 요청 / 좋은 요청" makes the mistake immediately visible.
- "예시 프롬프트" gives readers something they can reuse today.
- "참고해서 볼 만한 것들" adds credibility without turning the main post into a link dump.
- Every source link must include an application note.

## New Feature Format

Use this when Codex, Claude Code, Cursor, Copilot, Windsurf, or another agent tool releases a useful feature.

```text
Main:
[Tool]에 [new feature]가 추가됐다.
중요한 건 기능 이름이 아니라
[어떤 workflow가 바뀌는지]입니다.

나쁜 사용:
"..."

좋은 사용:
"..."
"..."

[한 줄 원칙]
---
Reply 1:
어디에 쓰면 좋은가:
1. ...
2. ...
3. ...
---
Reply 2:
예시 프롬프트:
"..."
---
Reply 3:
참고해서 볼 만한 것들:
[official release/doc link]
- 적용: ...
```

Rules:

- Always verify new-feature claims against official docs, release notes, or the product's GitHub repo before drafting.
- Do not claim a feature is available to all users unless the source says so.
- Separate "source fact" from "our workflow interpretation."
- Keep the post practical: one feature, one workflow, one example prompt.

## Hook Rule

Default first line:

```text
만약 [흔한 행동]하고 있다면, [진짜 기준]을 잘못 쓰고 있는 겁니다.
```

Other acceptable hooks:

- "AI agent 잘 쓰는 사람은 프롬프트보다 작업 단위를 먼저 설계한다."
- "GitHub star부터 보고 있다면, AI repo를 잘못 읽고 있는 겁니다."
- "AI에게 코드 리뷰를 시킬 때 '이 PR 리뷰해줘'라고 하면 대부분 평범한 말만 돌아옵니다."

Name a common mistake, reframe the real criterion, then show the better workflow.

## Source Rules

Use primary sources when possible:

- official docs/blogs
- GitHub repos/releases
- arXiv or research papers
- original talks/posts by named people

Separate:

- Source facts: what the source directly says or exposes.
- Our interpretation: what this means for developer workflow.

Use community sources only for reaction signals, not factual proof. GitHub stars are trend signals, not quality proof.

## Draft Output

When asked for a daily draft, produce:

```text
Recommended: A or B

Source Facts:
- ...

Our Interpretation:
- ...

A안: 대중형
Main:
...
Reply 1:
...
Reply 2:
...
Reply 3:
...
Sources:
Risk:

B안: 전문형
...
```

Never exceed 3 replies in either option.

## Reaction Learning

Optimize for useful developer attention, not views alone:

```text
reply_rate + share_rate + follow_rate + useful_comment_signal
```

Comment labels:

```text
asks_for_example
asks_for_template
asks_for_tooling
clicks_reference_links
saves_bad_good_format
wants_deeper_technical
disagrees
confused
```

Turn repeated signals into decisions:

- `asks_for_example` -> show a concrete workflow next.
- `asks_for_template` -> make the next post a checklist or prompt template.
- `saves_bad_good_format` -> reuse "나쁜 요청 / 좋은 요청" with a new workflow problem.
- `clicks_reference_links` -> keep final replies as source links with application notes.
- `wants_deeper_technical` -> make a technical teardown, but split long ideas across days.
- `confused` -> simplify terms or add before/after.
- `disagrees` -> write a respectful counterpoint post.

Weekly memory should record:

```text
Winning topics
Weak topics
Winning hooks
Comment demand
Formats to repeat
Formats to pause
Next scoring adjustments
```
