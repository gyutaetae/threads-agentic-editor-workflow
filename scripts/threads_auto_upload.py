import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from urllib.parse import urlencode

import requests


GRAPH_BASE = "https://graph.threads.net"
API_VERSION = "v1.0"


def raise_for_status_with_body(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = response.text.strip()
        sanitized_url = response.url
        if "access_token=" in sanitized_url:
            sanitized_url = sanitized_url.split("access_token=", 1)[0] + "access_token=<redacted>"
        access_token = os.environ.get("THREADS_ACCESS_TOKEN", "")
        if body and access_token:
            body = body.replace(access_token, "<redacted>")
        if body:
            raise SystemExit(f"{exc.response.status_code} Client Error for url: {sanitized_url}\nResponse body:\n{body}") from exc
        raise


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read().strip()


def build_auth_url(app_id: str, redirect_uri: str, scopes: str, state: str) -> str:
    query = urlencode(
        {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "response_type": "code",
            "state": state,
        }
    )
    return f"https://threads.net/oauth/authorize?{query}"


def exchange_code(app_id: str, app_secret: str, redirect_uri: str, code: str) -> dict:
    response = requests.post(
        f"{GRAPH_BASE}/oauth/access_token",
        data={
            "client_id": app_id,
            "client_secret": app_secret,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        },
        timeout=30,
    )
    raise_for_status_with_body(response)
    return response.json()


def exchange_long_lived(short_token: str, app_secret: str) -> dict:
    response = requests.get(
        f"{GRAPH_BASE}/access_token",
        params={
            "grant_type": "th_exchange_token",
            "client_secret": app_secret,
            "access_token": short_token,
        },
        timeout=30,
    )
    raise_for_status_with_body(response)
    return response.json()


def get_me(access_token: str) -> dict:
    response = requests.get(
        f"{GRAPH_BASE}/{API_VERSION}/me",
        params={
            "fields": "id,username,name",
            "access_token": access_token,
        },
        timeout=30,
    )
    raise_for_status_with_body(response)
    return response.json()


def get_thread_insights(access_token: str, post_id: str, metrics: list[str]) -> dict:
    response = requests.get(
        f"{GRAPH_BASE}/{API_VERSION}/{post_id}/insights",
        params={
            "metric": ",".join(metrics),
            "access_token": access_token,
        },
        timeout=30,
    )
    raise_for_status_with_body(response)
    return response.json()


def get_container_status(access_token: str, container_id: str) -> dict:
    response = requests.get(
        f"{GRAPH_BASE}/{API_VERSION}/{container_id}",
        params={
            "fields": "id,status,error_message",
            "access_token": access_token,
        },
        timeout=30,
    )
    raise_for_status_with_body(response)
    return response.json()


def wait_for_container_ready(
    access_token: str,
    container_id: str,
    timeout_seconds: int = 30,
    poll_seconds: float = 2.0,
) -> dict:
    deadline = time.monotonic() + timeout_seconds
    last_status = {}

    while time.monotonic() < deadline:
        last_status = get_container_status(access_token, container_id)
        status = str(last_status.get("status", "")).upper()

        if status in {"FINISHED", "PUBLISHED"}:
            return last_status

        if status in {"ERROR", "EXPIRED"}:
            message = last_status.get("error_message") or last_status
            raise SystemExit(f"Threads container {container_id} is not publishable: {message}")

        time.sleep(poll_seconds)

    raise SystemExit(f"Timed out waiting for Threads container {container_id}. Last status: {last_status}")


def parse_insights(payload: dict) -> dict[str, int]:
    parsed = {}
    for item in payload.get("data", []):
        name = item.get("name")
        value = None
        if "total_value" in item:
            total_value = item.get("total_value")
            if isinstance(total_value, dict):
                value = total_value.get("value")
            else:
                value = total_value
        if value is None and item.get("values"):
            latest = item["values"][-1]
            if isinstance(latest, dict):
                value = latest.get("value")
        if name and value is not None:
            try:
                parsed[name] = int(value)
            except (TypeError, ValueError):
                parsed[name] = 0
    return parsed


def create_container(
    user_id: str,
    access_token: str,
    text: str,
    media_type: str = "TEXT",
    image_url: str | None = None,
    alt_text: str | None = None,
    reply_to_id: str | None = None,
) -> dict:
    data = {
        "media_type": media_type,
        "text": text,
        "access_token": access_token,
    }

    if image_url:
        data["image_url"] = image_url

    if alt_text:
        data["alt_text"] = alt_text

    if reply_to_id:
        data["reply_to_id"] = reply_to_id

    response = requests.post(
        f"{GRAPH_BASE}/{API_VERSION}/{user_id}/threads",
        data=data,
        timeout=30,
    )
    raise_for_status_with_body(response)
    return response.json()


def is_retryable_publish_error(response: requests.Response) -> bool:
    try:
        error = response.json().get("error", {})
    except ValueError:
        return False

    return error.get("code") == 24 and error.get("error_subcode") == 4279009


def publish_container(user_id: str, access_token: str, creation_id: str) -> dict:
    wait_for_container_ready(access_token, creation_id)

    for attempt in range(1, 4):
        published = requests.post(
            f"{GRAPH_BASE}/{API_VERSION}/{user_id}/threads_publish",
            data={
                "creation_id": creation_id,
                "access_token": access_token,
            },
            timeout=30,
        )
        if published.ok:
            return published.json()

        if attempt < 3 and is_retryable_publish_error(published):
            time.sleep(2 * attempt)
            continue

        raise_for_status_with_body(published)

    raise SystemExit(f"Failed to publish Threads container {creation_id}")


def publish_post(
    user_id: str,
    access_token: str,
    text: str,
    image_url: str | None = None,
    alt_text: str | None = None,
    reply_to_id: str | None = None,
) -> dict:
    media_type = "IMAGE" if image_url else "TEXT"
    container = create_container(
        user_id=user_id,
        access_token=access_token,
        text=text,
        media_type=media_type,
        image_url=image_url,
        alt_text=alt_text,
        reply_to_id=reply_to_id,
    )
    return publish_container(user_id, access_token, container["id"])


def read_thread_parts(path: str) -> list[str]:
    raw = read_text(path)
    return [part.strip() for part in raw.split("\n---\n") if part.strip()]


def validate_thread_parts(parts: list[str]) -> None:
    too_long = [(index, len(part)) for index, part in enumerate(parts, start=1) if len(part) > 500]
    if too_long:
        detail = ", ".join(f"part {index}: {length} chars" for index, length in too_long)
        raise SystemExit(f"Threads text posts should be 500 characters or less. Too long: {detail}")


def print_thread_dry_run(parts: list[str], image_url: str | None = None) -> None:
    print("Dry run only. Thread chain to publish:")
    for i, part in enumerate(parts, start=1):
        print("-" * 40)
        print(f"Part {i}/{len(parts)} ({len(part)} chars)")
        print(part)
        if i == 1 and image_url:
            print(f"Image URL: {image_url}")
    print("-" * 40)


def publish_thread_parts(
    parts: list[str],
    user_id: str,
    access_token: str,
    image_url: str | None = None,
    alt_text: str | None = None,
) -> list[dict]:
    reply_to_id = None
    published = []

    for i, part in enumerate(parts):
        result = publish_post(
            user_id=user_id,
            access_token=access_token,
            text=part,
            image_url=image_url if i == 0 else None,
            alt_text=alt_text if i == 0 else None,
            reply_to_id=reply_to_id,
        )
        published.append(result)
        reply_to_id = result.get("id")
        if not reply_to_id:
            raise SystemExit(f"Published part {i + 1}, but response had no id: {result}")

    return published


def append_metrics_row(
    path: str,
    post_id: str,
    thread_url: str,
    topic: str,
    hook: str,
    format_name: str,
    source_count: int,
    card_used: bool,
    chain_replies: int = 0,
) -> None:
    fields = [
        "date",
        "post_id",
        "thread_url",
        "format",
        "topic",
        "hook",
        "source_count",
        "card_used",
        "posted_at",
        "views",
        "likes",
        "replies",
        "chain_replies",
        "own_replies",
        "audience_replies",
        "reposts",
        "quotes",
        "follows_gained",
        "notes",
    ]
    exists = os.path.exists(path)
    now = datetime.now().astimezone()
    with open(path, "a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "date": now.strftime("%Y-%m-%d"),
                "post_id": post_id,
                "thread_url": thread_url,
                "format": format_name,
                "topic": topic,
                "hook": hook,
                "source_count": source_count,
                "card_used": str(card_used).lower(),
                "posted_at": now.isoformat(timespec="seconds"),
                "views": 0,
                "likes": 0,
                "replies": 0,
                "chain_replies": chain_replies,
                "own_replies": 0,
                "audience_replies": 0,
                "reposts": 0,
                "quotes": 0,
                "follows_gained": 0,
                "notes": "auto-recorded after publish",
            }
        )


def append_content_history(
    path: str,
    source_name: str,
    source_url: str,
    topic: str,
    hook: str,
    format_name: str,
    post_ids: list[str],
    thread_url: str,
    series: str = "",
    series_part: str = "",
    public_theme: str = "",
    topic_pillar: str = "",
    workflow_stage: str = "",
    failure_mode: str = "",
    solution_pattern: str = "",
    bad_request: str = "",
) -> None:
    if not any([source_name, source_url, series, public_theme, topic_pillar, failure_mode, solution_pattern, bad_request]):
        return

    now = datetime.now().astimezone()
    entry = {
        "date": now.strftime("%Y-%m-%d"),
        "posted_at": now.isoformat(timespec="seconds"),
        "source_name": source_name,
        "source_url": source_url,
        "topic": topic,
        "format": format_name,
        "hook": hook,
        "post_ids": post_ids,
        "thread_url": thread_url,
        "series": series,
        "series_part": series_part,
        "public_theme": public_theme,
        "topic_pillar": topic_pillar,
        "workflow_stage": workflow_stage,
        "failure_mode": failure_mode,
        "solution_pattern": solution_pattern,
        "bad_request": bad_request,
    }
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def int_field(row: dict, key: str, default: int = 0) -> int:
    try:
        return int(row.get(key) or default)
    except (TypeError, ValueError):
        return default


def ensure_metrics_fields(fieldnames: list[str]) -> list[str]:
    desired_order = [
        "date",
        "post_id",
        "thread_url",
        "format",
        "topic",
        "hook",
        "source_count",
        "card_used",
        "posted_at",
        "views",
        "likes",
        "replies",
        "chain_replies",
        "own_replies",
        "audience_replies",
        "reposts",
        "quotes",
        "follows_gained",
        "notes",
    ]
    return desired_order + [field for field in fieldnames if field not in desired_order]


def update_metrics_row(
    path: str,
    post_id: str,
    metrics: dict[str, int],
    notes: str = "",
    own_replies: int | None = None,
) -> bool:
    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = ensure_metrics_fields(list(rows[0].keys()) if rows else [])

    if not rows:
        return False

    updated = False
    for row in reversed(rows):
        if row.get("post_id") == post_id:
            for key in ["views", "likes", "replies", "reposts", "quotes"]:
                if key in metrics:
                    row[key] = metrics[key]
            if own_replies is not None:
                row["own_replies"] = own_replies
            chain_replies = int_field(row, "chain_replies")
            own_reply_count = int_field(row, "own_replies")
            total_replies = int_field(row, "replies")
            row["audience_replies"] = max(total_replies - chain_replies - own_reply_count, 0)
            if notes:
                existing = row.get("notes", "")
                row["notes"] = " | ".join(part for part in [existing, notes] if part)
            updated = True
            break

    if not updated:
        return False

    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return True


def env(name: str, fallback: str | None = None) -> str:
    value = os.environ.get(name, fallback)
    if not value:
        raise SystemExit(f"{name} is required. Set it as an environment variable or pass the matching argument.")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Threads API helper for approved posts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    auth = subparsers.add_parser("auth-url")
    auth.add_argument("--app-id", default=os.environ.get("THREADS_APP_ID"))
    auth.add_argument("--redirect-uri", default=os.environ.get("THREADS_REDIRECT_URI"))
    auth.add_argument("--scopes", default="threads_basic,threads_content_publish")
    auth.add_argument("--state", default="threads-growth-console")

    code = subparsers.add_parser("exchange-code")
    code.add_argument("--code", required=True)
    code.add_argument("--app-id", default=os.environ.get("THREADS_APP_ID"))
    code.add_argument("--app-secret", default=os.environ.get("THREADS_APP_SECRET"))
    code.add_argument("--redirect-uri", default=os.environ.get("THREADS_REDIRECT_URI"))

    long = subparsers.add_parser("long-token")
    long.add_argument("--short-token", default=os.environ.get("THREADS_SHORT_LIVED_ACCESS_TOKEN"))
    long.add_argument("--app-secret", default=os.environ.get("THREADS_APP_SECRET"))

    me = subparsers.add_parser("me")
    me.add_argument("--access-token", default=os.environ.get("THREADS_ACCESS_TOKEN"))

    publish = subparsers.add_parser("publish")
    publish.add_argument("--text-path", default="approved-thread-post.txt")
    publish.add_argument("--user-id", default=os.environ.get("THREADS_USER_ID"))
    publish.add_argument("--access-token", default=os.environ.get("THREADS_ACCESS_TOKEN"))
    publish.add_argument("--image-url", default=os.environ.get("THREADS_IMAGE_URL"))
    publish.add_argument("--alt-text", default=os.environ.get("THREADS_ALT_TEXT"))
    publish.add_argument("--reply-to-id", default=None)
    publish.add_argument("--dry-run", action="store_true")

    chain = subparsers.add_parser("publish-chain")
    chain.add_argument("--thread-path", default="approved-thread-chain.txt")
    chain.add_argument("--user-id", default=os.environ.get("THREADS_USER_ID"))
    chain.add_argument("--access-token", default=os.environ.get("THREADS_ACCESS_TOKEN"))
    chain.add_argument("--image-url", default=os.environ.get("THREADS_IMAGE_URL"))
    chain.add_argument("--alt-text", default=os.environ.get("THREADS_ALT_TEXT"))
    chain.add_argument("--dry-run", action="store_true")

    approved = subparsers.add_parser("publish-approved-chain")
    approved.add_argument("--thread-path", default="approved-thread-chain.txt")
    approved.add_argument("--access-token", default=os.environ.get("THREADS_ACCESS_TOKEN"))
    approved.add_argument("--image-url", default=os.environ.get("THREADS_IMAGE_URL"))
    approved.add_argument("--alt-text", default=os.environ.get("THREADS_ALT_TEXT"))
    approved.add_argument("--metrics-path", default="threads-post-metrics.csv")
    approved.add_argument("--history-path", default="content-history.jsonl")
    approved.add_argument("--topic", default="research ai workflow")
    approved.add_argument("--hook", default="")
    approved.add_argument("--format", default="A")
    approved.add_argument("--source-count", type=int, default=0)
    approved.add_argument("--source-name", default="")
    approved.add_argument("--source-url", default="")
    approved.add_argument("--series", default="")
    approved.add_argument("--series-part", default="")
    approved.add_argument("--public-theme", default="")
    approved.add_argument("--topic-pillar", default="")
    approved.add_argument("--workflow-stage", default="")
    approved.add_argument("--failure-mode", default="")
    approved.add_argument("--solution-pattern", default="")
    approved.add_argument("--bad-request", default="")
    approved.add_argument("--card-used", action="store_true")
    approved.add_argument("--dry-run", action="store_true")

    collect = subparsers.add_parser("collect-metrics")
    collect.add_argument("--post-id", required=True)
    collect.add_argument("--access-token", default=os.environ.get("THREADS_ACCESS_TOKEN"))
    collect.add_argument("--metrics-path", default="threads-post-metrics.csv")
    collect.add_argument("--window", default="manual")
    collect.add_argument("--metrics", default="views,likes,replies,reposts,quotes")
    collect.add_argument("--own-replies", type=int, default=None)
    collect.add_argument("--no-update-csv", action="store_true")

    args = parser.parse_args()

    if args.command == "auth-url":
        print(build_auth_url(env("THREADS_APP_ID", args.app_id), env("THREADS_REDIRECT_URI", args.redirect_uri), args.scopes, args.state))
        return 0

    if args.command == "exchange-code":
        print(exchange_code(env("THREADS_APP_ID", args.app_id), env("THREADS_APP_SECRET", args.app_secret), env("THREADS_REDIRECT_URI", args.redirect_uri), args.code))
        return 0

    if args.command == "long-token":
        print(exchange_long_lived(env("THREADS_SHORT_LIVED_ACCESS_TOKEN", args.short_token), env("THREADS_APP_SECRET", args.app_secret)))
        return 0

    if args.command == "me":
        print(get_me(env("THREADS_ACCESS_TOKEN", args.access_token)))
        return 0

    if args.command == "publish":
        text = read_text(args.text_path)
        if args.dry_run:
            print("Dry run only. Text to publish:")
            print("-" * 40)
            print(text)
            if args.image_url:
                print("-" * 40)
                print(f"Image URL: {args.image_url}")
            if args.reply_to_id:
                print(f"Reply to: {args.reply_to_id}")
            print("-" * 40)
            return 0
        print(
            publish_post(
                user_id=env("THREADS_USER_ID", args.user_id),
                access_token=env("THREADS_ACCESS_TOKEN", args.access_token),
                text=text,
                image_url=args.image_url,
                alt_text=args.alt_text,
                reply_to_id=args.reply_to_id,
            )
        )
        return 0

    if args.command == "publish-chain":
        parts = read_thread_parts(args.thread_path)
        if not parts:
            raise SystemExit(f"No thread parts found in {args.thread_path}")
        validate_thread_parts(parts)

        if args.dry_run:
            print_thread_dry_run(parts, args.image_url)
            return 0

        user_id = env("THREADS_USER_ID", args.user_id)
        access_token = env("THREADS_ACCESS_TOKEN", args.access_token)
        published = publish_thread_parts(parts, user_id, access_token, args.image_url, args.alt_text)
        print(published)
        return 0

    if args.command == "publish-approved-chain":
        parts = read_thread_parts(args.thread_path)
        if not parts:
            raise SystemExit(f"No thread parts found in {args.thread_path}")
        validate_thread_parts(parts)

        if args.dry_run:
            print_thread_dry_run(parts, args.image_url)
            return 0

        access_token = env("THREADS_ACCESS_TOKEN", args.access_token)
        me_payload = get_me(access_token)
        user_id = me_payload["id"]
        username = me_payload.get("username", "")
        print(f"Verified Threads account: {username} ({user_id})")

        published = publish_thread_parts(parts, user_id, access_token, args.image_url, args.alt_text)
        post_id = published[0].get("id", "")
        thread_url = f"https://www.threads.net/@{username}/post/{post_id}" if username and post_id else ""
        hook = args.hook or parts[0].splitlines()[0]
        append_metrics_row(
            path=args.metrics_path,
            post_id=post_id,
            thread_url=thread_url,
            topic=args.topic,
            hook=hook,
            format_name=args.format,
            source_count=args.source_count,
            card_used=args.card_used,
            chain_replies=max(len(parts) - 1, 0),
        )
        append_content_history(
            path=args.history_path,
            source_name=args.source_name,
            source_url=args.source_url,
            topic=args.topic,
            hook=hook,
            format_name=args.format,
            post_ids=[str(item.get("id", "")) for item in published if item.get("id")],
            thread_url=thread_url,
            series=args.series,
            series_part=args.series_part,
            public_theme=args.public_theme,
            topic_pillar=args.topic_pillar,
            workflow_stage=args.workflow_stage,
            failure_mode=args.failure_mode,
            solution_pattern=args.solution_pattern,
            bad_request=args.bad_request,
        )
        print(published)
        print(f"Recorded metrics row in {args.metrics_path}")
        if args.source_name or args.source_url:
            print(f"Recorded content history row in {args.history_path}")
        return 0

    if args.command == "collect-metrics":
        access_token = env("THREADS_ACCESS_TOKEN", args.access_token)
        metric_names = [metric.strip() for metric in args.metrics.split(",") if metric.strip()]
        payload = get_thread_insights(access_token, args.post_id, metric_names)
        metrics = parse_insights(payload)
        print(metrics)
        if not args.no_update_csv:
            note = f"metrics collected: {args.window}"
            if update_metrics_row(args.metrics_path, args.post_id, metrics, note, args.own_replies):
                print(f"Updated metrics row in {args.metrics_path}")
            else:
                print(f"No matching metrics row found in {args.metrics_path}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
