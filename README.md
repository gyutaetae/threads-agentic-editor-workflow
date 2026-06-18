# Threads Agentic Editor Workflow

Codex, Claude Code, Cursor로 일 잘하고 싶은 개발자를 위한 Threads 운영 워크플로우.

목표:

```text
매일 하나, 프로 개발자의 AI agent 작업법
```

## 구성

```text
skills/threads-agentic-editor
  Codex 스킬. 글 톤, 훅, 사실/해석 분리, A/B 초안 기준.

scripts/agentic_daily_pipeline.py
  GitHub API, repo README, 안정적인 공식 RSS/Atom feed 수집, content router, 점수화.

scripts/generate_auto_thread.py
  Groq 초안 생성, format selection, quality gate, draft/discard 분기.

scripts/threads_auto_upload.py
  Threads API 게시 도우미.

scripts/record-thread-metrics.ps1
scripts/update-thread-metrics.ps1
  게시물 반응 기록.
```

## 새 컴퓨터 설치

1. 이 repo를 clone한다.
2. Python 패키지를 설치한다.

```powershell
python -m pip install requests pillow
```

3. Codex 스킬을 설치한다.

```powershell
.\install-skill.ps1
```

4. 샘플 파일을 복사한다.

```powershell
Copy-Item .\templates\approved-thread-chain.example.txt .\approved-thread-chain.txt
Copy-Item .\templates\threads-post-metrics.example.csv .\threads-post-metrics.csv
Copy-Item .\scripts\threads-api-env.sample.ps1 .\threads-api-env.ps1
```

5. `threads-api-env.ps1`에 실제 Threads 값은 로컬에서만 넣는다. 이 파일은 commit하지 않는다.

## 매일 루틴

```powershell
.\scripts\run-daily-agentic-editor.ps1
```

생성물:

```text
daily-editor/YYYY-MM-DD-brief.md
daily-editor/YYYY-MM-DD-draft-prompt.md
daily-editor/YYYY-MM-DD-candidates.json
```

그 다음 Codex에:

```text
Use $threads-agentic-editor with daily-editor/YYYY-MM-DD-draft-prompt.md and create A/B drafts.
```

채널 컨셉과 작성 규칙은 한 파일만 본다.

```text
docs/threads-channel-playbook.md
```

현재 우선 포맷:

```text
Main: 만약 [나쁜 사용]이라고 사용하고 있다면 / [무엇을 잘못 맡긴다는 뜻] / 이런 방식으로 요청해보세요
Reply 1: 적용 기준 or workflow modes
Reply 2: 예시 프롬프트
Reply 3: 참고해서 볼 만한 것들 + 각 링크의 적용법
```

글은 짧게 쓴다. 댓글은 최대 3개까지만 허용한다. 이 포맷은 중복 주제가 아니라 새 workflow 문제에 반복 적용한다. 예: PR 리뷰, 테스트 수정, refactor 범위 지정, agent 권한, memory 설정, rollback 설계.

승인 후 게시 전 확인:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "agent repo reading" -SourceCount 5 -DryRun
```

게시:

```powershell
.\scripts\publish-approved-chain.ps1 -Topic "agent repo reading" -SourceCount 5
```

이 명령은 `THREADS_ACCESS_TOKEN`으로 실제 계정 ID를 확인해서 stale `THREADS_USER_ID` 문제를 피하고, 게시 후 `threads-post-metrics.csv`에 기본 행을 기록한다.

게시 전 품질 검사만 따로 실행:

```powershell
.\scripts\check-approved-chain.ps1
```

게시 후 metrics 수집:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h"
```

내가 직접 단 추가 댓글까지 제외하려면:

```powershell
.\scripts\collect-thread-metrics.ps1 -PostId "THREADS_POST_ID" -Window "24h" -OwnReplies 1
```

`threads-post-metrics.csv`의 `replies`는 Threads API가 주는 총 reply 수다. 분석에는 체인으로 단 답글과 내가 직접 단 댓글을 뺀 `audience_replies`를 우선 사용한다.

```text
audience_replies = replies - chain_replies - own_replies
```

## GitHub Actions 게시

로컬 터미널 대신 GitHub Actions에서 수동으로 게시할 수 있다.

초기 설정:

1. GitHub repo `Settings -> Secrets and variables -> Actions`로 간다.
2. `New repository secret`을 누른다.
3. 이름은 `THREADS_ACCESS_TOKEN`, 값은 Threads long-lived access token으로 저장한다.
4. 변경사항을 GitHub에 push한다.

게시:

1. GitHub repo `Actions` 탭으로 간다.
2. `Publish Threads Chain` workflow를 선택한다.
3. `Run workflow`를 누른다.
4. `thread_text`에 본문을 붙여넣는다. main/reply 구분은 `---` 한 줄만 사용한다.
5. 처음에는 `dry_run = true`로 실행해서 미리보기와 품질 검사를 확인한다.
6. 문제가 없으면 같은 내용으로 `dry_run = false`를 실행한다.

규칙:

- `approved-thread-chain.txt`는 gitignore라서 GitHub Actions 입력창에 매번 붙여넣는다.
- 게시 전 검사에서 main + 댓글 3개를 넘으면 실패한다.
- 실행 결과의 artifact에 `approved-thread-chain.txt`와 `threads-post-metrics.csv`가 저장된다.

## GitHub Actions 완전 자동 게시

`Auto Publish Daily Threads Chain` workflow는 시간대 A/B 테스트를 위해 슬롯을 나눠 후보 수집, Groq 초안 생성, 품질 검사, Threads 게시를 자동 실행한다.

현재 실험:

```text
월/수/금 09:00 KST: morning_primary
화/목 09:00 KST: morning_extra_two_post_day
화/목/토/일 21:00 KST: evening_primary
```

의도:

```text
매일 최소 1개 게시
화/목만 하루 2개 게시
오전 슬롯과 저녁 슬롯의 반응 차이 추적
```

필요한 GitHub secret:

```text
GROQ_API_KEY
THREADS_ACCESS_TOKEN
```

선택 GitHub variable:

```text
GROQ_MODEL
POSTS_PER_DAY
GENERATION_CANDIDATES
```

기본 모델은 `openai/gpt-oss-120b`다. Groq는 OpenAI-compatible endpoint를 제공하므로 자동 초안 생성은 `GROQ_API_KEY`로 실행한다.
자동 생성은 상위 소스 후보 3개를 각각 글로 만든 뒤 quality gate 점수가 가장 높은 1개만 게시 대상으로 선택한다.
`GENERATION_CANDIDATES`는 기본값 3이다.
`POSTS_PER_DAY`는 수동 실행용 보조 값이다. 실제 예약 실행의 하루 2개 실험은 workflow cron과 `experiment_group`으로 추적한다.

수동 테스트:

1. GitHub repo `Actions` 탭으로 간다.
2. `Auto Publish Daily Threads Chain`을 선택한다.
3. `Run workflow`를 누른다.
4. `publish = false`로 실행하면 생성 + dry-run만 한다.
5. `publish = true`로 실행하면 생성 후 실제 게시한다.

주의:

- `schedule` 실행은 승인 없이 바로 게시한다.
- 자동 글은 main + 댓글 3개, 파트당 500자 제한을 통과해야 한다.
- 품질이 흔들리면 workflow의 `schedule` 줄을 제거하고 수동 실행만 유지한다.
- `quality_score < 85`이면 자동 게시하지 않고 `daily-editor/review`에 draft/rejected 파일로 남긴다.
- 게시 기록에는 `post_slot`, `experiment_group`, `model`, `quality_score`, `format_type`, `content_axis`를 남긴다.

## 자동 metrics 수집

`Collect Threads Metrics` workflow는 매일 10:30/22:30 KST에 실행되어 `threads-post-metrics.csv`에서 24h/72h 수집 시점이 지난 게시물을 업데이트한다.

수집된 최근 반응은 다음 자동 생성 때 `metrics_feedback`으로 프롬프트에 들어간다.

핵심 비교 기준:

```text
post_slot: morning | evening
experiment_group: morning_primary | morning_extra_two_post_day | evening_primary
format_type
content_axis
quality_score
audience_replies
views, likes, reposts, quotes
```

## Weekly Editorial Memory

`Update Weekly Editorial Memory` workflow는 매주 월요일 10:00 KST에 `threads-post-metrics.csv`를 요약해 `docs/weekly-editorial-memory.md`를 갱신한다.

수동 갱신:

```powershell
python .\scripts\update_weekly_editorial_memory.py --metrics-path ".\threads-post-metrics.csv" --output-path ".\docs\weekly-editorial-memory.md" --days 7
```

이 파일은 다음 자동 생성 prompt에 들어간다. 목표는 조회수만 따라가는 것이 아니라, 어떤 주제/포맷/시간대가 유용한 댓글, 공유, 저장, 프로필 방문으로 이어지는지 학습하는 것이다.

## Quote Bank And Persona

계정 목소리:

```text
agent로 논문 읽고, 글 쓰고, 개발하는 23살 대학생 개발자가 직접 실험한 AI 사용법
```

유명인 quote/idea hook은 `data/quote_bank.json`에서 관리한다.

원칙:

- `quote`가 비어 있으면 원문 인용이 아니라 요지 paraphrase로만 사용한다.
- 검증된 짧은 원문을 직접 넣고 싶으면 `quote`, `source_url`, `tags`, `angle`을 함께 채운다.
- 유명인의 말은 도입부일 뿐이고, 본문은 반드시 개인 실험 1-2줄 + 복사 가능한 prompt/checklist로 이어진다.

공장 느낌 방지:

- 최근 3개 글의 첫 문장 패턴이 같으면 quality gate에서 감점한다.
- 생성 prompt는 최근 hook pattern과 weekly memory를 함께 보고 다른 표면을 선택한다.

## 게시 정책

초반에는 완전 자동 게시 금지.

```text
auto collect
auto score
auto draft
auto card
auto upload
human approve
auto publish
```

## 중요한 규칙

- 안정적인 소스만 자동 수집한다.
- 출처가 말한 사실과 우리의 해석을 분리한다.
- GitHub stars는 인기도이지 품질 보장이 아니다.
- 강한 훅은 허용하지만 근거 없는 1등/최고/무조건 표현은 피한다.
- 같은 source URL이나 repo는 `content-history.jsonl`에 기록하고 다음 후보에서 제외한다. 계정 컨셉은 반복하되, 같은 repo를 반복 소재로 쓰지 않는다.

## Content Router

자동 수집 후보는 생성 전에 세 값을 받는다.

```text
content_axis:
prompt_habit | workflow_mode | repo_teardown | failure_prevention | checklist | official_update | opinion

format_type:
bad_to_better | senior_first_move | workflow_mode | repo_lesson | failure_case | copy_checklist | update_to_action | short_opinion

post_goal:
save | comment | share | follow | profile_visit
```

후보 점수는 `actionability`, `copyability`, `senior_insight`, `source_grounding`, `format_fit`, `reuse_value`, `risk_reduction`, `hook_strength`를 가중합한다. 자동 생성은 가장 높은 후보를 고르되, morning은 쉬운 hook/prompt/failure/checklist 쪽을, evening은 workflow/repo/docs/update 쪽을 우선할 수 있게 설계했다.

## Quality Gate

`scripts/generate_auto_thread.py`는 생성 후 자체 quality gate를 실행한다.

```text
quality_score >= 85: approved-thread-chain.txt에 저장, 자동 게시 가능
70 <= quality_score < 85: daily-editor/review/*-draft-thread.txt에 저장, 자동 게시 안 함
quality_score < 70: daily-editor/review/*-rejected-thread.txt에 저장, 자동 게시 안 함
```

검사 기준은 강한 첫 줄, 실용 action, 복사 가능한 prompt/checklist/criteria/workflow mode/failure rule, 쉬운 main과 깊은 replies, link는 Reply 3에만, hype 금지, generic AI news 금지다.

Dry-run:

```powershell
.\scripts\run-daily-agentic-editor.ps1
python .\scripts\generate_auto_thread.py --date (Get-Date -Format "yyyy-MM-dd") --candidates-path ".\daily-editor\$(Get-Date -Format "yyyy-MM-dd")-candidates.json"
.\scripts\publish-approved-chain.ps1 -DryRun
```

