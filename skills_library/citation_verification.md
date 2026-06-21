# Citation Verification

Use when the topic is `citation_doubt` or `citation_verification`.

## Problem

AI-generated citations can look safe because they are formatted cleanly. The research problem is whether each `citation` directly supports the `claim`.

## Strong Shape

1. Open with the false-safety problem: a citation exists, but support is unverified.
2. Separate existence, relevance, source location, and support strength.
3. Give a reusable prompt that asks for a claim-citation-evidence table.
4. Put source links in the final reply with `- 볼 부분:`.

## Reusable Prompt Pattern

```text
아래 초안의 모든 claim을 표로 뽑아줘.
각 claim마다 연결된 citation, 근거 위치, 근거 강도를 표시해줘.
citation이 claim을 직접 지지하지 않으면 '검증 필요'로 표시해줘.
존재 여부와 claim 지지 여부를 분리해서 판단해줘.
```

## Fingerprint

- human_signal_type: `citation_doubt`
- workflow_stage: `citation_verification`
- failure_mode: `claim_reference_mismatch`
- reusable_unit_type: `verification_checklist`
