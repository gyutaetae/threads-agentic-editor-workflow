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


CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"
MIN_PARTS = 1
MAX_PARTS = 4
MAX_CHARS = 500
AUTO_PUBLISH_QUALITY_SCORE = 85
DRAFT_QUALITY_SCORE = 70
DEFAULT_GENERATION_CANDIDATES = 1
DEFAULT_MAX_OUTPUT_TOKENS = 1200
PLAYBOOK_PROMPT_CHARS = 5000
LEARNINGS_PROMPT_CHARS = 2500
SKILL_LIBRARY_PROMPT_CHARS = 3500
WEEKLY_MEMORY_PROMPT_CHARS = 1500
SECTION_LABEL_RE = re.compile(r"(?im)^\s*(?:main|reply\s*\d+|reply\s*n|답글\s*\d+)\s*:\s*")
SEPARATOR_RE = re.compile(r"(?m)^\s*---\s*$")
URL_RE = re.compile(r"https?://\S+")
QUOTE_LINE_RE = re.compile(r"(?m)^\s*[\"“][^\"”]+[\"”]\s*$")
BRACKET_HEADING_RE = re.compile(r"^\[[^\]\n]{4,80}\]\s*(?:\n|$)")
HYPE_WORDS = ["무조건", "혁명", "논문 끝", "개발자 끝", "역대급", "미친 생산성", "뒤처집니다", "끝입니다"]
PRACTICAL_MARKERS = [
    "예시 프롬프트",
    "바로 써볼 프롬프트",
    "오늘 적용할 문장",
    "AI agent에게 이렇게 시켜보세요",
    "논문 읽을 때 붙여 넣을 문장",
    "다음 요약 전에 써볼 질문",
    "체크리스트",
    "기준",
    "모드",
    "규칙",
    "이런 방식으로 요청해보세요",
    "claim",
    "evidence",
    "citation",
    "limitation",
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
    "workflow_observation",
    "failed_agent_run",
    "better_prompt_pattern",
    "research_checklist",
    "agent_role_split",
    "tiny_source_case",
    "weekly_review_advice",
}
POST_GOALS = {"save", "comment", "share", "follow", "profile_visit"}
CANONICAL_STYLE_EXAMPLE = """AI에게 논문 요약을 맡길 때
"이 논문 요약해줘"라고 쓰면
초록을 다시 쓴 글이 나올 가능성이 큽니다.

나쁜 요청:
"이 논문 요약해줘"

좋은 요청:
"핵심 기여를 기존 연구와 분리해줘"
"방법을 재현 가능한 단계로 나눠줘"
"주장을 받치는 표, 그림, 실험을 연결해줘"
"저자가 말한 한계와 내가 의심할 점을 분리해줘"

좋은 요약은 짧은 글이 아니라
검증 가능한 연구 노트입니다.
---
[논문 요약은 4칸으로 나눕니다]
실전에서는 논문 요약을 4칸으로 나눕니다.
1. Contribution: 무엇을 주장했나
2. Method: 어떻게 증명하려 했나
3. Evidence: 어떤 실험/표/그림이 받치나
4. Limitation: 어디까지 믿어야 하나
---
[복사해서 쓸 프롬프트]
예시 프롬프트:
"이 논문의 main claim을 한 문장으로 쓰고, 근거 문단 위치를 붙여줘."
"method를 내가 재현할 순서대로 5단계로 나눠줘."
"claim마다 figure, table, experiment를 연결해줘."
"limitation과 내가 추가로 검증해야 할 gap을 분리해줘."
---
[볼 부분이 있는 링크만 남깁니다]
참고해서 볼 만한 것들:
https://github.com/gagyeomkim/Deep-Learning-Paper-Review-and-Practice
- 볼 부분: 리뷰를 요약, 코드, 발표 자료로 잇는 기록 구조"""

LEGACY_FORMAT_MAP = {
    "bad_to_better": "better_prompt_pattern",
    "senior_first_move": "workflow_observation",
    "workflow_mode": "agent_role_split",
    "repo_lesson": "tiny_source_case",
    "failure_case": "failed_agent_run",
    "copy_checklist": "research_checklist",
    "update_to_action": "tiny_source_case",
    "short_opinion": "workflow_observation",
}
AXIS_FORMAT_MAP = {
    "prompt_habit": "better_prompt_pattern",
    "workflow_mode": "agent_role_split",
    "repo_teardown": "tiny_source_case",
    "failure_prevention": "failed_agent_run",
    "checklist": "research_checklist",
    "official_update": "tiny_source_case",
    "opinion": "workflow_observation",
}
FORMAT_GUIDE = {
    "workflow_observation": "Start from one concrete paper-workflow judgment. Show why it matters, then add one reusable prompt or verification question.",
    "failed_agent_run": "Show a plausible AI-agent failure in paper work and the corrected work instruction. Do not invent first-person experience unless provided.",
    "better_prompt_pattern": "Turn a vague research request into a precise research prompt. The bad/good request structure is allowed but not required.",
    "research_checklist": "Give criteria a researcher can save and reuse to verify AI output.",
    "agent_role_split": "Split one broad paper task into agent roles such as reader, synthesizer, critic, and editor.",
    "tiny_source_case": "Translate one paper, repo, or official source into a reusable research workflow. Keep source facts separate from account interpretation.",
    "weekly_review_advice": "Friday evening only: derive one advice from the last 7 days of posts. Use a verified Korean quote only when it genuinely fits; otherwise publish a general weekly review.",
}
HUMAN_SIGNAL_TYPES = {
    "summary_suspicion",
    "citation_doubt",
    "literature_overload",
    "draft_without_argument",
    "evidence_missing",
    "agent_role_confusion",
    "reviewer_anxiety",
    "method_understanding_gap",
}

HOOK_PATTERNS = {
    "bad_usage": re.compile(r"만약|라고 사용하고 있다면|시키고 있다면"),
    "personal_diary": re.compile(r"오늘|내가|요즘 내가|23살|논문"),
    "quote_idea": re.compile(r"Feynman|Karpathy|Paul Graham|Andrew Ng|Sam Altman|말|요지"),
    "repo_diagnostic": re.compile(r"GitHub|repo|star|README"),
    "direct_claim": re.compile(r"논문|요약|citation|reference|evidence|claim|프롬프트|연구 노트"),
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


def read_text(path: Path, max_chars: int | None = None) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if max_chars is not None:
        return text[:max_chars]
    return text


def read_json(path: Path) -> object:
    return json.loads(read_text(path))


def read_optional_text(path: Path, max_chars: int = 4000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()[:max_chars]


def read_skill_library(path: Path, max_files: int = 4, max_chars: int = SKILL_LIBRARY_PROMPT_CHARS) -> str:
    if not path.exists() or not path.is_dir():
        return ""
    chunks = []
    for item in sorted(path.glob("*.md"))[:max_files]:
        text = item.read_text(encoding="utf-8").strip()
        if text:
            chunks.append(f"## {item.name}\n{text}")
    return "\n\n".join(chunks)[:max_chars]


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9가-힣_-]+", "-", text.strip())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug[:80] or "thread"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


def classify_research_problem(candidate: dict, analysis: dict | None = None) -> dict:
    text = " ".join(
        [
            candidate.get("title") or "",
            candidate.get("description") or "",
            candidate.get("readme_summary") or "",
            candidate.get("our_angle") or "",
            (analysis or {}).get("workflow_action") or "",
        ]
    ).lower()

    if any(term in text for term in ["citation", "reference", "bibliography", "인용", "참고문헌"]):
        signal = "citation_doubt"
        stage = "citation_verification"
        failure = "claim_reference_mismatch"
        problem = "AI가 붙인 citation이 claim을 실제로 받치는지 검증하기 어렵다."
    elif any(term in text for term in ["literature review", "related work", "survey", "리뷰", "관련 연구"]):
        signal = "literature_overload"
        stage = "literature_review"
        failure = "comparison_axis_missing"
        problem = "논문은 많지만 비교 기준이 없어 연구 흐름으로 정리하기 어렵다."
    elif any(term in text for term in ["draft", "writing", "초안", "논문 작성", "problem-gap", "argument"]):
        signal = "draft_without_argument"
        stage = "draft_structure"
        failure = "argument_structure_missing"
        problem = "초안 문장은 나왔지만 problem-gap-contribution 논리가 약하다."
    elif any(term in text for term in ["evidence", "experiment", "figure", "table", "근거", "실험", "그림", "표"]):
        signal = "evidence_missing"
        stage = "evidence_mapping"
        failure = "claim_evidence_link_missing"
        problem = "주장은 있지만 evidence가 표, 그림, 실험, 데이터와 연결되지 않는다."
    elif any(term in text for term in ["reviewer", "critique", "peer", "리뷰어", "반박"]):
        signal = "reviewer_anxiety"
        stage = "reviewer_critique"
        failure = "weakness_not_prechecked"
        problem = "리뷰어가 물을 약점과 limitation을 미리 찾기 어렵다."
    elif any(term in text for term in ["method", "reproduce", "reproduc", "방법", "재현"]):
        signal = "method_understanding_gap"
        stage = "method_understanding"
        failure = "method_steps_not_reproducible"
        problem = "방법론을 요약했지만 재현 가능한 단계로 설명하지 못한다."
    elif any(term in text for term in ["agent", "multi-agent", "subagent", "에이전트", "역할"]):
        signal = "agent_role_confusion"
        stage = "agent_workflow_design"
        failure = "roles_collapsed_into_one_agent"
        problem = "하나의 AI agent에게 읽기, 비교, 비판, 작성을 다 맡겨 결과가 흐려진다."
    else:
        signal = "summary_suspicion"
        stage = "summary_verification"
        failure = "false_fluency"
        problem = "AI 요약이 깔끔하지만 실제 이해를 만들었는지 검증하기 어렵다."

    return {
        "human_signal_source": "inferred",
        "human_signal_type": signal,
        "workflow_stage": stage,
        "failure_mode": failure,
        "research_problem": problem,
        "diagnostic_question": f"지금 문제는 {problem}",
        "verification_question": "AI 결과가 claim, evidence, limitation으로 분리되어 검증 가능한가?",
        "next_action_question": "AI agent에게 다음에 맡길 가장 작은 작업 단위는 무엇인가?",
    }


def is_friday_evening(date_text: str, post_slot: str) -> bool:
    try:
        return post_slot == "evening" and time.strptime(date_text, "%Y-%m-%d").tm_wday == 4
    except ValueError:
        return False


def route_format(candidate: dict, problem: dict, date_text: str, post_slot: str) -> str:
    if is_friday_evening(date_text, post_slot):
        return "weekly_review_advice"

    raw_format = str(candidate.get("format_type") or "").strip()
    if raw_format in FORMAT_TYPES:
        return raw_format
    if raw_format in LEGACY_FORMAT_MAP:
        return LEGACY_FORMAT_MAP[raw_format]

    axis = str(candidate.get("content_axis") or "").strip()
    if axis in AXIS_FORMAT_MAP:
        return AXIS_FORMAT_MAP[axis]

    signal = problem["human_signal_type"]
    if signal == "citation_doubt":
        return "research_checklist"
    if signal == "literature_overload":
        return "agent_role_split"
    if signal == "agent_role_confusion":
        return "agent_role_split"
    if signal in {"draft_without_argument", "method_understanding_gap"}:
        return "better_prompt_pattern"
    if signal in {"evidence_missing", "reviewer_anxiety"}:
        return "research_checklist"
    return "workflow_observation"


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

    lower_text = text.lower()
    practical_angle = candidate.get("our_angle") or "AI research workflow lesson"
    if any(term in lower_text for term in ["citation", "reference", "bibliography"]):
        workflow_action = "AI가 만든 reference를 그대로 믿지 말고 claim, metadata, 원문 위치를 따로 검증한다."
    elif any(term in lower_text for term in ["literature review", "related work", "survey"]):
        workflow_action = "논문 목록을 바로 문단으로 쓰지 말고 evidence matrix로 먼저 비교한다."
    elif any(term in lower_text for term in ["summarization", "summary", "paper"]):
        workflow_action = "요약 전에 contribution, method, evidence, limitation을 분리한다."
    elif any(term in lower_text for term in ["review", "critique", "peer"]):
        workflow_action = "초안 문체보다 claim과 evidence가 맞물리는지 reviewer 관점으로 확인한다."
    else:
        workflow_action = "큰 요청을 바로 맡기지 말고 읽기, 비교, 구조화, 검증 단계를 분리한다."

    return {
        "summary": text[:700],
        "source_facts": source_facts,
        "practical_angle": practical_angle,
        "workflow_action": workflow_action,
    }


def select_content_format(candidate: dict, analysis: dict, date_text: str, post_slot: str) -> dict:
    content_axis = safe_enum(candidate.get("content_axis"), CONTENT_AXES, "prompt_habit")
    problem = classify_research_problem(candidate, analysis)
    format_type = route_format(candidate, problem, date_text, post_slot)
    post_goal = safe_enum(candidate.get("post_goal"), POST_GOALS, "save")
    reusable_unit_type = {
        "workflow_observation": "applicable_prompt",
        "failed_agent_run": "corrected_instruction",
        "better_prompt_pattern": "applicable_prompt",
        "research_checklist": "verification_checklist",
        "agent_role_split": "agent_role_instruction",
        "tiny_source_case": "source_to_workflow_template",
        "weekly_review_advice": "weekly_research_prompt",
    }[format_type]
    return {
        "content_axis": content_axis,
        "format_type": format_type,
        "post_goal": post_goal,
        "reusable_unit_type": reusable_unit_type,
        **problem,
        "format_reason": candidate.get("format_reason")
        or "Use the format that best turns the source into a practical research workflow action.",
        "format_guide": FORMAT_GUIDE.get(format_type, FORMAT_GUIDE["workflow_observation"]),
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
                "human_signal_source": entry.get("human_signal_source"),
                "human_signal_type": entry.get("human_signal_type"),
                "research_problem": entry.get("research_problem"),
                "hook_pattern": entry.get("hook_pattern"),
                "structure_pattern": entry.get("structure_pattern"),
                "closer_pattern": entry.get("closer_pattern"),
                "reusable_unit_type": entry.get("reusable_unit_type"),
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
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()

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
    if len(parts) < MIN_PARTS or len(parts) > MAX_PARTS:
        raise SystemExit(f"Generated thread has {len(parts)} parts; expected {MIN_PARTS}-{MAX_PARTS} parts.")
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
    if "좋은 요청:" in joined:
        quoted_good_lines = QUOTE_LINE_RE.findall(joined.split("좋은 요청:", 1)[1])
        if any(re.match(r'^\s*["“]\s*\d+\.', line) for line in quoted_good_lines):
            raise SystemExit("Generated good-request lines should not include 1./2./3./4. numbering inside the quotes.")
    if "왜 좋은 요청일까요?" in joined:
        raise SystemExit("Generated thread should use practical framing, not '왜 좋은 요청일까요?'.")
    if any(part.lower().find("notebooklm.google") >= 0 for part in parts):
        raise SystemExit("Generated reference reply must link an actual example, not the NotebookLM homepage.")
    if URL_RE.search(joined) and "- 볼 부분:" not in joined and "인용 원문:" not in joined:
        raise SystemExit("Generated source links must explain what to inspect with '- 볼 부분:' or cite a quote source with '인용 원문:'.")


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
    recent_history: list[dict],
    persistent_learnings: str,
    skill_library: str,
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
        "Create exactly one Korean Threads chain for @arxiv.ai.\n"
        "Follow the channel playbook, PRD/ADR intent, and selected format router output exactly.\n\n"
        "Persistent learnings to apply before any other style choice:\n"
        f"{persistent_learnings or 'No persistent learnings yet.'}\n\n"
        "Reusable crystallized skills from previous good runs:\n"
        f"{skill_library or 'No crystallized skills yet.'}\n\n"
        "Hard constraints:\n"
        "- Return JSON only.\n"
        "- JSON keys: thread_text, topic, source_count, format, source_name, source_url, quote_used, quote_id.\n"
        "- Keep JSON compact. Do not include optional empty metadata fields.\n"
        "- thread_text must use --- between main and replies.\n"
        "- Do not include labels such as Main:, Reply 1:, Reply n:, or 제목: in thread_text.\n"
        "- Use short, sharp Korean Threads style: practical, calm, researcher/student-facing.\n"
        "- Use 1 to 4 parts total. Do not force a 4-part chain unless the format genuinely needs it.\n"
        "- Each part must be under 500 Korean characters.\n"
        "- Main must be easy to understand and must not contain external links.\n"
        "- Do not force '나쁜 요청:'/'좋은 요청:' unless selected format is better_prompt_pattern and it is the most natural shape.\n"
        "- Do not force bracketed reply headings. Use them only if they make the reply easier to scan.\n"
        "- Every chain must include one reusable unit: a practical prompt, verification checklist, agent-role instruction, or source-to-workflow template.\n"
        "- Prefer labels such as '바로 써볼 프롬프트:', '오늘 적용할 문장:', 'AI agent에게 이렇게 시켜보세요:', '논문 읽을 때 붙여 넣을 문장:', or '다음 요약 전에 써볼 질문:'. Rotate the label so it does not feel templated.\n"
        "- Derived questions must be practical: diagnostic question, verification question, or next-action question. Avoid philosophical questions.\n"
        "- If source links are used, put them in the final reply with full https:// URLs and '- 볼 부분: ...'.\n"
        "- Choose the first line as a sharp main-post hook. It should pull readers into the problem before the details.\n"
        "- The first post may be paired with a symbolic researcher/scientist image. Do not depend on the image for meaning.\n"
        "- Add human_signal as judgment, not fake diary. Automatic mode may infer source surprise, reader friction, common confusion, verification need, or agent-workflow bottleneck. Do not claim '직접 해봤다' unless supplied by the user.\n"
        "- If selected format is weekly_review_advice, first derive advice from recent history, then use a verified quote only if it genuinely matches. Quote text must be Korean only. Include source_url under '인용 원문:' in the final reply.\n"
        "- If using a verified quote, copy speaker_ko and quote_ko exactly, set quote_used=true and quote_id to the supplied id.\n"
        "- Do not use a quote merely because a famous speaker is available. If the quote is forced, set quote_used=false and write a general weekly review.\n"
        "- If no supplied quote_context is used, set quote_used=false and quote_id=\"\".\n"
        "- Avoid matching the recent hook patterns when possible.\n"
        "- Never use hype words: 무조건, 혁명, 논문 끝, 개발자 끝, 역대급, 미친 생산성, 이거 모르면 뒤처집니다.\n"
        "- Use Korean for names and general prose. Use English only for technical terms where Korean loses precision: AI agent, claim, evidence, limitation, citation, reviewer critique, workflow, prompt.\n"
        "- Do not use markdown code fences. Do not use bracketed mode labels such as '[초안 작성 모드]'.\n"
        "- Separate source facts from account interpretation.\n"
        "- Do not invent facts. Use only the candidates below as factual sources.\n"
        "- GitHub stars are popularity signals only, never quality proof.\n\n"
        "Format examples:\n"
        "- workflow_observation: observation -> research risk -> reusable prompt/check question.\n"
        "- failed_agent_run: failed agent request -> what broke -> corrected instruction.\n"
        "- better_prompt_pattern: vague request -> better research prompt(s), without forcing four examples.\n"
        "- research_checklist: verification checklist -> execution prompt.\n"
        "- agent_role_split: one broad task -> reader/synthesizer/critic/editor instructions.\n"
        "- tiny_source_case: source fact -> account interpretation -> reusable workflow.\n"
        "- weekly_review_advice: weekly pattern -> advice -> optional verified Korean quote -> next week's practical research prompt.\n\n"
        "Selected routing:\n"
        f"{json.dumps(routing, ensure_ascii=False, indent=2)}\n\n"
        "Candidate analysis:\n"
        f"{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        "Metrics feedback:\n"
        f"{json.dumps(feedback, ensure_ascii=False, indent=2)}\n\n"
        "Recent hook patterns to avoid repeating:\n"
        f"{json.dumps(recent_hooks, ensure_ascii=False, indent=2)}\n\n"
        "Recent content-history fingerprints to avoid repeating:\n"
        f"{json.dumps(recent_history, ensure_ascii=False, indent=2)}\n\n"
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
        suggestions.append("Open with a sharper paper-workflow mistake or research-note contrast.")
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
        suggestions.append("Replace hype with concrete research workflow impact.")
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
    if routing.get("format_type") == "tiny_source_case" and "적용" not in joined and "AI agent" not in joined:
        score -= 10
        reasons.append("Source case has no application note.")
        suggestions.append("Add a short '적용:' line explaining what to copy into a workflow.")
    if routing.get("format_type") == "weekly_review_advice" and "인용 원문:" in joined and not URL_RE.search(joined):
        score -= 20
        reasons.append("Weekly quote has no source URL.")
    if routing.get("format_type") == "weekly_review_advice" and "다음" not in joined and "프롬프트" not in joined:
        score -= 10
        reasons.append("Weekly review lacks a next practical question or prompt.")
    if len(parts) >= 2 and len(parts[0]) > 360:
        score -= 8
        reasons.append("Main is too dense for an easy hook.")
        suggestions.append("Move details to Reply 1 or Reply 2.")
    if len(recent_patterns) >= 3 and len(set(recent_patterns[-3:])) == 1 and hook_pattern == recent_patterns[-1]:
        score -= 18
        reasons.append(f"Factory-feel risk: hook pattern '{hook_pattern}' repeats the last 3 posts.")
        suggestions.append("Use a personal proof line, quote/idea hook, failed-request hook, or direct claim instead.")
    if "오늘" not in joined and "내가" not in joined and "요즘" not in joined and "리처드 파인만" not in joined and "안드레이 카파시" not in joined and "폴 그레이엄" not in joined and routing.get("human_signal_source") != "inferred":
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


def build_evaluator_prompt(
    thread_text: str,
    routing: dict,
    analysis: dict,
    recent_history: list[dict],
    persistent_learnings: str,
    skill_library: str,
) -> str:
    return (
        "You are the evaluator agent for @arxiv.ai. Review one Korean Threads chain.\n"
        "Return JSON only. Do not rewrite the full post.\n\n"
        "Evaluation goals:\n"
        "- The post should solve a real paper-work problem, not make generic AI commentary.\n"
        "- It must include a reusable prompt, checklist, agent instruction, or workflow template.\n"
        "- It must not invent personal experience in automatic mode.\n"
        "- It should avoid recent hook, structure, and closer repetition.\n"
        "- It must separate source facts from our interpretation.\n\n"
        "Return keys:\n"
        "{\n"
        '  "score": 0-100,\n'
        '  "decision": "publish" | "revise" | "discard",\n'
        '  "strengths": ["..."],\n'
        '  "risks": ["..."],\n'
        '  "revision_suggestions": ["..."],\n'
        '  "learning_candidate": "one compact lesson to add to docs/learnings.md if this result proves useful",\n'
        '  "skill_candidate": {"name": "optional_skill_name", "summary": "reusable pattern if any"}\n'
        "}\n\n"
        "Persistent learnings:\n"
        f"{persistent_learnings or 'No persistent learnings yet.'}\n\n"
        "Existing skill library:\n"
        f"{skill_library or 'No skills yet.'}\n\n"
        "Routing:\n"
        f"{json.dumps(routing, ensure_ascii=False, indent=2)}\n\n"
        "Candidate analysis:\n"
        f"{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        "Recent history:\n"
        f"{json.dumps(recent_history, ensure_ascii=False, indent=2)}\n\n"
        "Thread text:\n"
        f"{thread_text}"
    )


def fallback_evaluation(reason: str) -> dict:
    return {
        "score": 0,
        "decision": "revise",
        "strengths": [],
        "risks": [reason],
        "revision_suggestions": ["Evaluator failed. Review manually before using this evaluation as learning data."],
        "learning_candidate": "",
        "skill_candidate": {"name": "", "summary": ""},
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


def call_groq(api_key: str, model: str, prompt: str, max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS) -> dict:
    for attempt in range(1, 4):
        request_body = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return one valid JSON object only. Do not include markdown, prose, or code fences.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_completion_tokens": max_output_tokens,
        }

        response = requests.post(
            CHAT_COMPLETIONS_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=request_body,
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
    parser.add_argument("--weekly-memory-path", default="daily-editor/memory/weekly-editorial-memory.md")
    parser.add_argument("--learnings-path", default="docs/learnings.md")
    parser.add_argument("--skills-library-dir", default="skills_library")
    parser.add_argument("--review-dir", default="daily-editor/review")
    parser.add_argument("--run-log-dir", default="daily-editor/runs")
    parser.add_argument("--evaluation-dir", default="daily-editor/evaluations")
    parser.add_argument("--skip-evaluator", action="store_true")
    parser.add_argument("--post-slot", choices=["morning", "evening"], default=os.environ.get("POST_SLOT", "morning"))
    parser.add_argument("--posts-per-day", type=int, choices=[1, 2], default=int(os.environ.get("POSTS_PER_DAY", "1")))
    parser.add_argument("--experiment-group", default=os.environ.get("EXPERIMENT_GROUP", "manual"))
    parser.add_argument("--generation-candidates", type=int, default=int(os.environ.get("GENERATION_CANDIDATES", str(DEFAULT_GENERATION_CANDIDATES))))
    parser.add_argument("--model", default=os.environ.get("GROQ_MODEL", DEFAULT_MODEL))
    parser.add_argument("--max-output-tokens", type=int, default=int(os.environ.get("GROQ_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS))))
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY is required.")

    candidates = read_json(Path(args.candidates_path))
    if not isinstance(candidates, list) or not candidates:
        raise SystemExit(f"No candidates found in {args.candidates_path}")

    playbook = read_text(Path(args.playbook_path), max_chars=PLAYBOOK_PROMPT_CHARS)
    feedback = metrics_feedback(Path(args.metrics_path), limit=15)
    recent_hooks = recent_hook_patterns(Path(args.metrics_path))
    recent_history = load_recent_history(Path(args.history_path), limit=5)
    quote_bank = load_quote_bank(Path(args.quote_bank_path))
    weekly_memory = read_optional_text(Path(args.weekly_memory_path), max_chars=WEEKLY_MEMORY_PROMPT_CHARS)
    persistent_learnings = read_optional_text(Path(args.learnings_path), max_chars=LEARNINGS_PROMPT_CHARS)
    skill_library = read_skill_library(Path(args.skills_library_dir))
    review_dir = Path(args.review_dir)
    selected_candidates = choose_candidates(candidates, args.post_slot, max(1, args.generation_candidates))
    candidate_by_url = {item.get("url"): item for item in candidates if item.get("url")}
    generated_options = []

    for index, selected_candidate in enumerate(selected_candidates, start=1):
        analysis = analyze_candidate(selected_candidate)
        routing = select_content_format(selected_candidate, analysis, args.date, args.post_slot)
        quote_context = select_quote_context(selected_candidate, quote_bank)
        prompt = build_prompt(
            playbook,
            selected_candidate,
            analysis,
            routing,
            feedback,
            quote_context,
            recent_hooks,
            recent_history,
            persistent_learnings,
            skill_library,
            weekly_memory,
        )
        payload = call_groq(api_key, args.model, prompt, args.max_output_tokens)
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
                    "writer_prompt": prompt,
                    "model_output_raw": text,
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
                "writer_prompt": prompt,
                "model_output_raw": text,
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

    evaluator_prompt = ""
    evaluator_result = {}
    if args.skip_evaluator:
        evaluator_result = fallback_evaluation("Evaluator skipped by --skip-evaluator.")
    else:
        evaluator_prompt = build_evaluator_prompt(
            thread_text=thread_text,
            routing=routing,
            analysis=analysis,
            recent_history=recent_history,
            persistent_learnings=persistent_learnings,
            skill_library=skill_library,
        )
        try:
            evaluator_payload = call_groq(api_key, args.model, evaluator_prompt, min(args.max_output_tokens, 800))
            evaluator_text = extract_text(evaluator_payload)
            evaluator_result = extract_json(evaluator_text)
            evaluator_result["model_output_raw"] = evaluator_text
        except SystemExit as exc:
            evaluator_result = fallback_evaluation(f"Evaluator failed: {exc}")
        except Exception as exc:
            evaluator_result = fallback_evaluation(f"Evaluator failed: {exc}")

    metadata = {
        "date": args.date,
        "model": args.model,
        "post_slot": args.post_slot,
        "posts_per_day": args.posts_per_day,
        "experiment_group": args.experiment_group,
        "generation_candidates": len(selected_candidates),
        "selected_option": best["option"],
        "topic": data.get("topic", "research workflow"),
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
        "recent_history": recent_history,
        "persistent_learnings_path": args.learnings_path,
        "skills_library_dir": args.skills_library_dir,
        "evaluator": {
            "score": evaluator_result.get("score", 0),
            "decision": evaluator_result.get("decision", "revise"),
            "strengths": evaluator_result.get("strengths", []),
            "risks": evaluator_result.get("risks", []),
            "revision_suggestions": evaluator_result.get("revision_suggestions", []),
            "learning_candidate": evaluator_result.get("learning_candidate", ""),
            "skill_candidate": evaluator_result.get("skill_candidate", {}),
        },
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
        "workflow_stage": data.get("workflow_stage") or routing.get("workflow_stage", ""),
        "failure_mode": data.get("failure_mode") or routing.get("failure_mode", ""),
        "solution_pattern": data.get("solution_pattern", ""),
        "bad_request": data.get("bad_request", ""),
        "human_signal_source": data.get("human_signal_source") or routing.get("human_signal_source", ""),
        "human_signal_type": data.get("human_signal_type") or routing.get("human_signal_type", ""),
        "research_problem": data.get("research_problem") or routing.get("research_problem", ""),
        "hook_pattern": data.get("hook_pattern") or classify_hook_pattern(thread_text),
        "structure_pattern": data.get("structure_pattern", ""),
        "closer_pattern": data.get("closer_pattern", ""),
        "reusable_unit_type": data.get("reusable_unit_type") or routing.get("reusable_unit_type", ""),
        "quote_used": quote_used,
        "quote_id": quote_id,
        "quote_speaker": quote_suggestion.get("speaker", "") if quote_suggestion else "",
        "quote_source_url": quote_suggestion.get("source_url", "") if quote_suggestion else "",
    }

    run_slug = safe_slug(f"{args.date}-{args.post_slot}-{metadata['format']}-{metadata['topic']}")
    run_log = {
        "run_id": run_slug,
        "date": args.date,
        "model": args.model,
        "selected_candidate": selected_candidate,
        "context_used": {
            "playbook_path": args.playbook_path,
            "history_path": args.history_path,
            "metrics_path": args.metrics_path,
            "weekly_memory_path": args.weekly_memory_path,
            "learnings_path": args.learnings_path,
            "skills_library_dir": args.skills_library_dir,
            "recent_history_count": len(recent_history),
            "recent_hook_count": len(recent_hooks),
        },
        "routing": routing,
        "analysis": analysis,
        "writer_prompt": best.get("writer_prompt", ""),
        "model_output_raw": best.get("model_output_raw", ""),
        "final_thread_text": thread_text,
        "metadata": metadata,
    }
    run_log_path = Path(args.run_log_dir) / f"{run_slug}.json"
    evaluation_path = Path(args.evaluation_dir) / f"{run_slug}.eval.json"
    write_json(run_log_path, run_log)
    write_json(
        evaluation_path,
        {
            "run_id": run_slug,
            "evaluator_prompt": evaluator_prompt,
            "evaluation": evaluator_result,
            "thread_text": thread_text,
            "routing": routing,
        },
    )
    metadata["run_log_path"] = str(run_log_path)
    metadata["evaluation_path"] = str(evaluation_path)
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
