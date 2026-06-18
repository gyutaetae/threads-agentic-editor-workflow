import json
import tempfile
import unittest
from pathlib import Path

from scripts.quote_matcher import (
    attach_quote_suggestions,
    load_catalog,
    quote_used_recently,
    score_quote,
)


ROOT = Path(__file__).resolve().parents[1]


class QuoteMatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_catalog(ROOT / "data" / "verified-quotes.json")

    def test_paper_reading_matches_karpathy_prediction_quote(self) -> None:
        candidate = {
            "title": "Paper summarization workflow",
            "description": "Use hypothesis and critical reading before paper summarization.",
            "our_angle": "논문 읽기 전에 가설과 예측을 먼저 만든다.",
        }
        quote = next(item for item in self.catalog if item["id"] == "karpathy-predict-before-absorbing")
        score = score_quote(candidate, quote)
        self.assertGreaterEqual(score["total"], 8)
        self.assertIn("hypothesis", score["matched_terms"])

    def test_unrelated_topic_does_not_match(self) -> None:
        candidate = {
            "title": "CSS color palette",
            "description": "Choose accessible colors for a dashboard.",
        }
        scores = [score_quote(candidate, quote)["total"] for quote in self.catalog]
        self.assertTrue(all(score < 8 for score in scores))

    def test_recent_quote_blocks_all_suggestions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.jsonl"
            history_path.write_text(
                json.dumps({"quote_used": True}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            candidates = [{"title": "AI evaluation guardrail", "description": "Evaluate and verify an agent."}]
            result = attach_quote_suggestions(
                candidates,
                self.catalog,
                history_path,
                verify_urls=False,
            )
            self.assertTrue(quote_used_recently(history_path))
            self.assertNotIn("quote_suggestion", result[0])

    def test_matching_candidate_gets_one_suggestion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.jsonl"
            history_path.write_text("", encoding="utf-8")
            candidates = [
                {
                    "title": "Citation verification agent",
                    "description": "Add evaluation and guardrail checks to citation verification.",
                }
            ]
            result = attach_quote_suggestions(
                candidates,
                self.catalog,
                history_path,
                verify_urls=False,
            )
            self.assertEqual(result[0]["quote_suggestion"]["id"], "huang-direct-manage-evaluate-ai")
            self.assertGreaterEqual(result[0]["quote_suggestion"]["score"]["total"], 8)


if __name__ == "__main__":
    unittest.main()
