import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests


RESPONSES_URL = "https://api.groq.com/openai/v1/responses"
DEFAULT_MODEL = "openai/gpt-oss-20b"
MAX_PARTS = 4
MAX_CHARS = 500


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def read_json(path: Path) -> object:
    return json.loads(read_text(path))


def extract_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]

    parts = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def validate_thread(thread_text: str) -> None:
    parts = [part.strip() for part in thread_text.strip().split("\n---\n") if part.strip()]
    if not parts:
        raise SystemExit("Generated thread has no parts.")
    if len(parts) > MAX_PARTS:
        raise SystemExit(f"Generated thread has {len(parts)} parts; limit is {MAX_PARTS}.")
    for index, part in enumerate(parts, start=1):
        if len(part) > MAX_CHARS:
            raise SystemExit(f"Generated part {index} is {len(part)} chars; limit is {MAX_CHARS}.")
    if "나쁜 요청" not in parts[0] and "신기능" not in parts[0] and "추가" not in parts[0]:
        raise SystemExit("Generated main post does not match the channel's proven formats.")
    if len(parts) >= 3 and "예시 프롬프트" not in thread_text:
        raise SystemExit("Generated thread is missing an example prompt.")


def build_prompt(playbook: str, candidates: list[dict]) -> str:
    compact_candidates = []
    for item in candidates[:8]:
        compact_candidates.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "category": item.get("category"),
                "description": item.get("description"),
                "readme_summary": item.get("readme_summary"),
                "our_angle": item.get("our_angle"),
                "score": item.get("score", {}).get("total"),
                "risk": item.get("risk"),
                "facts_vs_interpretation": item.get("fact_boundary"),
            }
        )

    return (
        "Create exactly one Korean Threads chain for @gyu_in_black.\n"
        "Follow the channel playbook exactly.\n\n"
        "Hard constraints:\n"
        "- Return JSON only.\n"
        "- JSON keys: thread_text, topic, source_count, format, source_name, source_url.\n"
        "- thread_text must use --- between main and replies.\n"
        "- Maximum 4 parts total: main + up to 3 replies.\n"
        "- Each part must be under 500 Korean characters.\n"
        "- Prefer the proven structure: 나쁜 요청 / 좋은 요청, workflow mode, 예시 프롬프트, 참고해서 볼 만한 것들.\n"
        "- If using a new feature topic, include official source links and concrete usage.\n"
        "- Do not invent facts. Use only the candidates below as factual sources.\n"
        "- Keep it short. No hype. No investment/product-buying claims.\n\n"
        "Channel playbook:\n"
        f"{playbook}\n\n"
        "Today's candidates:\n"
        f"{json.dumps(compact_candidates, ensure_ascii=False, indent=2)}"
    )


def call_groq(api_key: str, model: str, prompt: str) -> dict:
    response = requests.post(
        RESPONSES_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "input": prompt,
            "max_output_tokens": 2000,
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise SystemExit(f"Groq API error {response.status_code}:\n{response.text}")
    return response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one approved Threads chain with Groq.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--candidates-path", required=True)
    parser.add_argument("--playbook-path", default="docs/threads-channel-playbook.md")
    parser.add_argument("--output-path", default="approved-thread-chain.txt")
    parser.add_argument("--metadata-path", default="daily-editor/auto-thread-metadata.json")
    parser.add_argument("--model", default=os.environ.get("GROQ_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY is required.")

    candidates = read_json(Path(args.candidates_path))
    if not isinstance(candidates, list) or not candidates:
        raise SystemExit(f"No candidates found in {args.candidates_path}")

    playbook = read_text(Path(args.playbook_path))
    prompt = build_prompt(playbook, candidates)
    payload = call_groq(api_key, args.model, prompt)
    text = extract_text(payload)
    data = extract_json(text)

    thread_text = str(data.get("thread_text", "")).strip()
    validate_thread(thread_text)

    candidate_by_url = {item.get("url"): item for item in candidates if item.get("url")}
    source_url = str(data.get("source_url") or "").strip()
    source_item = candidate_by_url.get(source_url) or candidates[0]

    output_path = Path(args.output_path)
    output_path.write_text(thread_text + "\n", encoding="utf-8")

    metadata = {
        "date": args.date,
        "model": args.model,
        "topic": data.get("topic", "agent workflow"),
        "source_count": int(data.get("source_count", 0) or 0),
        "format": data.get("format", "A"),
        "source_name": data.get("source_name") or source_item.get("name") or source_item.get("title") or "",
        "source_url": source_url or source_item.get("url") or "",
    }
    metadata_path = Path(args.metadata_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {output_path}")
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
