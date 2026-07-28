import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.daily_publish_guard import (
    ALLOW,
    GUARD_ERROR,
    SKIP_TODAY,
    day_bounds,
    is_authored_top_level,
    run_guard,
)


class FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload
        self.ok = status_code < 400
        self.text = json.dumps(payload)

    def json(self) -> dict:
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls = []

    def get(self, *args, **kwargs) -> FakeResponse:
        self.calls.append((args, kwargs))
        return self.response


class DailyPublishGuardTests(unittest.TestCase):
    def test_day_bounds_use_kst_calendar_day(self) -> None:
        now = datetime(2026, 7, 18, 9, 30, tzinfo=timezone.utc)
        start, end = day_bounds(now)
        self.assertEqual(start.isoformat(), "2026-07-18T00:00:00+09:00")
        self.assertEqual(end.isoformat(), "2026-07-18T18:30:00+09:00")

    def test_only_authored_top_level_posts_block(self) -> None:
        self.assertTrue(is_authored_top_level({"id": "main", "is_reply": False}))
        self.assertTrue(is_authored_top_level({"id": "quote", "is_quote_post": True}))
        self.assertFalse(is_authored_top_level({"id": "reply", "is_reply": True}))
        self.assertFalse(is_authored_top_level({"id": "reply2", "root_post": {"id": "main"}}))
        self.assertFalse(is_authored_top_level({"id": "repost", "reposted_post": {"id": "other"}}))

    def test_manual_post_blocks_and_is_synced_once(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / "content-history.jsonl"
            state = root / "state.json"
            failures = root / "failures"
            response = FakeResponse(
                200,
                {
                    "data": [
                        {
                            "id": "manual-1",
                            "text": "수동으로 게시한 글입니다.",
                            "timestamp": "2026-07-18T08:00:00+0000",
                            "permalink": "https://www.threads.net/@arxiv.ai/post/manual-1",
                            "is_reply": False,
                            "is_quote_post": False,
                        },
                        {"id": "reply-1", "text": "답글", "is_reply": True},
                    ]
                },
            )
            now = datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc)

            first_code, first = run_guard(
                "preflight", history, state, failures, "secret-token", now, FakeSession(response)
            )
            second_code, second = run_guard(
                "prepublish", history, state, failures, "secret-token", now, FakeSession(response)
            )

            entries = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(first_code, SKIP_TODAY)
        self.assertEqual(second_code, SKIP_TODAY)
        self.assertEqual(first["synced_history_count"], 1)
        self.assertEqual(second["synced_history_count"], 0)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["origin"], "external_manual")
        self.assertEqual(entries[0]["post_ids"], ["manual-1"])

    def test_no_manual_post_allows_auto_publish(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, result = run_guard(
                "preflight",
                root / "history.jsonl",
                root / "state.json",
                root / "failures",
                "secret-token",
                datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
                FakeSession(FakeResponse(200, {"data": []})),
            )

        self.assertEqual(code, ALLOW)
        self.assertEqual(result["decision"], "allow_auto_publish")

    def test_verify_succeeds_when_top_level_post_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            response = FakeResponse(200, {"data": [{"id": "published-1", "is_reply": False}]})
            code, result = run_guard(
                "verify",
                root / "history.jsonl",
                root / "state.json",
                root / "failures",
                "secret-token",
                datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
                FakeSession(response),
                expect_post=True,
            )

        self.assertEqual(code, ALLOW)
        self.assertEqual(result["decision"], "post_verified")

    def test_verify_fails_when_no_top_level_post_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, result = run_guard(
                "verify",
                root / "history.jsonl",
                root / "state.json",
                root / "failures",
                "secret-token",
                datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
                FakeSession(FakeResponse(200, {"data": []})),
                expect_post=True,
            )

        self.assertEqual(code, GUARD_ERROR)
        self.assertEqual(result["decision"], "post_missing")

    def test_expired_token_fails_closed_and_redacts_secret(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = "super-secret-token"
            response = FakeResponse(
                401,
                {"error": {"code": 190, "message": f"Access token {token} expired"}},
            )
            code, result = run_guard(
                "preflight",
                root / "history.jsonl",
                root / "state.json",
                root / "failures",
                token,
                datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
                FakeSession(response),
            )
            failure_files = list((root / "failures").glob("*.json"))
            saved = failure_files[0].read_text(encoding="utf-8")

        self.assertEqual(code, GUARD_ERROR)
        self.assertEqual(result["decision"], "block_on_guard_error")
        self.assertEqual(result["error_type"], "threads_token_expired_or_invalid")
        self.assertEqual(len(failure_files), 1)
        self.assertNotIn(token, saved)
        self.assertIn("<redacted>", saved)


if __name__ == "__main__":
    unittest.main()
