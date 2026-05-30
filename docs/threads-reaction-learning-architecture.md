# Threads Reaction Learning Architecture

Purpose:

```text
반응 데이터를 이용해 "개발자가 흥미를 느끼고 댓글 달고 싶어 하는 agent/harness 주제"를 더 잘 고른다.
```

Do not optimize only for views. Optimize for useful developer attention:

```text
reply_rate + share_rate + follow_rate + useful_comment_signal
```

## Loop

```text
publish approved chain
  -> collect metrics at 1h / 6h / 24h / 72h
  -> label useful comments
  -> update channel-strategy-memory.md weekly
  -> tune next candidate scoring
```

## Metrics

Collect:

```text
views, likes, replies, reposts, quotes, follows_gained
```

Derived:

```text
reply_rate = replies / views
share_rate = (reposts + quotes) / views
follow_rate = follows_gained / views
conversation_score = replies + quotes * 2
```

Interpretation:

- high views + low follows = broad but weak fit
- low views + high replies/quotes = turn into follow-up
- high share_rate = saveable framework or strong disagreement
- high reply_rate = topic has open questions

## Comment Labels

Use comments as strategy input, not truth.

Labels:

```text
asks_for_example
asks_for_template
asks_for_tooling
asks_for_beginner_version
wants_deeper_technical
disagrees
adds_context
confused
```

Turn repeated labels into content decisions:

- `asks_for_example` -> next post should show a concrete workflow
- `asks_for_template` -> make a checklist/card
- `wants_deeper_technical` -> make B안 or architecture teardown
- `confused` -> simplify terms or add before/after
- `disagrees` -> make a respectful counterpoint post

## Weekly Strategy Memory

Write or update `channel-strategy-memory.md` with:

```text
Winning topics:
Weak topics:
Winning hooks:
Comment demand:
Formats to repeat:
Formats to pause:
Next scoring adjustments:
```

Scoring adjustment:

```text
final_score =
  source_score
  + harness_insight_bonus
  + developer_utility_bonus
  + comment_potential_bonus
  + proven_format_bonus
  - generic_news_penalty
  - repo_list_without_lesson_penalty
```

## Current Commands

Publish:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "agent repo reading" -SourceCount 3
```

Collect metrics:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

Check draft quality:

```powershell
.\scripts\check-approved-chain.ps1
```

## Guardrails

- Keep source facts separate from our interpretation.
- Use GitHub stars as a hook, not a claim of quality.
- Do not let one viral post fully change the channel direction.
- Prefer patterns developers can copy over general AI commentary.
