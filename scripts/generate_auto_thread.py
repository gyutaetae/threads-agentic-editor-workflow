import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests


RESPONSES_URL = "https://api.groq.com/openai/v1/responses"
DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_PARTS = 4
MAX_CHARS = 500
AUTO_PUBLISH_QUALITY_SCORE = 85
DRAFT_QUALITY_SCORE = 70
DEFAULT_GENERATION_CANDIDATES = 3
SECTION_LABEL_RE = re.compile(r"(?im)^\s*(?:main|reply\s*\d+|reply\s*n|답글\s*\d+)\s*:\s*")
SEPARATOR_RE = re.compile(r"(?m)^\s*---\s*$")
URL_RE = re.compile(r"https?://\S+")
QUOTE_LINE_RE = re.compile(r"(?m)^\s*[\"“][^\"”]+[\"”]\s*$")
HYPE_WORDS = ["무조건", "혁명", "개발자 끝", "역대급", "미친 생산성", "뒤처집니다", "끝입니다"]
PRACTICAL_MARKERS = [
    "예시 프롬프트",
    "체크리스트",
    "기준",
    "모드",
    "규칙",
    "이런 방식으로 요청해보세요",
    "1.",
    "2.",
    "3.",
]
CONTENT_AXES = {
    "prompt_habit",
    "workflow_mode",
    "repo_teardown",
    "failure_prevention",
    "checklist",
    "official_update",
    "opinion",
}
FORMAT_TYPES = {
    "bad_to_better",
    "senior_first_move",
    "workflow_mode",
    "repo_lesson",
    "failure_case",
    "copy_checklist",
    "update_to_action",
    "short_opinion",
}
POST_GOALS = {"save", "comment", "share", "follow", "profile_visit"}
CANONICAL_STYLE_EXAMPLE = """만약
"앱 하나 만들어줘"
라고 사용하고 있다면,

검증 가능한 작업 단위를 agent에게 주지 못한다는 겁니다.

이런 방식으로 요청해보세요:
"이 failing test 하나만 고쳐줘"
"이 PR에서 위험한 변경만 찾아줘"
"이 함수 타입 오류만 정리해줘"

---

왜 이게 중요하냐면,
AI agent는 애매한 큰 목표보다
검증 가능한 작은 티켓에서 훨씬 잘 작동한다.

사람 팀도 마찬가지다.
"서비스 개선해줘"보다
"로그인 실패 케이스 재현하고 테스트 하나 추가해줘"가 훨씬 낫다.

agent도 결국 작업 단위가 좋아야 일을 잘한다.

---

내가 생각하는 좋은 agent 작업 조건:

1. 범위가 작다
2. 성공 기준이 보인다
3. 테스트나 diff로 검증 가능하다
4. 실패해도 되돌릴 수 있다
5. 사람이 마지막 판단을 할 수 있다

AI agent 시대의 실력은
명령어가 아니라 작업 분해에서 나온다."""

FORMAT_GUIDE = {
    "bad_to_better": "Show one bad agent usage and three better requests. Use the phrase '이런 방식으로 요청해보세요:' in Main.",
    "senior_first_move": "Explain what a senior developer asks the agent before implementation. Main should be easy, replies should add decision criteria and a copyable prompt.",
    "workflow_mode": "Turn the idea into repeatable modes such as 탐색 모드, 수정 모드, 검증 모드, 리뷰 모드, 롤백 모드.",
    "repo_lesson": "Teach what to copy from the repo's structure, tests, docs, configs, or examples. Do not turn it into generic repo news.",
    "failure_case": "Start from a common failure and give a prevention rule. Keep it calm and practical.",
    "copy_checklist": "Make a reusable checklist or decision criteria that developers can save.",
    "update_to_action": "Translate the official update into a concrete developer action. Separate source fact from our interpretation.",
    "short_opinion": "Write a concise account-level viewpoint with one practical takeaway.",
}

HOOK_PATTERNS = {
    "bad_usage": re.compile(r"만약|라고 사용하고 있다면|시키고 있다면"),
    "personal_diary": re.compile(r"오늘|내가|요즘 내가|23살|논문"),
    "quote_idea": re.compile(r"Feynman|Karpathy|Paul Graham|Andrew Ng|Sam Altman|말|요지"),
    "repo_diagnostic": re.compile(r"GitHub|repo|star|README"),
    "direct_claim": re.compile(r"AI agent|agent|프롬프트|작업 단위"),
}
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


def read_optional_text(path: Path, max_chars: int = 4000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()[:max_chars]


def classify_hook_pattern(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    for name, pattern in HOOK_PATTERNS.items():
        if pattern.search(first_line):
            return name
    return "other"


def recent_hook_patterns(metrics_path: Path, limit: int = 3) -> list[dict]:
    if not metrics_path.exists():
        return []
    try:
        with metrics_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [row for row in csv.DictReader(handle) if row.get("hook") or row.get("main_text")]
    except Exception:
        return []

    recent = rows[-limit:]
    return [
        {
            "hook": row.get("hook") or next((line.strip() for line in (row.get("main_text") or "").splitlines() if line.strip()), ""),
            "pattern": classify_hook_pattern(row.get("hook") or row.get("main_text") or ""),
            "format_type": row.get("format_type") or row.get("format") or "",
            "content_axis": row.get("content_axis") or "",
        }
        for row in recent
    ]


def load_quote_bank(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict) and item.get("speaker")]


def select_quote_context(candidate: dict, quote_bank: list[dict]) -> dict | None:
    if not quote_bank:
        return None
    text = item_text_for_quote(candidate)
    scored = []
    for item in quote_bank:
        tags = [str(tag).lower() for tag in item.get("tags") or []]
        tag_score = sum(1 for tag in tags if tag and tag.replace("_", " ") in text)
        seed = f"{candidate.get('url') or candidate.get('title')}-{item.get('id') or item.get('speaker')}"
        stable_tiebreak = int(hashlib.sha1(seed.encode("utf-8")).hexdigest()[:6], 16)
        scored.append((tag_score, -stable_tiebreak, item))
    scored.sort(reverse=True)
    selected = scored[0][2]
    return {
        "speaker": selected.get("speaker"),
        "quote": selected.get("quote") or "",
        "idea_summary": selected.get("idea_summary") or "",
        "source_url": selected.get("source_url") or "",
        "use_as": selected.get("use_as") or "paraphrase",
        "angle": selected.get("angle") or "",
        "rule": "Use only if it improves the hook. Prefer paraphrase unless quote is non-empty and verified.",
    }


def item_text_for_quote(candidate: dict) -> str:
    return " ".join(
        [
            candidate.get("title") or "",
            candidate.get("description") or "",
            candidate.get("readme_summary") or "",
            candidate.get("our_angle") or "",
            candidate.get("content_axis") or "",
            candidate.get("format_type") or "",
        ]
    ).lower()


def safe_enum(value: str, allowed: set[str], fallback: str) -> str:
    value = str(value or "").strip()
    return value if value in allowed else fallback


def analyze_candidate(candidate: dict) -> dict:
    text = " ".join(
        [
            candidate.get("title") or "",
            candidate.get("description") or "",
            candidate.get("readme_summary") or "",
            candidate.get("our_angle") or "",
        ]
    ).strip()
    source_facts = [
        f"source_type={candidate.get('source_type', 'unknown')}",
        f"title={candidate.get('title') or candidate.get('name') or 'unknown'}",
        f"url={candidate.get('url') or ''}",
    ]
    if candidate.get("stars"):
        source_facts.append(f"stars={candidate.get('stars')} as popularity signal only")
    if candidate.get("language"):
        source_facts.append(f"language={candidate.get('language')}")

    practical_angle = candidate.get("our_angle") or "AI coding agent workflow lesson"
    if "test" in text.lower() or "eval" in text.lower():
        developer_action = "검증 기준을 먼저 정하고 agent에게 작은 작업 단위로 맡긴다."
    elif "mcp" in text.lower() or "tool" in text.lower():
        developer_action = "도구 연결 자체보다 agent에게 어떤 작업 환경을 넘길지 정한다."
    elif "review" in text.lower() or "pr" in text.lower():
        developer_action = "구현 전에 영향 범위와 리뷰 기준부터 agent에게 분석시킨다."
    else:
        developer_action = "큰 요청을 바로 맡기지 말고 범위, 기준, 검증 방법을 분리한다."

    return {
        "summary": text[:700],
        "source_facts": source_facts,
        "practical_angle": practical_angle,
        "developer_action": developer_action,
    }


def select_content_format(candidate: dict) -> dict:
    content_axis = safe_enum(candidate.get("content_axis"), CONTENT_AXES, "prompt_habit")
    format_type = safe_enum(candidate.get("format_type"), FORMAT_TYPES, "bad_to_better")
    post_goal = safe_enum(candidate.get("post_goal"), POST_GOALS, "save")
    return {
        "content_axis": content_axis,
        "format_type": format_type,
        "post_goal": post_goal,
        "format_reason": candidate.get("format_reason")
        or "Use the format that best turns the source into a practical developer action.",
        "format_guide": FORMAT_GUIDE.get(format_type, FORMAT_GUIDE["bad_to_better"]),
    }


def metrics_feedback(metrics_path: Path, limit: int = 25) -> dict:
    if not metrics_path.exists():
        return {
            "available": False,
            "guidance": "No metrics file found. Prefer save-worthy practical formats over generic news.",
        }

    try:
        with metrics_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))[-limit:]
    except Exception as exc:
        return {"available": False, "guidance": f"Metrics could not be read: {exc}"}

    if not rows:
        return {
            "available": False,
            "guidance": "Metrics file is empty. Prefer copyable prompts, checklists, and workflow modes.",
        }

    by_format: dict[str, int] = {}
    by_axis: dict[str, int] = {}
    by_slot: dict[str, int] = {}
    by_experiment: dict[str, int] = {}
    for row in rows:
        engagement = sum(
            int(row.get(key) or 0)
            for key in ["audience_replies", "reposts", "quotes", "follows_gained", "saves", "profile_visits"]
            if str(row.get(key) or "0").isdigit()
        )
        if engagement == 0 and str(row.get("likes") or "0").isdigit():
            engagement = int(row.get("likes") or 0)
        fmt = row.get("format_type") or row.get("format") or "unknown"
        axis = row.get("content_axis") or "unknown"
        slot = row.get("post_slot") or "unknown"
        experiment = row.get("experiment_group") or "unknown"
        by_format[fmt] = by_format.get(fmt, 0) + engagement
        by_axis[axis] = by_axis.get(axis, 0) + engagement
        by_slot[slot] = by_slot.get(slot, 0) + engagement
        by_experiment[experiment] = by_experiment.get(experiment, 0) + engagement

    best_format = max(by_format, key=by_format.get) if by_format else "unknown"
    best_axis = max(by_axis, key=by_axis.get) if by_axis else "unknown"
    best_slot = max(by_slot, key=by_slot.get) if by_slot else "unknown"
    best_experiment = max(by_experiment, key=by_experiment.get) if by_experiment else "unknown"
    return {
        "available": True,
        "best_format": best_format,
        "best_axis": best_axis,
        "best_slot": best_slot,
        "best_experiment": best_experiment,
        "guidance": (
            f"Recent engagement favors format={best_format}, axis={best_axis}, "
            f"slot={best_slot}, experiment={best_experiment}. "
            "Use this as a weak signal until at least 20 posts have 24h/72h metrics. "
            "Do not optimize only for views or likes."
        ),
    }


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


def strip_section_label(text: str) -> str:
    lines = text.strip().splitlines()
    while lines and SECTION_LABEL_RE.fullmatch(lines[0].strip()):
        lines.pop(0)
    if lines:
        lines[0] = SECTION_LABEL_RE.sub("", lines[0], count=1)
    return "\n".join(lines).strip()


def normalize_part(part: str) -> str:
    part = strip_section_label(part)
    text = "\n".join(line.rstrip() for line in part.splitlines()).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def normalize_thread_text(thread_text: str) -> str:
    raw_parts = [part.strip() for part in SEPARATOR_RE.split(thread_text.strip()) if part.strip()]
    parts = [normalize_part(part) for part in raw_parts]
    parts = [part for part in parts if part]
    return "\n---\n".join(parts)


def validate_thread(thread_text: str) -> None:
    parts = [part.strip() for part in SEPARATOR_RE.split(thread_text.strip()) if part.strip()]
    if not parts:
        raise SystemExit("Generated thread has no parts.")
    if len(parts) != MAX_PARTS:
        raise SystemExit(f"Generated thread has {len(parts)} parts; expected exactly {MAX_PARTS} parts.")
    for index, part in enumerate(parts, start=1):
        if SECTION_LABEL_RE.match(part):
            raise SystemExit(f"Generated part {index} still has a drafting label such as Main: or Reply n:.")
        if len(part) > MAX_CHARS:
            raise SystemExit(f"Generated part {index} is {len(part)} chars; limit is {MAX_CHARS}.")
    if URL_RE.search(parts[0]):
        raise SystemExit("Generated main post contains a source link; move links to Reply 3.")
    if not has_practical_element(thread_text):
        raise SystemExit("Generated thread is missing a copyable prompt, checklist, criteria, workflow mode, or failure-prevention rule.")
    if any(word in thread_text for word in HYPE_WORDS):
        raise SystemExit("Generated thread contains banned hype language.")
    joined = "\n".join(parts)
    for forbidden in FORBIDDEN_TEXT:
        if forbidden in joined:
            raise SystemExit(f"Generated thread contains forbidden label: {forbidden}")
    if "```" in joined or '{"role"' in joined or '"tools"' in joined:
        raise SystemExit("Generated thread uses a code block or JSON-style prompt; use natural quoted Korean prompt text.")
    if "나쁜 요청:" not in parts[0] or "좋은 요청:" not in parts[0]:
        raise SystemExit("Generated main post must include both '나쁜 요청:' and '좋은 요청:' sections.")
    good_request = parts[0].split("좋은 요청:", 1)[1]
    if len(QUOTE_LINE_RE.findall(good_request)) < 4:
        raise SystemExit("Generated main post must include at least four quoted good-request lines.")
    for number in ("1", "2", "3", "4"):
        if f"{number}." not in parts[1]:
            raise SystemExit(f"Generated explanation reply is missing good request {number}.")
    if parts[1].count("- 활용:") < 4:
        raise SystemExit("Generated explanation reply must include four '- 활용:' lines.")
    if not parts[2].startswith("예시 프롬프트:"):
        raise SystemExit("Generated third part must start with '예시 프롬프트:'.")
    if len(QUOTE_LINE_RE.findall(parts[2])) < 4:
        raise SystemExit("Generated prompt reply must include four quoted prompt examples.")
    if not parts[3].startswith("참고해서 볼 만한 것들:"):
        raise SystemExit("Generated final reply must start with '참고해서 볼 만한 것들:'.")
    if not URL_RE.search(parts[3]):
        raise SystemExit("Generated reference reply must include at least one full clickable URL.")
    if "notebooklm.google" in parts[3].lower():
        raise SystemExit("Generated reference reply must link an actual example, not the NotebookLM homepage.")
    if "- 볼 부분:" not in parts[3]:
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


def rank_candidate(item: dict, post_slot: str = "morning") -> tuple[int, int]:
    if post_slot == "evening":
        preferred = {"workflow_mode", "repo_teardown", "official_update", "checklist"}
    else:
        preferred = {"prompt_habit", "failure_prevention", "checklist"}

    score = int(item.get("score", {}).get("total") or 0)
    axis_bonus = 8 if item.get("content_axis") in preferred else 0
    return score + axis_bonus, score


def choose_candidates(candidates: list[dict], post_slot: str = "morning", count: int = DEFAULT_GENERATION_CANDIDATES) -> list[dict]:
    ranked = sorted(candidates, key=lambda item: rank_candidate(item, post_slot), reverse=True)
    selected = []
    seen_urls = set()
    for item in ranked:
        url = str(item.get("url") or "")
        if url and url in seen_urls:
            continue
        selected.append(item)
        if url:
            seen_urls.add(url)
        if len(selected) >= count:
            break
    return selected or ranked[:1]


def build_prompt(
    playbook: str,
    candidate: dict,
    analysis: dict,
    routing: dict,
    feedback: dict,
    quote_context: dict | None,
    recent_hooks: list[dict],
    weekly_memory: str,
) -> str:
    compact_candidate = {
        "title": candidate.get("title"),
        "url": candidate.get("url"),
        "source_type": candidate.get("source_type"),
        "category": candidate.get("category"),
        "description": candidate.get("description"),
        "readme_summary": candidate.get("readme_summary"),
        "our_angle": candidate.get("our_angle"),
        "score": candidate.get("score", {}).get("total"),
        "score_breakdown": candidate.get("score", {}),
        "risk": candidate.get("risk"),
        "facts_vs_interpretation": candidate.get("fact_boundary"),
        "optional_verified_quote": candidate.get("quote_suggestion"),
    }

    return (
        "Create exactly one Korean Threads chain for @gyu_in_black.\n"
        "Follow the channel playbook and selected content format exactly.\n\n"
        "Hard constraints:\n"
        "- Return JSON only.\n"
        "- JSON keys: thread_text, topic, source_count, format, source_name, source_url, quote_used, quote_id.\n"
        "- Also return fingerprint keys: series, series_part, public_theme, topic_pillar, workflow_stage, failure_mode, solution_pattern, bad_request.\n"
        "- thread_text must use --- between main and replies.\n"
        "- Do not include labels such as Main:, Reply 1:, Reply n:, or 제목: in thread_text.\n"
        "- Use short, sharp Korean Threads style: practical, calm, developer-to-developer.\n"
        "- Exactly 4 parts total: main + 3 replies.\n"
        "- Each part must be under 500 Korean characters.\n"
        "- Main must be easy to understand and must not contain external links.\n"
        "- Main post must include '나쁜 요청:' with one quoted bad request.\n"
        "- Main post must include '좋은 요청:' with at least four short quoted good-request lines.\n"
        "- Number the four good requests 1 through 4 inside the quoted lines so later explanations map to them.\n"
        "- Reply 1 must explain why each of the four requests is good and include a concrete '- 활용:' line for each.\n"
        "- Reply 2 must start with '예시 프롬프트:' and include four natural quoted Korean prompts corresponding to requests 1 through 4, not JSON and not a code block.\n"
        "- Reply 3 must start with '참고해서 볼 만한 것들:' and include source links plus how to apply each source.\n"
        "- Reference lines must include a full clickable URL beginning with https:// and a '- 볼 부분: ...' line.\n"
        "- Choose the first line naturally: either a '만약 ...' diagnostic hook or a natural first line like 'AI에게 논문 초안을 맡길 때'.\n"
        "- Add human texture: a personal proof line, failed request, quote/idea hook, or direct diagnostic. Do not use the same surface every time.\n"
        "- If using personal experience, keep it to 1-2 lines and then move to a practical example.\n"
        "- If using quote_context, use it as a short doorway into the workflow. Prefer paraphrase unless quote_context.quote is non-empty.\n"
        "- If using a verified quote, copy speaker_ko and quote_ko exactly, set quote_used=true and quote_id to the supplied id, and include the supplied source_url under '인용 원문:' in the final reply.\n"
        "- Do not use a quote merely because a famous speaker is available. Prefer quote_used=false when the connection feels decorative or needs a long explanation.\n"
        "- If no supplied quote_context is used, set quote_used=false and quote_id=\"\".\n"
        "- Avoid matching the recent hook patterns when possible.\n"
        "- Never use hype words: 무조건, 혁명, 개발자 끝, 역대급, 미친 생산성, 이거 모르면 뒤처집니다.\n"
        "- Do not use markdown code fences. Do not use bracketed mode labels such as '[초안 작성 모드]'.\n"
        "- Separate source facts from account interpretation.\n"
        "- Do not invent facts. Use only the candidates below as factual sources.\n"
        "- GitHub stars are popularity signals only, never quality proof.\n\n"
        "Required thread_text skeleton:\n"
        "[natural diagnostic hook]\n\n"
        "나쁜 요청:\n"
        "\"...\"\n\n"
        "좋은 요청:\n"
        "\"1. ...\"\n"
        "\"2. ...\"\n"
        "\"3. ...\"\n"
        "\"4. ...\"\n\n"
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
        "Canonical style example for bad_to_better only. Copy the compact line shape, not the topic:\n"
        f"{CANONICAL_STYLE_EXAMPLE}\n\n"
        "Selected routing:\n"
        f"{json.dumps(routing, ensure_ascii=False, indent=2)}\n\n"
        "Candidate analysis:\n"
        f"{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        "Metrics feedback:\n"
        f"{json.dumps(feedback, ensure_ascii=False, indent=2)}\n\n"
        "Recent hook patterns to avoid repeating:\n"
        f"{json.dumps(recent_hooks, ensure_ascii=False, indent=2)}\n\n"
        "Optional quote/idea context:\n"
        f"{json.dumps(quote_context or {}, ensure_ascii=False, indent=2)}\n\n"
        "Weekly editorial memory:\n"
        f"{weekly_memory or 'No weekly memory yet.'}\n\n"
        "Channel playbook:\n"
        f"{playbook}\n\n"
        "Selected candidate:\n"
        f"{json.dumps(compact_candidate, ensure_ascii=False, indent=2)}"
    )


def has_practical_element(thread_text: str) -> bool:
    return any(marker in thread_text for marker in PRACTICAL_MARKERS)


def quality_gate(thread_text: str, routing: dict, recent_hooks: list[dict] | None = None) -> dict:
    parts = [part.strip() for part in SEPARATOR_RE.split(thread_text.strip()) if part.strip()]
    score = 100
    reasons = []
    suggestions = []

    if not parts:
        return {
            "quality_score": 0,
            "decision": "discard",
            "reasons": ["No thread parts were generated."],
            "revision_suggestions": ["Generate a main post and at least one practical reply."],
        }

    main = parts[0]
    joined = "\n".join(parts)
    main_first_line = next((line.strip() for line in main.splitlines() if line.strip()), "")
    hook_pattern = classify_hook_pattern(main)
    recent_patterns = [item.get("pattern") for item in (recent_hooks or []) if item.get("pattern")]

    if len(main_first_line) < 8:
        score -= 12
        reasons.append("First line is weak or too short.")
        suggestions.append("Open with a sharper developer mistake or senior-workflow contrast.")
    if not has_practical_element(joined):
        score -= 25
        reasons.append("Thread has no copyable prompt/checklist/criteria/workflow mode/failure rule.")
        suggestions.append("Add a reusable prompt, checklist, decision criteria, workflow mode, or failure-prevention rule.")
    if URL_RE.search(main):
        score -= 18
        reasons.append("Main contains an external link.")
        suggestions.append("Move source links to Reply 3.")
    if any(word in joined for word in HYPE_WORDS):
        score -= 25
        reasons.append("Thread contains banned hype language.")
        suggestions.append("Replace hype with concrete developer impact.")
    if "AI가 중요" in joined or "AI 시대" in main and "기준" not in joined:
        score -= 12
        reasons.append("Thread risks generic AI advice.")
        suggestions.append("Ground the point in one concrete work unit or failure mode.")
    if len(parts) > MAX_PARTS:
        score -= 30
        reasons.append("Thread has too many replies.")
    if any(len(part) > MAX_CHARS for part in parts):
        score -= 30
        reasons.append("At least one part exceeds Threads length limits.")
    if routing.get("format_type") == "repo_lesson" and "적용" not in joined:
        score -= 10
        reasons.append("Repo lesson has no application note.")
        suggestions.append("Add a short '적용:' line explaining what to copy into a workflow.")
    if routing.get("format_type") == "update_to_action" and "해석" not in joined and "중요한 건" not in joined:
        score -= 10
        reasons.append("Official update is not clearly translated into account interpretation.")
    if len(parts) >= 2 and len(parts[0]) > 360:
        score -= 8
        reasons.append("Main is too dense for an easy hook.")
        suggestions.append("Move details to Reply 1 or Reply 2.")
    if len(recent_patterns) >= 3 and len(set(recent_patterns[-3:])) == 1 and hook_pattern == recent_patterns[-1]:
        score -= 18
        reasons.append(f"Factory-feel risk: hook pattern '{hook_pattern}' repeats the last 3 posts.")
        suggestions.append("Use a personal proof line, quote/idea hook, failed-request hook, or direct claim instead.")
    if "오늘" not in joined and "내가" not in joined and "요즘" not in joined and "Feynman" not in joined and "Karpathy" not in joined and "Paul Graham" not in joined:
        score -= 5
        reasons.append("Thread has little human texture.")
        suggestions.append("Add one short personal-use line or idea hook without turning it into a diary.")

    score = max(0, min(100, score))
    if score >= AUTO_PUBLISH_QUALITY_SCORE:
        decision = "publish"
    elif score >= DRAFT_QUALITY_SCORE:
        decision = "draft"
    else:
        decision = "discard"

    if not reasons:
        reasons.append("Quality gate passed.")
    return {
        "quality_score": score,
        "decision": decision,
        "reasons": reasons,
        "revision_suggestions": suggestions,
    }


def write_review_artifact(review_dir: Path, date: str, post_slot: str, label: str, thread_text: str) -> Path:
    review_dir.mkdir(parents=True, exist_ok=True)
    path = review_dir / f"{date}-{post_slot}-{label}-thread.txt"
    path.write_text(thread_text + "\n", encoding="utf-8")
    return path


def retry_delay_seconds(response: requests.Response) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return max(1.0, float(retry_after))
        except ValueError:
            pass

    match = re.search(r"try again in ([0-9.]+)s", response.text, re.I)
    if match:
        return max(1.0, float(match.group(1)))
    return 30.0


def call_groq(api_key: str, model: str, prompt: str) -> dict:
    for attempt in range(1, 4):
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
        if response.ok:
            return response.json()
        if response.status_code == 429 and attempt < 3:
            delay = retry_delay_seconds(response) + 2
            print(f"Groq rate limited; retrying in {delay:.1f}s (attempt {attempt}/3).")
            time.sleep(delay)
            continue
        raise SystemExit(f"Groq API error {response.status_code}:\n{response.text}")

    raise SystemExit("Groq API did not return a response after retries.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one approved Threads chain with Groq.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--candidates-path", required=True)
    parser.add_argument("--playbook-path", default="docs/threads-channel-playbook.md")
    parser.add_argument("--history-path", default="content-history.jsonl")
    parser.add_argument("--output-path", default="approved-thread-chain.txt")
    parser.add_argument("--metadata-path", default="daily-editor/auto-thread-metadata.json")
    parser.add_argument("--metrics-path", default="threads-post-metrics.csv")
    parser.add_argument("--quote-bank-path", default="data/quote_bank.json")
    parser.add_argument("--weekly-memory-path", default="docs/weekly-editorial-memory.md")
    parser.add_argument("--review-dir", default="daily-editor/review")
    parser.add_argument("--post-slot", choices=["morning", "evening"], default=os.environ.get("POST_SLOT", "morning"))
    parser.add_argument("--posts-per-day", type=int, choices=[1, 2], default=int(os.environ.get("POSTS_PER_DAY", "1")))
    parser.add_argument("--experiment-group", default=os.environ.get("EXPERIMENT_GROUP", "manual"))
    parser.add_argument("--generation-candidates", type=int, default=int(os.environ.get("GENERATION_CANDIDATES", str(DEFAULT_GENERATION_CANDIDATES))))
    parser.add_argument("--model", default=os.environ.get("GROQ_MODEL", DEFAULT_MODEL))
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY is required.")

    candidates = read_json(Path(args.candidates_path))
    if not isinstance(candidates, list) or not candidates:
        raise SystemExit(f"No candidates found in {args.candidates_path}")

    playbook = read_text(Path(args.playbook_path))
    feedback = metrics_feedback(Path(args.metrics_path))
    recent_hooks = recent_hook_patterns(Path(args.metrics_path))
    quote_bank = load_quote_bank(Path(args.quote_bank_path))
    weekly_memory = read_optional_text(Path(args.weekly_memory_path), max_chars=3000)
    review_dir = Path(args.review_dir)
    selected_candidates = choose_candidates(candidates, args.post_slot, max(1, args.generation_candidates))
    candidate_by_url = {item.get("url"): item for item in candidates if item.get("url")}
    generated_options = []

    for index, selected_candidate in enumerate(selected_candidates, start=1):
        analysis = analyze_candidate(selected_candidate)
        routing = select_content_format(selected_candidate)
        quote_context = select_quote_context(selected_candidate, quote_bank)
        prompt = build_prompt(playbook, selected_candidate, analysis, routing, feedback, quote_context, recent_hooks, weekly_memory)
        payload = call_groq(api_key, args.model, prompt)
        text = extract_text(payload)
        try:
            data = extract_json(text)
        except json.JSONDecodeError as exc:
            generated_options.append(
                {
                    "option": index,
                    "candidate_title": selected_candidate.get("title"),
                    "candidate_url": selected_candidate.get("url"),
                    "quality_score": 0,
                    "quality_decision": "discard",
                    "quality_reasons": [f"Groq returned malformed JSON: {exc}"],
                    "raw_text_preview": text[:1200],
                }
            )
            continue

        thread_text = normalize_thread_text(str(data.get("thread_text", "")).strip())
        try:
            validate_thread(thread_text)
            gate = quality_gate(thread_text, routing, recent_hooks)
        except SystemExit as exc:
            gate = {
                "quality_score": 0,
                "decision": "discard",
                "reasons": [str(exc)],
                "revision_suggestions": ["Regenerate with stronger format compliance."],
            }

        generated_options.append(
            {
                "option": index,
                "candidate": selected_candidate,
                "analysis": analysis,
                "routing": routing,
                "quote_context": quote_context,
                "data": data,
                "thread_text": thread_text,
                "quality_score": gate["quality_score"],
                "quality_decision": gate["decision"],
                "quality_reasons": gate["reasons"],
                "revision_suggestions": gate["revision_suggestions"],
            }
        )

    if not generated_options:
        raise SystemExit("No thread options were generated.")

    best = max(generated_options, key=lambda option: int(option.get("quality_score") or 0))
    if "thread_text" not in best:
        metadata_path = Path(args.metadata_path)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps({"date": args.date, "model": args.model, "generated_options": generated_options}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit("All generated options failed before thread extraction.")

    selected_candidate = best["candidate"]
    analysis = best["analysis"]
    routing = best["routing"]
    data = best["data"]
    thread_text = best["thread_text"]
    gate = {
        "quality_score": best["quality_score"],
        "decision": best["quality_decision"],
        "reasons": best["quality_reasons"],
        "revision_suggestions": best["revision_suggestions"],
    }
    source_url = str(data.get("source_url") or "").strip()
    source_item = candidate_by_url.get(source_url) or selected_candidate
    quote_used = data.get("quote_used") is True
    quote_id = str(data.get("quote_id") or "").strip()
    quote_suggestion = validate_quote_selection(thread_text, data, source_item)

    metadata = {
        "date": args.date,
        "model": args.model,
        "post_slot": args.post_slot,
        "posts_per_day": args.posts_per_day,
        "experiment_group": args.experiment_group,
        "generation_candidates": len(selected_candidates),
        "selected_option": best["option"],
        "topic": data.get("topic", "agent workflow"),
        "source_count": int(data.get("source_count", 0) or 0),
        "format": data.get("format") or routing["format_type"],
        "content_axis": routing["content_axis"],
        "format_type": routing["format_type"],
        "post_goal": routing["post_goal"],
        "format_reason": routing["format_reason"],
        "final_candidate_score": selected_candidate.get("score", {}).get("total", 0),
        "quality_score": gate["quality_score"],
        "quality_decision": gate["decision"],
        "quality_reasons": gate["reasons"],
        "revision_suggestions": gate["revision_suggestions"],
        "analysis": analysis,
        "metrics_feedback": feedback,
        "recent_hooks": recent_hooks,
        "quote_context": best.get("quote_context"),
        "generated_options": [
            {
                "option": option.get("option"),
                "candidate_title": (option.get("candidate") or {}).get("title") or option.get("candidate_title"),
                "candidate_url": (option.get("candidate") or {}).get("url") or option.get("candidate_url"),
                "content_axis": (option.get("routing") or {}).get("content_axis"),
                "format_type": (option.get("routing") or {}).get("format_type"),
                "quality_score": option.get("quality_score"),
                "quality_decision": option.get("quality_decision"),
                "quality_reasons": option.get("quality_reasons"),
            }
            for option in generated_options
        ],
        "source_name": data.get("source_name") or source_item.get("name") or source_item.get("title") or "",
        "source_url": source_url or source_item.get("url") or "",
        "source_type": source_item.get("source_type", ""),
        "hook_text": next((line.strip() for line in thread_text.splitlines() if line.strip()), ""),
        "main_text": thread_text.split("\n---\n", 1)[0],
        "reply_count": max(len([part for part in SEPARATOR_RE.split(thread_text) if part.strip()]) - 1, 0),
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

    if gate["decision"] == "publish":
        output_path = Path(args.output_path)
        output_path.write_text(thread_text + "\n", encoding="utf-8")
        print(f"Wrote {output_path}")
    elif gate["decision"] == "draft":
        draft_path = write_review_artifact(review_dir, args.date, args.post_slot, "draft", thread_text)
        print(f"Saved draft for review: {draft_path}")
        print(json.dumps(metadata, ensure_ascii=False))
        return 2
    else:
        rejected_path = write_review_artifact(review_dir, args.date, args.post_slot, "rejected", thread_text)
        print(f"Rejected generated thread: {rejected_path}")
        print(json.dumps(metadata, ensure_ascii=False))
        return 3

    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

