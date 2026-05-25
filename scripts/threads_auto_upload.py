import argparse
import os
import sys
from urllib.parse import urlencode

import requests


GRAPH_BASE = "https://graph.threads.net"
API_VERSION = "v1.0"


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
    response.raise_for_status()
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
    response.raise_for_status()
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
    response.raise_for_status()
    return response.json()


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
    response.raise_for_status()
    return response.json()


def publish_container(user_id: str, access_token: str, creation_id: str) -> dict:
    published = requests.post(
        f"{GRAPH_BASE}/{API_VERSION}/{user_id}/threads_publish",
        data={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    published.raise_for_status()
    return published.json()


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

        if args.dry_run:
            print("Dry run only. Thread chain to publish:")
            for i, part in enumerate(parts, start=1):
                print("-" * 40)
                print(f"Part {i}/{len(parts)}")
                print(part)
                if i == 1 and args.image_url:
                    print(f"Image URL: {args.image_url}")
            print("-" * 40)
            return 0

        user_id = env("THREADS_USER_ID", args.user_id)
        access_token = env("THREADS_ACCESS_TOKEN", args.access_token)
        reply_to_id = None
        published = []

        for i, part in enumerate(parts):
            result = publish_post(
                user_id=user_id,
                access_token=access_token,
                text=part,
                image_url=args.image_url if i == 0 else None,
                alt_text=args.alt_text if i == 0 else None,
                reply_to_id=reply_to_id,
            )
            published.append(result)
            reply_to_id = result.get("id")
            if not reply_to_id:
                raise SystemExit(f"Published part {i + 1}, but response had no id: {result}")

        print(published)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
