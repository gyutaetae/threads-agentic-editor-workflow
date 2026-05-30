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
