# Threads Agentic Editor Examples

## A안: 대중형

Main:

```text
Codex나 Claude Code한테
"이 앱 만들어줘"라고 시키면 대부분 망한다.

프로들은 일을 이렇게 쪼갠다.

1. 실패하는 테스트 하나
2. 수정할 파일 범위
3. 성공 기준
4. 되돌릴 수 있는 diff
```

Reply:

```text
AI agent는 큰 목표보다
검증 가능한 작은 티켓에서 훨씬 강하다.

사람 팀도 똑같다.
"서비스 개선"보다
"로그인 실패 케이스 재현하고 테스트 추가"가 훨씬 잘 굴러간다.
```

Card:

```text
AI agent에게 일을 맡기는 기준
1. 범위가 작다
2. 성공 기준이 보인다
3. diff/test로 검증 가능하다
4. 실패해도 되돌릴 수 있다
```

## B안: 전문형

Main:

```text
subagent는 일을 많이 시키려고 쓰는 게 아니다.

실전에서는 실패 범위를 줄이려고 쓴다.

리서치 agent가 틀려도
코드 수정 agent가 바로 main branch를 건드리지 않게 만드는 것.
이게 agent 아키텍처의 핵심이다.
```

Reply:

```text
내 기준으로 subagent를 나누는 축은 역할보다 권한이다.

- 읽기만 가능한 agent
- diff 제안만 가능한 agent
- 테스트 실행 가능한 agent
- 실제 파일 수정 가능한 agent

agent 설계는 똑똑함보다 권한 경계가 먼저다.
```

Card:

```text
Subagent를 나누는 기준
역할보다 권한

READ
SUGGEST
TEST
EDIT
PUBLISH
```
