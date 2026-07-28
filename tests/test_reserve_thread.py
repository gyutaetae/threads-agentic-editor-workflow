import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.reserve_thread import consume_reserve, remaining_reserves, select_reserve


THREAD_TEXT = """AI에게 논문 검토를 맡길 때 결과 문장만 받으면 재현 조건이 사라집니다.

내가 어떤 환경에서 결과가 나왔는지 설명 못하면, 그건 검증이 아니라 결과 복사입니다.

나쁜 요청:
“이 실험 결과가 맞는지 확인해줘.”

좋은 요청:
“실행 환경과 dependency를 분리해줘.”
“각 결과를 만드는 command를 표시해줘.”
“필요한 dataset과 seed를 기록해줘.”
“실패할 때 먼저 볼 check를 남겨줘.”

좋은 재현 노트는 결과를 다시 말하는 문서가 아니라
다른 사람이 같은 검사를 실행할 수 있는 안내서입니다.
---
[먼저 확인할 것]
재현 가능성은 세 가지를 먼저 확인합니다.

1. 환경과 dependency가 고정됐는가
2. 입력과 실행 command가 남았는가
3. 예상 결과와 실패 조건이 분리됐는가
---
[저장해둘 프롬프트]
artifact를 검토할 때 붙여 넣을 문장:

“실험을 environment, input, command, expected output, failure check로 나눠 재현 표를 만들어줘.”
---
[참고 자료]
https://example.com/artifact-guideline
- 볼 부분: artifact를 실행하고 결과를 확인하기 위한 정보

- 적용: 결과 요약보다 재현 절차를 먼저 검사하는 체크리스트로 사용합니다."""


def reserve_payload(reserve_id: str, source_url: str) -> dict:
    return {
        "id": reserve_id,
        "thread_text": THREAD_TEXT.replace("https://example.com/artifact-guideline", source_url),
        "metadata": {
            "topic": "artifact reproducibility",
            "format": "research_checklist",
            "workflow_stage": "artifact_review",
            "failure_mode": "reproduction_steps_missing",
            "artifact_type": "artifact_execution_ledger",
            "reusable_unit_type": "reproducibility_checklist",
            "hook_pattern": "direct_claim",
            "source_name": "Artifact guideline",
            "source_urls": [source_url],
        },
    }


class ReserveThreadTests(unittest.TestCase):
    def test_select_skips_published_source_and_consume_moves_item(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            available = root / "available"
            used = root / "used"
            available.mkdir()
            first = available / "01-first.json"
            second = available / "02-second.json"
            first.write_text(
                json.dumps(reserve_payload("first", "https://example.com/used"), ensure_ascii=False),
                encoding="utf-8",
            )
            second.write_text(
                json.dumps(reserve_payload("second", "https://example.com/new"), ensure_ascii=False),
                encoding="utf-8",
            )
            history = root / "history.jsonl"
            history.write_text(
                json.dumps({"source_url": "https://example.com/used"}) + "\n",
                encoding="utf-8",
            )
            spec_path = root / "approved-thread-spec.json"
            thread_path = root / "approved-thread-chain.txt"
            metadata_path = root / "metadata.json"
            selection_path = root / "selection.json"

            selection = select_reserve(available, history, thread_path, spec_path, metadata_path, selection_path)
            destination = consume_reserve(selection_path, available, used)

            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            rendered_thread = thread_path.read_text(encoding="utf-8")
            destination_exists = destination.exists()

        self.assertEqual(selection["reserve_id"], "second")
        self.assertEqual(spec["origin"], "manual_codex")
        self.assertEqual(metadata["publish_mode"], "reserve")
        self.assertIn("나쁜 요청:", rendered_thread)
        self.assertEqual(destination.name, "02-second.json")
        self.assertTrue(destination_exists)

    def test_remaining_counts_only_unused_valid_reserves(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            available = root / "available"
            available.mkdir()
            (available / "01-first.json").write_text(
                json.dumps(reserve_payload("first", "https://example.com/used"), ensure_ascii=False),
                encoding="utf-8",
            )
            (available / "02-second.json").write_text(
                json.dumps(reserve_payload("second", "https://example.com/new"), ensure_ascii=False),
                encoding="utf-8",
            )
            history = root / "history.jsonl"
            history.write_text(json.dumps({"source_url": "https://example.com/used"}) + "\n", encoding="utf-8")

            remaining = remaining_reserves(available, history)

        self.assertEqual(remaining, 1)


if __name__ == "__main__":
    unittest.main()
