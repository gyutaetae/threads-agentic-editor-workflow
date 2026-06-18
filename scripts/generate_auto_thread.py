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
URL_RE = re.compile(r"https?://\S+")
QUOTE_LINE_RE = re.compile(r"(?m)^\s*[\"“][^\"”]+[\"”]\s*$")
FORBIDDEN_TEXT = [
    "[한 줄 원칙",
    "한 줄 원칙:",
    "Reply 1:",
    "Reply 2:",
    "Reply 3:",
    "Reply 1",
    "Reply 2",
    "Reply 3",
    "[초안 작성 모드]",
    "초안 작성 모드",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def read_json(path: Path) -> object:
    return json.loads(read_text(path))


def load_recent_history(path: Path, limit: int = 12) -> list[dict]:
    if not path.exists():
        return []

    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        entries.append(
            {
                "date": entry.get("date"),
                "series": entry.get("series"),
                "series_part": entry.get("series_part"),
                "public_theme": entry.get("public_theme"),
                "topic_pillar": entry.get("topic_pillar") or entry.get("topic"),
                "workflow_stage": entry.get("workflow_stage"),
                "failure_mode": entry.get("failure_mode"),
                "solution_pattern": entry.get("solution_pattern"),
                "bad_request": entry.get("bad_request"),
                "hook": entry.get("hook"),
                "source_name": entry.get("source_name"),
                "source_url": entry.get("source_url"),
                "quote_used": entry.get("quote_used", False),
                "quote_id": entry.get("quote_id"),
                "quote_speaker": entry.get("quote_speaker"),
            }
        )
    return entries[-limit:]


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
    if len(parts) != MAX_PARTS:
        raise SystemExit(f"Generated thread has {len(parts)} parts; expected exactly {MAX_PARTS} parts.")
    for index, part in enumerate(parts, start=1):
        if len(part) > MAX_CHARS:
            raise SystemExit(f"Generated part {index} is {len(part)} chars; limit is {MAX_CHARS}.")
    joined = "\n".join(parts)
    for forbidden in FORBIDDEN_TEXT:
        if forbidden in joined:
            raise SystemExit(f"Generated thread contains forbidden label: {forbidden}")
    if "```" in joined or '{"role"' in joined or '"tools"' in joined:
        raise SystemExit("Generated thread uses a code block or JSON-style prompt; use natural quoted Korean prompt text.")
    if "나쁜 요청:" not in parts[0] or "좋은 요청:" not in parts[0]:
        raise SystemExit("Generated main post must include both '나쁜 요청:' and '좋은 요청:' sections.")
    good_request = parts[0].split("좋은 요청:", 1)[1]
    quoted_good_lines = QUOTE_LINE_RE.findall(good_request)
    if len(quoted_good_lines) < 4:
        raise SystemExit("Generated main post must include at least four quoted good-request lines.")
    explanation_part = parts[1]
    for number in ("1", "2", "3", "4"):
        if f"{number}." not in explanation_part:
            raise SystemExit(f"Generated explanation reply is missing good request {number}.")
    if explanation_part.count("- 활용:") < 4:
        raise SystemExit("Generated explanation reply must include four '- 활용:' lines.")
    if not parts[2].startswith("예시 프롬프트:"):
        raise SystemExit("Generated third part must start with '예시 프롬프트:'.")
    if len(QUOTE_LINE_RE.findall(parts[2])) < 4:
        raise SystemExit("Generated prompt reply must include four quoted prompt examples.")
    reference_part = parts[-1]
    if not reference_part.startswith("참고해서 볼 만한 것들:"):
        raise SystemExit("Generated final reply must start with '참고해서 볼 만한 것들:'.")
    if not URL_RE.search(reference_part):
        raise SystemExit("Generated reference reply must include at least one full clickable URL.")
    if "notebooklm.google" in reference_part.lower():
        raise SystemExit("Generated reference reply must link an actual example, not the NotebookLM homepage.")
    if "- 볼 부분:" not in reference_part:
        raise SystemExit("Generated reference reply must explain what to inspect in each source.")


def validate_quote_selection(thread_text: str, data: dict, source_item: dict) -> dict | None:
    quote_used = data.get("quote_used") is True
    quote_id = str(data.get("quote_id") or "").strip()
    if not quote_used:
        if quote_id:
            raise SystemExit("Generated quote_id must be empty when quote_used is false.")
        return None

    quote_suggestion = source_item.get("quote_suggestion")
    if not quote_suggestion:
        raise SystemExit("Generated thread used a quote, but the selected source has no verified quote suggestion.")
    if quote_id != quote_suggestion["id"]:
        raise SystemExit("Generated quote_id does not match the selected source's verified quote suggestion.")

    required_quote_text = [
        quote_suggestion["speaker_ko"],
        quote_suggestion["quote_ko"],
        quote_suggestion["source_url"],
        "인용 원문:",
    ]
    missing = [value for value in required_quote_text if value not in thread_text]
    if missing:
        raise SystemExit(f"Generated quoted thread is missing verified quote fields: {missing}")
    return quote_suggestion


def build_prompt(playbook: str, candidates: list[dict], recent_history: list[dict]) -> str:
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
                "optional_verified_quote": item.get("quote_suggestion"),
            }
        )

    return (
        "Create exactly one Korean Threads chain for @gyu_in_black's research AI channel.\n"
        "Follow the channel playbook exactly.\n\n"
        "Hard constraints:\n"
        "- Return JSON only.\n"
        "- JSON keys: thread_text, topic, source_count, format, source_name, source_url, quote_used, quote_id.\n"
        "- Also return fingerprint keys: series, series_part, public_theme, topic_pillar, workflow_stage, failure_mode, solution_pattern, bad_request.\n"
        "- thread_text must use --- between main and replies.\n"
        "- Exactly 4 parts total: main + 3 replies.\n"
        "- Each part must be under 500 Korean characters.\n"
        "- Match the manual publishing style exactly. Do not sound like generated documentation.\n"
        "- Main post must start with either a '만약 ...' diagnostic hook or a natural first line like 'AI에게 논문 초안을 맡길 때'.\n"
        "- Main post must then include '나쁜 요청:' with one quoted bad request.\n"
        "- Main post must include '좋은 요청:' with at least four short quoted good-request lines.\n"
        "- End the main post with a plain closing principle sentence. Do not write '[한 줄 원칙:]' or '한 줄 원칙:'.\n"
        "- Number the four good requests 1 through 4 inside the quoted lines so later explanations map to them.\n"
        "- Reply 1 must explain why each of the four requests is good and include a concrete '- 활용:' line for each. Do not include the text 'Reply 1:', 'Reply 2:', or 'Reply 3:'.\n"
        "- Reply 2 must start with '예시 프롬프트:' and include four natural quoted Korean prompts corresponding to requests 1 through 4, not JSON and not a code block.\n"
        "- Reply 3 must start with '참고해서 볼 만한 것들:' and include only Korean-language technical blog posts or GitHub repositories directly related to today's topic. Link to the actual article or repository, never a product homepage.\n"
        "- Reference lines must be formatted as source title, newline full clickable URL beginning with https://, newline '- 볼 부분: ...'.\n"
        "- A candidate may include optional_verified_quote. It is optional, never mandatory. Use at most one quote only when it directly strengthens today's core workflow lesson.\n"
        "- Do not use a quote merely because a famous speaker is available. Prefer quote_used=false when the connection would feel decorative or needs a long explanation.\n"
        "- If using a quote, copy speaker_ko and quote_ko exactly, set quote_used=true and quote_id to the supplied id, and include the supplied source_url under '인용 원문:' in the final reply.\n"
        "- Practical reference links must remain Korean-language technical blog posts or GitHub repositories. A non-Korean URL is allowed only as the verified primary source under '인용 원문:'.\n"
        "- If no supplied optional_verified_quote is used, set quote_used=false and quote_id=\"\".\n"
        "- Do not use markdown code fences. Do not use bracketed mode labels such as '[초안 작성 모드]'.\n"
        "- If using a new feature topic, include official source links and concrete usage.\n"
        "- Do not invent facts. Use only the candidates below as factual sources.\n"
        "- Avoid repeating recent topic fingerprints.\n"
        "- Block drafts with the same failure_mode and same solution_pattern as recent history.\n"
        "- Same broad topic_pillar is allowed only if workflow_stage or solution_pattern is different.\n"
        "- Avoid the old winning angle based on '서론 써줘' unless the solution is clearly not the previous drafting solution.\n"
        "- Keep it short. No hype. No investment/product-buying claims.\n\n"
        "Required thread_text skeleton. Choose one hook style:\n"
        "A) 만약 [흔한 나쁜 요청]으로 AI에게 논문 작업을 맡기고 있다면\n"
        "   [결과가 왜 흐려지는지 한 줄]\n"
        "B) AI에게 [논문 작업]을 맡길 때\n"
        "   \"[넓은 요청]\"라고 쓰면\n"
        "   [결과가 왜 흐려지는지 한 줄]\n\n"
        "나쁜 요청:\n"
        "\"...\"\n\n"
        "좋은 요청:\n"
        "\"...\"\n"
        "\"...\"\n"
        "\"...\"\n"
        "\"...\"\n\n"
        "[plain principle sentence without label]\n"
        "---\n"
        "왜 좋은 요청일까요?\n"
        "1. [why request 1 is good]\n"
        "- 활용: [when/how to use it]\n"
        "2. [why request 2 is good]\n"
        "- 활용: [when/how to use it]\n"
        "3. [why request 3 is good]\n"
        "- 활용: [when/how to use it]\n"
        "4. [why request 4 is good]\n"
        "- 활용: [when/how to use it]\n"
        "---\n"
        "예시 프롬프트:\n"
        "\"[prompt for request 1]\"\n"
        "\"[prompt for request 2]\"\n"
        "\"[prompt for request 3]\"\n"
        "\"[prompt for request 4]\"\n"
        "---\n"
        "참고해서 볼 만한 것들:\n"
        "[source title]\n"
        "https://...\n"
        "- 볼 부분: ...\n\n"
        "Channel playbook:\n"
        f"{playbook}\n\n"
        "Recent post history to avoid or intentionally continue:\n"
        f"{json.dumps(recent_history, ensure_ascii=False, indent=2)}\n\n"
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
    parser.add_argument("--history-path", default="content-history.jsonl")
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
    recent_history = load_recent_history(Path(args.history_path))
    prompt = build_prompt(playbook, candidates, recent_history)
    payload = call_groq(api_key, args.model, prompt)
    text = extract_text(payload)
    data = extract_json(text)

    thread_text = str(data.get("thread_text", "")).strip()
    validate_thread(thread_text)

    candidate_by_url = {item.get("url"): item for item in candidates if item.get("url")}
    source_url = str(data.get("source_url") or "").strip()
    source_item = candidate_by_url.get(source_url) or candidates[0]
    quote_used = data.get("quote_used") is True
    quote_id = str(data.get("quote_id") or "").strip()
    quote_suggestion = validate_quote_selection(thread_text, data, source_item)

    output_path = Path(args.output_path)
    output_path.write_text(thread_text + "\n", encoding="utf-8")

    metadata = {
        "date": args.date,
        "model": args.model,
        "topic": data.get("topic", "research ai workflow"),
        "source_count": int(data.get("source_count", 0) or 0),
        "format": data.get("format", "A"),
        "source_name": data.get("source_name") or source_item.get("name") or source_item.get("title") or "",
        "source_url": source_url or source_item.get("url") or "",
        "series": data.get("series", ""),
        "series_part": data.get("series_part", ""),
        "public_theme": data.get("public_theme", ""),
        "topic_pillar": data.get("topic_pillar", ""),
        "workflow_stage": data.get("workflow_stage", ""),
        "failure_mode": data.get("failure_mode", ""),
        "solution_pattern": data.get("solution_pattern", ""),
        "bad_request": data.get("bad_request", ""),
        "quote_used": quote_used,
        "quote_id": quote_id,
        "quote_speaker": quote_suggestion.get("speaker", "") if quote_suggestion else "",
        "quote_source_url": quote_suggestion.get("source_url", "") if quote_suggestion else "",
    }
    metadata_path = Path(args.metadata_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {output_path}")
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
