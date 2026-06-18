# Threads Channel Playbook

Compact reference for `@gyu_in_black`. Keep this file short enough to fit into generation prompts.

## Positioning

```text
agent로 논문 읽고, 글 쓰고, 개발하는 23살 대학생 개발자가 직접 실험한 AI 사용법
```

Promise:

```text
매일 하나, 개발자가 바로 복사해 쓸 수 있는 agent 작업법
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

Voice:

```text
직접 써본 사람의 짧은 기록. 개인 경험은 1-2줄만 쓰고 바로 실용 예시로 간다.
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

## Human Texture

Use a mix of surfaces so the account does not feel machine-produced.

Target mix:

- 40% bad usage -> better request
- 20% paper/dev diary: "오늘 논문/코드 작업하면서 느낀 건..."
- 20% failed request -> fixed request
- 20% quote/idea/opinion hook

Good personal lines:

- "오늘 논문 정리하다가 느낀 건..."
- "내가 agent에게 이렇게 시켰더니 결과가 흐렸습니다."
- "요즘 내가 제일 많이 쓰는 요청은 이겁니다."
- "23살 대학생 입장에서 제일 체감되는 차이는..."

Rules:

- Personal line is proof of use, not diary content.
- Add one concrete prompt, checklist, or workflow mode within the same chain.
- Never pretend to have used a tool, repo, or paper if the source does not support it.

## Quote Rule

Use quotes/idea hooks sparingly: about 20-30% of posts, not every post.

Quote-bank behavior:

- Use `data/quote_bank.json`.
- Prefer paraphrase unless `quote` is filled and source is verified.
- Start from the quote/idea, then immediately connect it to a real agent workflow.
- The famous person is the doorway. The value is the user's own agent practice.

Example:

```text
Feynman식으로 말하면,
이해했다는 건 다시 설명하고 재구성할 수 있다는 뜻입니다.

논문을 agent에게 읽힐 때도
"요약해줘"보다 이렇게 시키는 게 낫습니다:
...
```

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
Main: bad usage hook + meaning + better usage examples
Reply 1: 적용 기준 or workflow modes
Reply 2: 예시 프롬프트
Reply 3: 참고해서 볼 만한 것들 + how to apply each source
```

## Proven Format

Use this often for practical workflow posts:

```text
Main:
만약
"[나쁜 사용 예시]"
라고 사용하고 있다면,

[무엇을 잘못 맡기고 있거나 놓치고 있다는 뜻]입니다.

이런 방식으로 요청해보세요:
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

- The first line puts the bad usage inside the hook instead of labeling it as a draft section.
- "이런 방식으로 요청해보세요" gives readers the better phrasing immediately.
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

만약
"[나쁜 사용 예시]"
라고 사용하고 있다면,

[기능을 도구 이름으로만 쓰고 workflow를 바꾸지 못한다는 뜻]입니다.

이런 방식으로 요청해보세요:
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
만약
"[나쁜 사용 예시]"
라고 사용하고 있다면,

[무엇을 잘못 맡기고 있거나 놓치고 있다는 뜻]입니다.
```

Other acceptable hooks:

- "AI agent 잘 쓰는 사람은 프롬프트보다 작업 단위를 먼저 설계한다."
- "GitHub star부터 보고 있다면, AI repo를 잘못 읽고 있는 겁니다."
- "AI에게 코드 리뷰를 시킬 때 '이 PR 리뷰해줘'라고 하면 대부분 평범한 말만 돌아옵니다."
- "오늘 논문 정리하다가 agent에게 절대 한 번에 맡기면 안 되는 일을 배웠습니다."
- "내가 agent에게 이렇게 시켰더니 결과가 흐렸습니다."
- "[Famous person]의 [idea]를 agent 작업에 적용하면 기준이 달라집니다."

Name a common mistake through an exact bad usage example, reframe what it means, then show the better workflow with "이런 방식으로 요청해보세요:".

## Format Diversity

Avoid factory feel.

- Do not reuse the same opening pattern for 3 consecutive published posts.
- If the last 3 hooks use the same pattern, the next generated option should be penalized.
- Vary first-person proof, quote/idea hook, failed request, and direct diagnostic.
- Keep the reusable structure under the surface: mistake, criterion, example, source.

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
- `saves_bad_good_format` -> reuse the "만약 [나쁜 사용]이라고 사용하고 있다면 / 이런 방식으로 요청해보세요" format with a new workflow problem.
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

