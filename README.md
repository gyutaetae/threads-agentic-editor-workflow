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
  GitHub API, repo README, 안정적인 공식 RSS/Atom feed 수집 및 점수화.

scripts/threads_auto_upload.py
  Threads API 게시 도우미.

scripts/upload-thread-image-gh.ps1
  카드 이미지를 GitHub public raw URL로 업로드.

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
Main: 나쁜 요청 / 좋은 요청
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

`Auto Publish Daily Threads Chain` workflow는 매일 09:00 KST에 후보 수집, Groq 초안 생성, 품질 검사, Threads 게시를 자동 실행한다.

필요한 GitHub secret:

```text
GROQ_API_KEY
THREADS_ACCESS_TOKEN
```

선택 GitHub variable:

```text
GROQ_MODEL
```

기본 모델은 `openai/gpt-oss-20b`다. Groq는 OpenAI-compatible endpoint를 제공하므로 자동 초안 생성은 `GROQ_API_KEY`로 실행한다.

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
