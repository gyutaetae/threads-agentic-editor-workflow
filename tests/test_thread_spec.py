import unittest

from scripts.generate_auto_thread import apply_evaluator_gate
from scripts.thread_spec import (
    PART_ROLES,
    build_thread_spec,
    raise_for_report,
    thread_text_from_spec,
    validate_thread_spec,
    validate_thread_text,
)


VALID_THREAD = """AI에게 논문 요약을 맡길 때 “정리해줘”라고 하면 근거 위치가 흐려집니다.

나쁜 요청:
“이 논문을 요약해줘.”

좋은 요청:
“핵심 claim을 세 문장으로 분리해줘.”
“각 claim을 받치는 evidence 위치를 표시해줘.”
“limitation이 claim 범위를 어떻게 제한하는지 써줘.”
“citation이 실제로 지지하는 범위를 구분해줘.”

좋은 논문 요약은 매끄러운 문장이 아니라
근거를 다시 확인할 수 있는 연구 노트입니다.
---
[먼저 확인할 것]
요약 검증은 세 가지 연결을 봅니다.

1. claim이 한 문장으로 분리되는가
2. evidence가 표나 실험 위치와 연결되는가
3. limitation이 claim 범위를 제한하는가
---
[저장해둘 프롬프트]
논문 읽을 때 붙여 넣을 문장:

“이 요약을 claim, evidence, limitation 표로 바꾸고 각 항목에 원문 위치를 붙여줘.”
---
[참고 논문]
https://example.com/research-workflow
- 볼 부분: source fact가 claim과 evidence를 연결하는 방식

[나의 견해]
이 구조를 연구 노트의 검증 표로 적용할 수 있습니다."""


def metadata() -> dict:
    return {
        "topic": "summary verification",
        "format": "research_checklist",
        "workflow_stage": "summary_verification",
        "failure_mode": "false_fluency",
        "artifact_type": "summary_verification_grid",
        "reusable_unit_type": "verification_prompt",
        "hook_pattern": "reader_test",
        "source_name": "Research workflow example",
        "source_urls": ["https://example.com/research-workflow"],
    }


class ThreadSpecTests(unittest.TestCase):
    def test_valid_thread_uses_one_canonical_contract(self) -> None:
        report = validate_thread_text(VALID_THREAD)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.warnings, [])
        self.assertEqual(len(report.part_lengths), 4)

    def test_non_four_part_thread_fails(self) -> None:
        report = validate_thread_text("근거를 검증해야 합니다.\n---\n[프롬프트]\nclaim을 evidence와 연결해줘.")
        self.assertIn("exactly 4 parts", " ".join(report.errors))

    def test_role_order_and_metadata_are_persisted(self) -> None:
        spec = build_thread_spec(VALID_THREAD, metadata=metadata(), origin="manual_codex")
        report = validate_thread_spec(spec, require_metadata=True)
        self.assertEqual(report.errors, [])
        self.assertEqual([part["role"] for part in spec["parts"]], list(PART_ROLES))
        self.assertEqual(thread_text_from_spec(spec), VALID_THREAD)

    def test_empty_fingerprint_is_a_strict_warning(self) -> None:
        empty = metadata()
        empty["artifact_type"] = ""
        spec = build_thread_spec(VALID_THREAD, metadata=empty, origin="manual_codex")
        report = validate_thread_spec(spec, require_metadata=True)
        self.assertIn("empty fingerprint fields", " ".join(report.warnings))
        with self.assertRaises(SystemExit):
            raise_for_report(report, strict=True)

    def test_repeated_generic_reply_heading_warns(self) -> None:
        repeated = VALID_THREAD.replace("[먼저 확인할 것]", "[핵심 한 줄]").replace("[저장해둘 프롬프트]", "[핵심 한 줄]")
        report = validate_thread_text(repeated)
        self.assertIn("feel templated", " ".join(report.warnings))

    def test_main_post_requires_bad_and_good_request_labels(self) -> None:
        report = validate_thread_text(VALID_THREAD.replace("나쁜 요청:", "피해야 할 요청:"))
        self.assertIn("나쁜 요청", " ".join(report.errors))

    def test_main_post_requires_three_or_four_good_requests(self) -> None:
        shortened = VALID_THREAD.replace("“citation이 실제로 지지하는 범위를 구분해줘.”\n", "").replace(
            "“limitation이 claim 범위를 어떻게 제한하는지 써줘.”\n", ""
        )
        report = validate_thread_text(shortened)
        self.assertIn("3-4", " ".join(report.errors))

    def test_main_post_requires_judgment_closer(self) -> None:
        shortened = VALID_THREAD.replace(
            "\n\n좋은 논문 요약은 매끄러운 문장이 아니라\n근거를 다시 확인할 수 있는 연구 노트입니다.", ""
        )
        report = validate_thread_text(shortened)
        self.assertIn("judgment closer", " ".join(report.errors))


class EvaluatorGateTests(unittest.TestCase):
    def test_evaluator_can_veto_auto_publish(self) -> None:
        gate = {"quality_score": 92, "decision": "publish", "reasons": [], "revision_suggestions": []}
        combined = apply_evaluator_gate(gate, {"score": 72, "decision": "revise", "revision_suggestions": ["hook 수정"]})
        self.assertEqual(combined["decision"], "draft")
        self.assertIn("Evaluator veto", " ".join(combined["reasons"]))

    def test_high_evaluator_score_keeps_publish(self) -> None:
        gate = {"quality_score": 92, "decision": "publish", "reasons": [], "revision_suggestions": []}
        combined = apply_evaluator_gate(gate, {"score": 90, "decision": "publish"})
        self.assertEqual(combined["decision"], "publish")


if __name__ == "__main__":
    unittest.main()
