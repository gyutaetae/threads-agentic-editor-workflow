import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


GRAPH_BASE = "https://graph.threads.net"
API_VERSION = "v1.0"
ACCOUNT_TIMEZONE = timezone(timedelta(hours=9), "KST")
THREAD_FIELDS = (
    "id,text,timestamp,permalink,is_quote_post,is_reply,root_post,replied_to,reposted_post"
)
ALLOW = 0
SKIP_TODAY = 10
GUARD_ERROR = 20


def account_now() -> datetime:
    return datetime.now(ACCOUNT_TIMEZONE)


def day_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    current = (now or account_now()).astimezone(ACCOUNT_TIMEZONE)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, current


def sanitize_error(text: str, access_token: str) -> str:
    sanitized = (text or "").strip()
    if access_token:
        sanitized = sanitized.replace(access_token, "<redacted>")
    return sanitized[:4000]


def classify_api_error(response: requests.Response) -> str:
    try:
        error = response.json().get("error", {})
    except ValueError:
        error = {}
    if response.status_code in {401, 403} or error.get("code") == 190:
        return "threads_token_expired_or_invalid"
    return "threads_api_error"


def fetch_threads_for_today(
    access_token: str,
    now: datetime | None = None,
    session=requests,
) -> list[dict]:
    start, end = day_bounds(now)
    response = session.get(
        f"{GRAPH_BASE}/{API_VERSION}/me/threads",
        params={
            "fields": THREAD_FIELDS,
            "since": int(start.timestamp()),
            "until": int(end.timestamp()),
            "limit": 100,
            "access_token": access_token,
        },
        timeout=30,
    )
    if not response.ok:
        error_type = classify_api_error(response)
        body = sanitize_error(response.text, access_token)
        raise RuntimeError(f"{error_type}: HTTP {response.status_code}: {body}")
    payload = response.json()
    data = payload.get("data", [])
    return data if isinstance(data, list) else []


def is_authored_top_level(item: dict) -> bool:
    if item.get("is_reply") is True or item.get("root_post") or item.get("replied_to"):
        return False
    if item.get("reposted_post"):
        return False
    return bool(item.get("id"))


def known_post_ids(history_path: Path) -> set[str]:
    if not history_path.exists():
        return set()
    known: set[str] = set()
    for line in history_path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        for post_id in entry.get("post_ids") or []:
            if post_id:
                known.add(str(post_id))
    return known


def parse_timestamp(value: str, fallback: datetime) -> datetime:
    if not value:
        return fallback
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ACCOUNT_TIMEZONE)
    except ValueError:
        return fallback


def sync_external_posts(history_path: Path, posts: list[dict], now: datetime | None = None) -> int:
    current = (now or account_now()).astimezone(ACCOUNT_TIMEZONE)
    known = known_post_ids(history_path)
    entries = []
    for post in posts:
        post_id = str(post.get("id") or "")
        if not post_id or post_id in known:
            continue
        text = str(post.get("text") or "").strip()
        posted_at = parse_timestamp(str(post.get("timestamp") or ""), current)
        entries.append(
            {
                "date": posted_at.strftime("%Y-%m-%d"),
                "posted_at": posted_at.isoformat(timespec="seconds"),
                "origin": "external_manual",
                "source_name": "",
                "source_url": "",
                "topic": "manual_unclassified",
                "format": "manual_unclassified",
                "hook": next((line.strip() for line in text.splitlines() if line.strip()), ""),
                "main_text": text,
                "post_ids": [post_id],
                "thread_url": str(post.get("permalink") or ""),
                "is_quote_post": post.get("is_quote_post") is True,
                "manual_metadata_pending": True,
            }
        )
        known.add(post_id)

    if entries:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return len(entries)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def failure_type(message: str) -> str:
    if message.startswith("threads_token_expired_or_invalid"):
        return "threads_token_expired_or_invalid"
    if message.startswith("threads_token_missing"):
        return "threads_token_missing"
    return "threads_api_error"


def run_guard(
    stage: str,
    history_path: Path,
    state_path: Path,
    failure_dir: Path,
    access_token: str,
    now: datetime | None = None,
    session=requests,
    expect_post: bool = False,
) -> tuple[int, dict]:
    current = (now or account_now()).astimezone(ACCOUNT_TIMEZONE)
    base = {
        "date": current.strftime("%Y-%m-%d"),
        "checked_at": current.isoformat(timespec="seconds"),
        "stage": stage,
    }
    try:
        if not access_token:
            raise RuntimeError("threads_token_missing: THREADS_ACCESS_TOKEN is not configured")
        posts = [
            item
            for item in fetch_threads_for_today(access_token, current, session=session)
            if is_authored_top_level(item)
        ]
        synced = sync_external_posts(history_path, posts, current)
        result = {
            **base,
            "decision": (
                "post_verified"
                if posts and expect_post
                else "post_missing"
                if expect_post
                else "skip_manual_post"
                if posts
                else "allow_auto_publish"
            ),
            "top_level_post_count": len(posts),
            "synced_history_count": synced,
            "post_ids": [str(item.get("id")) for item in posts],
        }
        write_json(state_path, result)
        if expect_post:
            return (ALLOW if posts else GUARD_ERROR), result
        return (SKIP_TODAY if posts else ALLOW), result
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        message = sanitize_error(str(exc), access_token)
        result = {
            **base,
            "decision": "block_on_guard_error",
            "error_type": failure_type(message),
            "error": message,
        }
        write_json(state_path, result)
        failure_path = failure_dir / f"{base['date']}-{stage}-{result['error_type']}.json"
        write_json(failure_path, result)
        return GUARD_ERROR, result


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed daily Threads auto-publish guard.")
    parser.add_argument("--stage", choices=["preflight", "prepublish", "verify"], required=True)
    parser.add_argument("--expect-post", action="store_true")
    parser.add_argument("--history-path", default="content-history.jsonl")
    parser.add_argument("--state-path", default="daily-editor/state/daily-publish-guard.json")
    parser.add_argument("--failure-dir", default="daily-editor/failures")
    parser.add_argument("--access-token", default=os.environ.get("THREADS_ACCESS_TOKEN", ""))
    args = parser.parse_args()

    exit_code, result = run_guard(
        stage=args.stage,
        history_path=Path(args.history_path),
        state_path=Path(args.state_path),
        failure_dir=Path(args.failure_dir),
        access_token=args.access_token,
        expect_post=args.expect_post,
    )
    print(json.dumps(result, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
