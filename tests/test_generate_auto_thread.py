import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.generate_auto_thread import (
    build_evaluator_prompt,
    read_skill_library,
    safe_slug,
    select_content_format,
    validate_quote_selection,
    validate_thread,
)


SUGGESTION = {
    "id": "karpathy-predict-before-absorbing",
    "speaker": "Andrej Karpathy",
    "speaker_ko": "안드레이 카파시",
    "quote_ko": "정보를 받아들이기 전에 먼저 예측해보는 것이 이상적입니다.",
    "source_url": "https://karpathy.ai/tweets.html",
}


class QuoteSelectionTests(unittest.TestCase):
    def test_verified_quote_selection_passes(self) -> None:
        thread = (
            '안드레이 카파시는 "정보를 받아들이기 전에 먼저 예측해보는 것이 이상적입니다."라고 말했습니다.\n'
            "인용 원문:\nhttps://karpathy.ai/tweets.html"
        )
        result = validate_quote_selection(
            thread,
            {"quote_used": True, "quote_id": SUGGESTION["id"]},
            {"quote_suggestion": SUGGESTION},
        )
        self.assertEqual(result, SUGGESTION)

    def test_unsupplied_quote_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            validate_quote_selection(
                "안드레이 카파시",
                {"quote_used": True, "quote_id": SUGGESTION["id"]},
                {},
            )

    def test_quote_id_is_empty_when_unused(self) -> None:
        with self.assertRaises(SystemExit):
            validate_quote_selection(
                "No quote",
                {"quote_used": False, "quote_id": SUGGESTION["id"]},
                {},
            )


class FormatRouterTests(unittest.TestCase):
    def test_legacy_candidate_maps_to_new_router_format(self) -> None:
        candidate = {
            "title": "citation verification workflow",
            "description": "Check whether references support claims.",
            "content_axis": "checklist",
            "format_type": "copy_checklist",
            "post_goal": "save",
        }
        analysis = {"workflow_action": "AI가 만든 reference를 claim과 따로 검증한다."}
        routing = select_content_format(candidate, analysis, "2026-06-22", "morning")
        self.assertEqual(routing["format_type"], "research_checklist")
        self.assertEqual(routing["human_signal_type"], "citation_doubt")
        self.assertEqual(routing["reusable_unit_type"], "verification_checklist")

    def test_friday_evening_routes_to_weekly_review(self) -> None:
        candidate = {"title": "paper summary", "post_goal": "save"}
        routing = select_content_format(candidate, {}, "2026-06-26", "evening")
        self.assertEqual(routing["format_type"], "weekly_review_advice")


class ThreadValidationTests(unittest.TestCase):
    def test_flexible_two_part_chain_passes(self) -> None:
        thread = (
            "AI 요약이 너무 깔끔하면 먼저 claim과 evidence를 분리해야 합니다.\n\n"
            "읽기 쉬운 요약과 검증 가능한 연구 노트는 다릅니다.\n"
            "---\n"
            "바로 써볼 프롬프트:\n"
            "\"이 논문의 claim을 나누고, 각 claim을 받치는 evidence와 limitation을 표로 정리해줘.\""
        )
        validate_thread(thread)

    def test_chain_without_reusable_unit_fails(self) -> None:
        with self.assertRaises(SystemExit):
            validate_thread("AI 시대에는 논문을 다르게 읽어야 합니다.")


class SelfImprovementLoopTests(unittest.TestCase):
    def test_safe_slug_keeps_korean_and_removes_punctuation(self) -> None:
        self.assertEqual(safe_slug("2026-06-22 citation 검증!!"), "2026-06-22-citation-검증")

    def test_read_skill_library_collects_markdown_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "citation.md").write_text("# Citation\n검증 규칙", encoding="utf-8")
            (root / "ignore.txt").write_text("ignore", encoding="utf-8")
            text = read_skill_library(root)
        self.assertIn("citation.md", text)
        self.assertIn("검증 규칙", text)
        self.assertNotIn("ignore", text)

    def test_evaluator_prompt_contains_thread_and_learning_context(self) -> None:
        prompt = build_evaluator_prompt(
            thread_text="바로 써볼 프롬프트:\n\"claim과 citation을 분리해줘.\"",
            routing={"format_type": "research_checklist"},
            analysis={"workflow_action": "citation 검증"},
            recent_history=[],
            persistent_learnings="citation은 claim 지지 여부를 본다.",
            skill_library="Citation Verification",
        )
        self.assertIn("Return JSON only", prompt)
        self.assertIn("citation은 claim 지지 여부를 본다.", prompt)
        self.assertIn("바로 써볼 프롬프트", prompt)


if __name__ == "__main__":
    unittest.main()
