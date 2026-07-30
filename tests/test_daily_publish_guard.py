import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.daily_publish_guard import (
    ALLOW,
    GRAPH_BASE,
    GUARD_ERROR,
    SKIP_TODAY,
    THREAD_FIELDS,
    day_bounds,
    fetch_threads_for_today,
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
    def __init__(self, response: FakeResponse | list[FakeResponse]) -> None:
        self.responses = response if isinstance(response, list) else [response]
        self.calls = []

    def get(self, *args, **kwargs) -> FakeResponse:
        self.calls.append((args, kwargs))
        return self.responses[min(len(self.calls) - 1, len(self.responses) - 1)]


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

    def test_fetch_uses_current_threads_list_contract_and_kst_bounds(self) -> None:
        now = datetime(2026, 7, 18, 9, 30, tzinfo=timezone.utc)
        session = FakeSession(FakeResponse(200, {"data": []}))

        fetch_threads_for_today("secret-token", now, session)

        args, kwargs = session.calls[0]
        self.assertEqual(args[0], f"{GRAPH_BASE}/v1.0/me/threads")
        self.assertEqual(GRAPH_BASE, "https://graph.threads.com")
        self.assertEqual(
            set(THREAD_FIELDS.split(",")),
            {"text", "timestamp", "permalink", "username"},
        )
        self.assertTrue(
            {"root_post", "replied_to", "reposted_post"}.isdisjoint(
                kwargs["params"]["fields"].split(",")
            )
        )
        self.assertEqual(
            kwargs["params"]["since"],
            int(datetime(2026, 7, 18, 0, 0, tzinfo=timezone.utc).timestamp())
            - (9 * 60 * 60),
        )
        self.assertEqual(kwargs["params"]["until"], int(now.timestamp()))
        self.assertEqual(kwargs["params"]["limit"], 100)
        self.assertEqual(kwargs["timeout"], 30)

    def test_fetch_retries_transient_threads_api_failures(self) -> None:
        session = FakeSession(
            [
                FakeResponse(500, {"error": {"code": 1, "message": "unknown"}}),
                FakeResponse(502, {"error": {"code": 2, "message": "temporary"}}),
                FakeResponse(200, {"data": [{"id": "post-1"}]}),
            ]
        )

        with patch("scripts.daily_publish_guard.time.sleep") as sleep:
            posts = fetch_threads_for_today(
                "secret-token",
                datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
                session,
            )

        self.assertEqual(posts, [{"id": "post-1"}])
        self.assertEqual(len(session.calls), 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_repeated_threads_api_500_fails_closed_after_retries(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = FakeSession(
                FakeResponse(500, {"error": {"code": 1, "message": "unknown"}})
            )
            with patch("scripts.daily_publish_guard.time.sleep"):
                code, result = run_guard(
                    "preflight",
                    root / "history.jsonl",
                    root / "state.json",
                    root / "failures",
                    "secret-token",
                    datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
                    session,
                )

        self.assertEqual(code, GUARD_ERROR)
        self.assertEqual(result["decision"], "block_on_guard_error")
        self.assertEqual(result["error_type"], "threads_api_error")
        self.assertEqual(len(session.calls), 4)

    def test_hidden_expired_token_is_classified_after_threads_api_500(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            session = FakeSession(
                [
                    FakeResponse(500, {"error": {"code": 1, "message": "unknown"}}),
                    FakeResponse(500, {"error": {"code": 1, "message": "unknown"}}),
                    FakeResponse(500, {"error": {"code": 1, "message": "unknown"}}),
                    FakeResponse(
                        400,
                        {
                            "error": {
                                "code": 190,
                                "message": "Error validating access token: Session has expired.",
                            }
                        },
                    ),
                ]
            )
            with patch("scripts.daily_publish_guard.time.sleep"):
                code, result = run_guard(
                    "preflight",
                    root / "history.jsonl",
                    root / "state.json",
                    root / "failures",
                    "expired-token",
                    datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
                    session,
                )

        self.assertEqual(code, GUARD_ERROR)
        self.assertEqual(result["decision"], "block_on_guard_error")
        self.assertEqual(result["error_type"], "threads_token_expired_or_invalid")
        self.assertEqual(len(session.calls), 4)
        self.assertEqual(session.calls[-1][0][0], f"{GRAPH_BASE}/debug_token")

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
