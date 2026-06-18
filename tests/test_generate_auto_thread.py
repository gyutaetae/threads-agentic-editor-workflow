import unittest

from scripts.generate_auto_thread import validate_quote_selection


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


if __name__ == "__main__":
    unittest.main()
