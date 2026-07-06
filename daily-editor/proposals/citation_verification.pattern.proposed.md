# 제안된 Pattern: citation_verification

상태: proposed

검토 후 유용한 부분만 `docs/thread-pattern-library.md`에 승격합니다.

## 요약

claim-citation-evidence table을 중심으로 citation 검증 글을 구성한다.

## 근거

- 2026-06-22-manual-citation-verification | research_checklist | AI citation 검증 | score=88 | evaluator score 88 >= 85; decision=publish; https://www.threads.net/@arxiv.ai/post/17955254165986058

## 재사용 패턴

- 글이 해결하려는 구체적인 research failure에서 시작합니다.
- source fact와 계정의 적용 해석을 분리합니다.
- 복사 가능한 prompt, checklist, agent instruction 중 하나를 포함합니다.
- 고정 템플릿이 되지 않도록 구조를 유연하게 둡니다.

## 예시 발췌

### 2026-06-22-manual-citation-verification

- AI가 citation을 달아주면 안심하기 쉽습니다. 그런데 논문 작업에서는 citation이 있다는 것과 그 citation이 claim을 실제로 받친다는 것은 다릅니다. AI가 붙인 참고문헌은 먼저 "존재하는가"보다 "이 문장을 정말 지지하는가"로 봐야 합니다. 좋은 citation 검증은 reference 확인이 아니라 claim과 근거 위치를 다시 연결하는 작업입니다.
- citation을 볼 때는 이 4개만 먼저 확인합니다. 1. 존재성: 실제 논문/문서인가 2. 관련성: 주제만 비슷한가, claim을 직접 받치나 3. 위치: 어느 문단, 표, 그림, 실험이 근거인가 4. 강도: 강한 근거인가, 배경 설명인가 AI가 만든 bibliography를 그대로 믿으면 가장 위험한 부분이 제일 깔끔해 보입니다.
- 바로 써볼 프롬프트: "아래 초안의 모든 claim을 표로 뽑아줘. 각 claim마다 연결된 citation, 근거 위치, 근거 강도를 표시해줘. citation이 claim을 직접 지지하지 않으면 '검증 필요'로 표시해줘. 존재 여부와 claim 지지 여부를 분리해서 판단해줘."
