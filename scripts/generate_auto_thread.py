import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

try:
    from scripts.thread_spec import (
        BRACKET_HEADING_RE,
        HYPE_WORDS,
        MAX_CHARS,
        PART_ROLES,
        PRACTICAL_MARKERS,
        PROMPT_CONTRACT_VERSION,
        QUOTE_LINE_RE,
        SECTION_LABEL_RE,
        SEPARATOR_RE,
        URL_RE,
        build_thread_spec,
        raise_for_report,
        validate_thread_spec,
        validate_thread_text,
        write_spec,
    )
except ModuleNotFoundError:
    from thread_spec import (
        BRACKET_HEADING_RE,
        HYPE_WORDS,
        MAX_CHARS,
        PART_ROLES,
        PRACTICAL_MARKERS,
        PROMPT_CONTRACT_VERSION,
        QUOTE_LINE_RE,
        SECTION_LABEL_RE,
        SEPARATOR_RE,
        URL_RE,
        build_thread_spec,
        raise_for_report,
        validate_thread_spec,
        validate_thread_text,
        write_spec,
    )


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_PROVIDER = "openrouter"
DEFAULT_MODEL = "google/gemma-4-26b-a4b-it:free"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
DEFAULT_OPENAI_MODEL = "gpt-5.6-terra"
DEFAULT_FALLBACK_PROVIDER = ""
MIN_PARTS = len(PART_ROLES)
MAX_PARTS = len(PART_ROLES)
AUTO_PUBLISH_QUALITY_SCORE = int(os.environ.get("AUTO_PUBLISH_QUALITY_SCORE", "85"))
DRAFT_QUALITY_SCORE = int(os.environ.get("DRAFT_QUALITY_SCORE", "70"))
EVALUATOR_PUBLISH_SCORE = int(os.environ.get("EVALUATOR_PUBLISH_SCORE", "85"))
DEFAULT_GENERATION_CANDIDATES = 1
DEFAULT_MAX_OUTPUT_TOKENS = 900
DEFAULT_ATTEMPT_COOLDOWN_DAYS = 7
PLAYBOOK_PROMPT_CHARS = 1200
LEARNINGS_PROMPT_CHARS = 800
SKILL_LIBRARY_PROMPT_CHARS = 600
WEEKLY_MEMORY_PROMPT_CHARS = 500
FORBIDDEN_FALLBACK_PHRASES = [
    "GitHub stars는 인기 신호일 뿐이고",
    "연구 품질 증거로 쓰면 안 됩니다",
]
THREAD_CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {
            "type": "string",
            "description": "Publishable Korean main post: problem hook, 나쁜 요청 with 1 quote, 좋은 요청 with 3-4 quotes, and a short judgment closer.",
        },
        "diagnosis": {
            "type": "string",
            "description": "Publishable Korean text with three concrete diagnostic checks.",
        },
        "action": {
            "type": "string",
            "description": "Publishable Korean reusable prompt, checklist, protocol, matrix, or role instruction.",
        },
        "source": {
            "type": "string",
            "description": "Publishable Korean source interpretation with the supplied URL and fact/opinion boundary.",
        },
        "quote_used": {"type": "boolean"},
        "quote_id": {"type": "string"},
    },
    "required": ["hook", "diagnosis", "action", "source", "quote_used", "quote_id"],
    "additionalProperties": False,
}
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
CANONICAL_STYLE_EXAMPLE = """AI에게 method paper 초안을 검토시킬 때 “리뷰어처럼 봐줘”라고 하면 답이 너무 흐립니다.

내가 어느 claim이 어떤 evidence 때문에 기각될 수 있는지 설명 못하면, 그건 review가 아니라 점수 예측입니다.

나쁜 요청:
“리뷰어처럼 평가해줘.”

좋은 요청:
“핵심 claim 3개와 필요한 evidence를 분리해줘.”
“ICML 기준으로 soundness를 흔들 반례 질문을 써줘.”
“AC가 볼 때 치명적인 약점을 우선순위로 표시해줘.”
“표현 지적과 reject 근거가 될 구조적 약점을 나눠줘.”

AI reviewer는 점수 예측기가 아니라
제출 전 위험 위치를 찾는 도구입니다."""

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
    "workflow_observation": "Use the fixed 4-part template; emphasize a concrete judgment in Part 1.",
    "failed_agent_run": "Use the fixed 4-part template; emphasize a failure scene in Part 1 and a corrected instruction in Part 3.",
    "better_prompt_pattern": "Use the fixed 4-part template; include a bad request in Part 1 and a better request in Part 3.",
    "research_checklist": "Use the fixed 4-part template; emphasize 3 concrete checks in Part 2.",
    "agent_role_split": "Use the fixed 4-part template; emphasize reader/synthesizer/critic/editor roles in Part 3.",
    "tiny_source_case": "Use the fixed 4-part template; emphasize source fact vs account interpretation in Part 4.",
    "weekly_review_advice": "Use the fixed 4-part template; derive Part 2-3 advice from recent history.",
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
ARTIFACT_BY_FAILURE_MODE = {
    "false_fluency": "summary_verification_grid",
    "claim_reference_mismatch": "citation_support_table",
    "claim_evidence_link_missing": "claim_evidence_map",
    "method_steps_not_reproducible": "reproducibility_protocol",
    "comparison_axis_missing": "literature_comparison_matrix",
    "argument_structure_missing": "problem_gap_contribution_outline",
    "revision_without_rule": "revision_rule_diff",
    "weakness_not_prechecked": "reviewer_risk_checklist",
    "roles_collapsed_into_one_agent": "agent_role_instruction",
}
ARTIFACT_OUTPUT_GUIDE = {
    "summary_verification_grid": "claim, method, evidence, limitation을 분리한 검증표",
    "citation_support_table": "claim마다 citation 원문 위치와 지지 범위를 표시한 표",
    "claim_evidence_map": "claim을 표, 그림, 실험, 데이터에 연결한 근거 지도",
    "reproducibility_protocol": "input, procedure, parameter, output, check로 나눈 재현 프로토콜",
    "literature_comparison_matrix": "논문들을 같은 비교 축으로 정렬한 evidence matrix",
    "problem_gap_contribution_outline": "problem, gap, contribution, evidence 순서의 초안 구조",
    "revision_rule_diff": "human revision을 다음 초안 규칙으로 바꾼 diff",
    "reviewer_risk_checklist": "reviewer가 물을 limitation과 반박 가능성 체크리스트",
    "agent_role_instruction": "reader, synthesizer, critic, editor 역할별 output 지시문",
}
ARTIFACT_READER_TEST_GUIDE = {
    "summary_verification_grid": "내가 claim, method, evidence, limitation을 설명 못하면",
    "citation_support_table": "내가 citation이 어느 claim을 받치는지 설명 못하면",
    "claim_evidence_map": "내가 claim을 어떤 실험, 표, 그림이 받치는지 설명 못하면",
    "reproducibility_protocol": "내가 method를 재현 순서로 설명 못하면",
    "literature_comparison_matrix": "내가 논문 간 차이를 같은 축으로 설명 못하면",
    "problem_gap_contribution_outline": "내가 problem-gap-contribution을 설명 못하면",
    "revision_rule_diff": "내가 수정 이유를 다음 초안 규칙으로 설명 못하면",
    "reviewer_risk_checklist": "내가 reviewer가 물을 약점을 설명 못하면",
    "agent_role_instruction": "내가 reader, critic, editor 역할을 나눠 설명 못하면",
}
ARTIFACT_FAILURE_JUDGMENT_GUIDE = {
    "summary_verification_grid": "그건 요약이 아니라 대리 독서입니다.",
    "citation_support_table": "그건 검증이 아니라 참고문헌 장식입니다.",
    "claim_evidence_map": "그건 이해가 아니라 요약문 신뢰입니다.",
    "reproducibility_protocol": "그건 방법론 이해가 아니라 방법론 복사입니다.",
    "literature_comparison_matrix": "그건 literature review가 아니라 논문 목록 정리입니다.",
    "problem_gap_contribution_outline": "그건 초안 작성이 아니라 문장 생산입니다.",
    "revision_rule_diff": "그건 개선이 아니라 문장 수정입니다.",
    "reviewer_risk_checklist": "그건 비판이 아니라 좋은 말 요약입니다.",
    "agent_role_instruction": "그건 agent workflow가 아니라 한 에이전트에게 다 맡긴 것입니다.",
}

HOOK_PATTERNS = {
    "bad_usage": re.compile(r"만약|라고 사용하고 있다면|시키고 있다면"),
    "personal_diary": re.compile(r"오늘|내가|요즘 내가|23살"),
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
    if not path.exists():
        return ""
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()[:max_chars]
    if not path.is_dir():
        return ""
    chunks = []
    for item in sorted(path.glob("*.md"))[:max_files]:
        text = item.read_text(encoding="utf-8").strip()
        if text:
            chunks.append(f"## {item.name}\n{text}")
    return "\n\n".join(chunks)[:max_chars]


def clip_text(value: object, max_chars: int) -> str:
    text = str(value or "").strip()
    return text[:max_chars]


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

    artifact_type = ARTIFACT_BY_FAILURE_MODE.get(failure, "research_workflow_artifact")
    return {
        "human_signal_source": "inferred",
        "human_signal_type": signal,
        "workflow_stage": stage,
        "failure_mode": failure,
        "research_problem": problem,
        "artifact_type": artifact_type,
        "artifact_output": ARTIFACT_OUTPUT_GUIDE.get(artifact_type, "검증 가능한 연구 작업 산출물"),
        "reader_test": ARTIFACT_READER_TEST_GUIDE.get(artifact_type, "내가 핵심 작업 단위를 설명 못하면"),
        "failure_judgment": ARTIFACT_FAILURE_JUDGMENT_GUIDE.get(artifact_type, "그건 이해가 아니라 자동화 결과 신뢰입니다."),
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
        artifact_type = entry.get("artifact_type") or ARTIFACT_BY_FAILURE_MODE.get(entry.get("failure_mode") or "")
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
                "artifact_type": artifact_type,
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


def load_curation_log(path: Path, limit: int = 50) -> list[dict]:
    if not path.exists():
        return []

    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records[-limit:]


def curation_bonus(item: dict, curation_records: list[dict]) -> int:
    if not curation_records:
        return 0

    text = " ".join(
        [
            str(item.get("title") or item.get("name") or ""),
            str(item.get("description") or ""),
            str(item.get("readme_summary") or ""),
            str(item.get("our_angle") or ""),
            str(item.get("content_axis") or ""),
            str(item.get("format_type") or ""),
        ]
    ).lower()
    url = str(item.get("url") or "").strip().lower()
    axis = str(item.get("content_axis") or "")
    fmt = str(item.get("format_type") or "")
    bonus = 0

    for record in curation_records[-12:]:
        if str(record.get("codex_gate_decision") or "keep").lower() not in {"keep", "publish", "draft"}:
            continue
        if url and url == str(record.get("codex_selected_url") or "").strip().lower():
            bonus += 6
        if axis and axis == record.get("selected_content_axis"):
            bonus += 3
        if fmt and fmt == record.get("selected_format_type"):
            bonus += 3
        for signal in record.get("preferred_future_signals") or []:
            signal_text = str(signal).lower().strip()
            if signal_text and signal_text in text:
                bonus += 5
        for preference in record.get("human_preference") or []:
            preference_text = str(preference).lower().strip()
            if preference_text and preference_text in text:
                bonus += 2

    return min(bonus, 18)


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
    text = re.sub(r"\\\s*\n\s*", r"\\n", text)
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


def normalize_thread_candidate(payload: dict, candidate: dict, routing: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Thread candidate response must be a JSON object.")

    missing = [key for key in THREAD_CANDIDATE_SCHEMA["required"] if key not in payload]
    extra = [key for key in payload if key not in THREAD_CANDIDATE_SCHEMA["properties"]]
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing={','.join(missing)}")
        if extra:
            details.append(f"unexpected={','.join(extra)}")
        raise ValueError(f"ThreadCandidate v1 shape mismatch ({'; '.join(details)}).")

    parts = [normalize_part(str(payload[role])) for role in PART_ROLES]
    if any(not part for part in parts):
        raise ValueError("ThreadCandidate v1 parts must be non-empty strings.")

    normalized = {
        "thread_text": "\n---\n".join(parts),
        "topic": routing.get("human_signal_type") or "research workflow",
        "source_count": 1 if candidate.get("url") else 0,
        "format": routing.get("format_type") or "research_checklist",
        "source_name": candidate.get("title") or candidate.get("name") or "",
        "source_url": candidate.get("url") or "",
        "quote_used": payload.get("quote_used") is True,
        "quote_id": str(payload.get("quote_id") or "").strip(),
    }
    return normalized


def build_fallback_thread(candidate: dict, routing: dict, analysis: dict) -> str:
    source_title = clip_text(candidate.get("title") or candidate.get("name") or "오늘의 source", 80)
    source_url = str(candidate.get("url") or "").strip()
    problem = routing.get("research_problem") or "AI가 만든 연구 결과를 그대로 믿기 어렵다."
    reader_test = routing.get("reader_test") or "내가 claim과 evidence의 연결을 설명 못하면"
    failure_judgment = routing.get("failure_judgment") or "그건 이해가 아니라 요약문 신뢰입니다."
    workflow_action = analysis.get("workflow_action") or "읽기, 비교, 검증, 작성을 분리한다."
    if not source_url:
        source_url = "https://github.com/gyutaetae/threads-agentic-editor-workflow"

    parts = [
        (
            f"논문 작업을 AI에게 한 번에 맡기면 {problem}\n\n"
            f"{reader_test}, {failure_judgment}\n\n"
            "나쁜 요청:\n"
            "“이 논문 정리해줘.”\n\n"
            "좋은 요청:\n"
            "“핵심 claim과 필요한 evidence를 분리해줘.”\n"
            "“각 claim을 받치는 원문 위치를 표시해줘.”\n"
            "“limitation과 추가 검증 항목을 나눠줘.”\n"
            "“결과를 표로 만들고 판단 이유를 남겨줘.”\n\n"
            "좋은 research agent는 답을 대신 만드는 도구가 아니라\n"
            "검증할 위치와 판단 근거를 남기는 도구입니다."
        ),
        (
            "[먼저 확인할 것]\n"
            "초안보다 먼저 검증할 중간 산출물을 정해야 합니다.\n\n"
            "1. claim이 분리되는가\n"
            "2. evidence 위치가 남는가\n"
            "3. limitation과 citation 범위가 따로 보이는가"
        ),
        (
            "[저장해둘 프롬프트]\n\n"
            "\"이 논문 작업을 reader, synthesizer, critic, citation checker로 나눠줘. "
            "각 역할은 output, evidence, failure mode를 따로 적어줘.\"\n\n"
            f"목표는 {workflow_action}"
        ),
        (
            "[참고 논문]\n"
            f"{source_url}\n"
            f"- 볼 부분: {source_title}에서 source fact를 연구 workflow로 바꾸는 단서\n\n"
            "- 적용: 다음 요청 전에는 source fact와\n"
            "내가 적용하려는 workflow 해석을 한 줄씩 나눠보세요."
        ),
    ]
    return "\n---\n".join(parts)


def validate_thread(thread_text: str) -> None:
    report = validate_thread_text(thread_text)
    for forbidden in FORBIDDEN_FALLBACK_PHRASES:
        if forbidden in thread_text:
            report.errors.append(f"Generated thread contains retired fallback phrase: {forbidden}")
    raise_for_report(report)


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


def rank_candidate(item: dict, post_slot: str = "morning", curation_records: list[dict] | None = None) -> tuple[int, int, int]:
    if post_slot == "evening":
        preferred = {"workflow_mode", "repo_teardown", "official_update", "checklist"}
    else:
        preferred = {"prompt_habit", "failure_prevention", "checklist"}

    score = int(item.get("score", {}).get("total") or 0)
    axis_bonus = 8 if item.get("content_axis") in preferred else 0
    codex_bonus = curation_bonus(item, curation_records or [])
    return score + axis_bonus + codex_bonus, score, codex_bonus


def choose_candidates(
    candidates: list[dict],
    post_slot: str = "morning",
    count: int = DEFAULT_GENERATION_CANDIDATES,
    curation_records: list[dict] | None = None,
    excluded_urls: set[str] | None = None,
) -> list[dict]:
    ranked = sorted(candidates, key=lambda item: rank_candidate(item, post_slot, curation_records), reverse=True)
    excluded_urls = {str(url).strip().lower() for url in (excluded_urls or set()) if str(url).strip()}
    fresh_ranked = [
        item
        for item in ranked
        if str(item.get("url") or "").strip().lower() not in excluded_urls
    ]
    if fresh_ranked:
        ranked = fresh_ranked
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


def load_recent_attempted_urls(path: Path, target_date: str, cooldown_days: int = DEFAULT_ATTEMPT_COOLDOWN_DAYS) -> set[str]:
    if not path.exists():
        return set()
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        return set()
    cutoff = target - timedelta(days=max(1, cooldown_days) - 1)
    urls: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            attempted_on = date.fromisoformat(str(record.get("date") or ""))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        url = str(record.get("source_url") or "").strip().lower()
        if url and cutoff <= attempted_on <= target:
            urls.add(url)
    return urls


def append_generation_attempts(path: Path, target_date: str, options: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for option in options:
        candidate = option.get("candidate") or {}
        source_url = str(candidate.get("url") or option.get("candidate_url") or "").strip()
        if not source_url:
            continue
        records.append(
            {
                "date": target_date,
                "source_url": source_url,
                "source_name": candidate.get("title") or candidate.get("name") or option.get("candidate_title") or "",
                "provider": option.get("provider") or "",
                "model": option.get("model") or "",
                "quality_decision": option.get("quality_decision") or "error",
                "quality_score": int(option.get("quality_score") or 0),
                "quality_reasons": list(option.get("quality_reasons") or []),
            }
        )
    if not records:
        return
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


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
        "title": clip_text(candidate.get("title"), 160),
        "url": candidate.get("url"),
        "source_type": candidate.get("source_type"),
        "category": candidate.get("category"),
        "description": clip_text(candidate.get("description"), 260),
        "readme_summary": clip_text(candidate.get("readme_summary"), 500),
        "our_angle": clip_text(candidate.get("our_angle"), 180),
        "score": candidate.get("score", {}).get("total"),
        "score_breakdown": candidate.get("score", {}),
        "risk": clip_text(candidate.get("risk"), 180),
        "facts_vs_interpretation": clip_text(candidate.get("fact_boundary"), 220),
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
        "- Return one ThreadCandidate v1 JSON object only.\n"
        "- JSON keys are exactly: hook, diagnosis, action, source, quote_used, quote_id.\n"
        "- Each of hook, diagnosis, action, and source is one publishable part. Do not include --- separators in a field.\n"
        "- Do not include labels such as Main:, Reply 1:, Reply n:, or 제목:.\n"
        "- Use short, sharp Korean Threads style: practical, calm, researcher/student-facing.\n"
        "- Use exactly 4 parts total. This is a hard rule.\n"
        "- Part 1 must use this compact main-post template: recognizable paper-work scene -> sharp self-diagnosis/verdict -> '나쁜 요청:' -> exactly 1 standalone quoted vague request -> '좋은 요청:' -> 3-4 standalone copy-ready requests -> memorable working principle. Do not include a bracket label here.\n"
        "- Part 2: start with a role-specific Korean bracket label such as '[먼저 확인할 것]' and give 3 concrete diagnosis criteria/checks by default.\n"
        "- Part 3: start with '[저장해둘 프롬프트]' when it contains a reusable prompt; otherwise use a role-specific bracket label for the reusable checklist or agent instruction.\n"
        "- Part 4: start with '[참고 논문]' or another source-specific bracket label, include the source URL, use '- 볼 부분:' for source fact and '- 적용:' for the account's workflow interpretation. Never use '[나의 견해]'.\n"
        "- Each part must be under 500 Korean characters.\n"
        "- Main must be easy to understand and must not contain external links.\n"
        "- Use Korean role labels. Avoid repeated generic '[핵심 한 줄]' labels and avoid English structural labels.\n"
        "- The account's north star: AI가 논문을 대신 읽어주는 게 아니라, 독자가 설명할 수 있는 상태로 바꿔준다.\n"
        "- Start from the reader test when possible: selected routing includes reader_test and failure_judgment.\n"
        "- Strong pattern: '내가 [artifact target]을 설명 못하면, 그건 [good outcome]이 아니라 [failure judgment]입니다.'\n"
        "- The opening must name a paper-work scene many readers recognize and its concrete consequence. Avoid generic AI-problem openings.\n"
        "- The verdict should stop the reader through accurate self-diagnosis, never hype or humiliation.\n"
        "- Use the labels exactly as '나쁜 요청:' and '좋은 요청:'. Put each example request on its own quoted line with no numbering inside the quote.\n"
        "- Good-request lines must be immediately copyable and visibly more specific than the bad request.\n"
        "- Do not stop at summarizing what a paper says. Show what the reader can now explain, verify, reproduce, compare, or revise.\n"
        "- Every chain must own exactly one research-work artifact from selected routing: artifact_type and artifact_output. This is the reader's reusable intermediate output.\n"
        "- Compare against recent content-history fingerprints before writing. The new post must differ in at least two of: failure_mode, workflow_stage, artifact_type, hook_pattern, reusable_unit_type.\n"
        "- If a recent post shares the same broad opening frame, make Part 1 start from the artifact-specific failure instead of a generic '논문 작업을 AI에게 한 번에 맡기면' frame.\n"
        "- If a recent post shares the same failure_mode, use a clearly different artifact_type or discard that angle.\n"
        "- Part 2 and Part 3 must name or strongly imply the artifact through checks, prompt wording, or agent instruction.\n"
        "- The full bad/good request card is required in Part 1 for every format. Vary the concrete failure, requests, and closer rather than removing the card.\n"
        "- Every chain must include one reusable unit: a practical prompt, verification checklist, agent-role instruction, or source-to-workflow template.\n"
        "- Prefer concise labels such as '[저장해둘 프롬프트]', '[먼저 확인할 것]', and '[참고 논문]'. Rotate labels so they fit the reply's role.\n"
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
        "- Separate source facts from account interpretation without a personal-opinion heading.\n"
        "- In Part 4, explicitly distinguish what the source provides under '- 볼 부분:' from how @arxiv.ai applies it under '- 적용:'.\n"
        "- Do not invent facts. Use only the candidates below as factual sources.\n"
        "- Do not write the retired phrase 'GitHub stars는 인기 신호일 뿐이고, 연구 품질 증거로 쓰면 안 됩니다.'\n\n"
        "All format routers keep the same Part 1 card. They only change the emphasis of Parts 2-4: diagnosis, reusable action, and source interpretation.\n\n"
        "Canonical surface example:\n"
        f"{CANONICAL_STYLE_EXAMPLE}\n\n"
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


def quality_gate(
    thread_text: str,
    routing: dict,
    recent_hooks: list[dict] | None = None,
    recent_history: list[dict] | None = None,
) -> dict:
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
    recent_history = recent_history or []

    contract_report = validate_thread_text(thread_text)
    if contract_report.errors:
        return {
            "quality_score": 0,
            "decision": "discard",
            "reasons": contract_report.errors,
            "revision_suggestions": ["Repair the canonical ThreadSpec contract before editorial scoring."],
        }
    if contract_report.warnings:
        score -= min(20, len(contract_report.warnings) * 4)
        reasons.extend(f"Contract warning: {warning}" for warning in contract_report.warnings)
        suggestions.append("Resolve contract warnings before strict prepublish validation.")
    if any(phrase in joined for phrase in FORBIDDEN_FALLBACK_PHRASES):
        score -= 40
        reasons.append("Thread uses a retired fallback phrase.")
        suggestions.append("Replace generic GitHub-stars caveats with a source-specific next action.")
    if len(main_first_line) < 8:
        score -= 12
        reasons.append("First line is weak or too short.")
        suggestions.append("Open with a sharper paper-workflow mistake or research-note contrast.")
    if "AI가 중요" in joined or "AI 시대" in main and "기준" not in joined:
        score -= 12
        reasons.append("Thread risks generic AI advice.")
        suggestions.append("Ground the point in one concrete work unit or failure mode.")
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
        score -= 8
        reasons.append(f"Factory-feel risk: hook pattern '{hook_pattern}' repeats the last 3 posts.")
        suggestions.append("Use a personal proof line, quote/idea hook, failed-request hook, or direct claim instead.")
    same_artifact_history = [
        item
        for item in recent_history[-5:]
        if item.get("failure_mode")
        and item.get("failure_mode") == routing.get("failure_mode")
        and item.get("artifact_type")
        and item.get("artifact_type") == routing.get("artifact_type")
    ]
    if same_artifact_history:
        score -= 8
        artifact_type = routing.get("artifact_type") or "unknown"
        reasons.append(f"Near-duplicate risk: recent post used the same failure_mode and artifact_type '{artifact_type}'.")
        suggestions.append("Change the research-work artifact, or start Part 1 from a narrower artifact-specific failure.")
    same_problem_frame_history = [
        item
        for item in recent_history[-5:]
        if item.get("hook_pattern") == hook_pattern
        and (
            item.get("failure_mode") == routing.get("failure_mode")
            or item.get("workflow_stage") == routing.get("workflow_stage")
        )
    ]
    if same_problem_frame_history:
        score -= 6
        reasons.append("Near-duplicate risk: hook pattern repeats with the same failure or workflow stage.")
        suggestions.append("Replace the generic opening frame with the artifact-specific contrast from selected routing.")
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
    if contract_report.warnings and decision == "publish":
        decision = "draft"

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
        "Existing pattern library:\n"
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


def build_revision_prompt(
    thread_text: str,
    candidate: dict,
    routing: dict,
    analysis: dict,
    quality_reasons: list[str],
    revision_suggestions: list[str],
    evaluator_result: dict,
) -> str:
    return (
        "You are revising one Korean Threads chain for @arxiv.ai.\n"
        "Return strict ThreadCandidate v1 JSON only. Keep the same verified source URL and do not invent facts.\n"
        "Preserve the four semantic roles: hook, diagnosis, action, source.\n"
        "Fix the concrete issues below while keeping every part under 500 characters.\n\n"
        f"Quality reasons:\n{json.dumps(quality_reasons, ensure_ascii=False, indent=2)}\n\n"
        f"Revision suggestions:\n{json.dumps(revision_suggestions, ensure_ascii=False, indent=2)}\n\n"
        f"Evaluator feedback:\n{json.dumps(evaluator_result, ensure_ascii=False, indent=2)}\n\n"
        f"Routing:\n{json.dumps(routing, ensure_ascii=False, indent=2)}\n\n"
        f"Candidate analysis:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        f"Verified candidate:\n{json.dumps(candidate, ensure_ascii=False, indent=2)}\n\n"
        f"Current thread:\n{thread_text}"
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


def apply_evaluator_gate(gate: dict, evaluator_result: dict, minimum_score: int = EVALUATOR_PUBLISH_SCORE) -> dict:
    combined = {
        "quality_score": gate.get("quality_score", 0),
        "decision": gate.get("decision", "discard"),
        "reasons": list(gate.get("reasons", [])),
        "revision_suggestions": list(gate.get("revision_suggestions", [])),
    }
    if combined["decision"] != "publish":
        return combined

    evaluator_decision = str(evaluator_result.get("decision") or "revise").lower()
    try:
        evaluator_score = int(evaluator_result.get("score") or 0)
    except (TypeError, ValueError):
        evaluator_score = 0

    if evaluator_decision == "discard":
        combined["decision"] = "discard"
    elif evaluator_decision != "publish" or evaluator_score < minimum_score:
        combined["decision"] = "draft"

    if combined["decision"] != "publish":
        combined["reasons"].append(
            f"Evaluator veto: decision={evaluator_decision}, score={evaluator_score}, required={minimum_score}."
        )
        combined["revision_suggestions"].extend(evaluator_result.get("revision_suggestions", []))
    return combined


def apply_daily_guarantee_gate(
    gate: dict,
    evaluator_result: dict,
    revision_attempted: bool,
    minimum_quality: int = DRAFT_QUALITY_SCORE,
    minimum_evaluator_score: int = EVALUATOR_PUBLISH_SCORE,
) -> dict:
    combined = {
        "quality_score": gate.get("quality_score", 0),
        "decision": gate.get("decision", "discard"),
        "reasons": list(gate.get("reasons", [])),
        "revision_suggestions": list(gate.get("revision_suggestions", [])),
    }
    if combined["decision"] == "publish" or combined["decision"] == "discard" or not revision_attempted:
        return combined
    if any(str(reason).startswith("Contract warning:") for reason in combined["reasons"]):
        return combined
    try:
        evaluator_score = int(evaluator_result.get("score") or 0)
    except (TypeError, ValueError):
        evaluator_score = 0
    evaluator_decision = str(evaluator_result.get("decision") or "revise").lower()
    if (
        int(combined["quality_score"] or 0) >= minimum_quality
        and evaluator_decision == "publish"
        and evaluator_score >= minimum_evaluator_score
    ):
        combined["decision"] = "publish"
        combined["reasons"].append(
            "Daily guarantee soft promotion: revised candidate passed strict contract and evaluator approval."
        )
    return combined


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


def is_size_limit(response: requests.Response) -> bool:
    if response.status_code not in {413, 429}:
        return False
    text = response.text.lower()
    return (
        "request too large" in text
        or "tokens per minute" in text
        or "rate_limit_exceeded" in text
    )


def request_options(provider: str, model: str, response_schema: dict | None = None) -> dict:
    if response_schema:
        options = {
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "thread_candidate_v1",
                    "strict": True,
                    "schema": response_schema,
                },
            },
        }
        if provider == "openrouter":
            options["provider"] = {"require_parameters": True}
    else:
        options = {"response_format": {"type": "json_object"}}
    if provider == "groq" and model.startswith("openai/gpt-oss-"):
        options["include_reasoning"] = False
        options["reasoning_effort"] = "low"
    return options


def api_key_for_provider(provider: str) -> str:
    if provider == "openrouter":
        return os.environ.get("OPENROUTER_API_KEY", "")
    if provider == "openai":
        return os.environ.get("OPENAI_API_KEY", "")
    if provider == "groq":
        return os.environ.get("GROQ_API_KEY", "")
    return ""


def default_model_for_provider(provider: str) -> str:
    if provider == "openrouter":
        return os.environ.get("OPENROUTER_MODEL") or os.environ.get("LLM_MODEL") or DEFAULT_MODEL
    if provider == "openai":
        return os.environ.get("OPENAI_MODEL") or os.environ.get("LLM_MODEL") or DEFAULT_OPENAI_MODEL
    if provider == "groq":
        return os.environ.get("GROQ_MODEL") or os.environ.get("LLM_MODEL") or DEFAULT_GROQ_MODEL
    raise SystemExit(f"Unsupported LLM provider: {provider}")


def fallback_provider_chain(provider: str, model: str) -> list[dict]:
    provider = provider.lower()
    chain = [
        {
            "provider": provider,
            "model": model,
            "api_key": api_key_for_provider(provider),
        }
    ]
    configured_fallbacks = os.environ.get("LLM_FALLBACK_PROVIDERS", "").strip()
    if configured_fallbacks:
        fallback_providers = [item.strip().lower() for item in configured_fallbacks.split(",") if item.strip()]
    else:
        legacy_fallback = os.environ.get("LLM_FALLBACK_PROVIDER", DEFAULT_FALLBACK_PROVIDER).lower().strip()
        fallback_providers = [legacy_fallback] if legacy_fallback else []
    seen_providers = {provider}
    for fallback_provider in fallback_providers:
        if fallback_provider in seen_providers or not api_key_for_provider(fallback_provider):
            continue
        seen_providers.add(fallback_provider)
        fallback_model = default_model_for_provider(fallback_provider)
        if len(fallback_providers) == 1:
            fallback_model = os.environ.get("LLM_FALLBACK_MODEL") or fallback_model
        chain.append(
            {
                "provider": fallback_provider,
                "model": fallback_model,
                "api_key": api_key_for_provider(fallback_provider),
            }
        )
    return chain


def call_llm(
    provider: str,
    api_key: str,
    model: str,
    prompt: str,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    response_schema: dict | None = None,
) -> dict:
    provider = provider.lower()
    endpoint = {
        "groq": GROQ_CHAT_COMPLETIONS_URL,
        "openrouter": OPENROUTER_CHAT_COMPLETIONS_URL,
        "openai": OPENAI_CHAT_COMPLETIONS_URL,
    }.get(provider)
    if endpoint is None:
        raise SystemExit(f"Unsupported LLM provider: {provider}")

    output_tokens = max_output_tokens
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
            **request_options(provider, model, response_schema),
        }
        token_limit_key = "max_tokens" if provider == "openrouter" else "max_completion_tokens"
        request_body[token_limit_key] = output_tokens
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if provider == "openrouter":
            headers["HTTP-Referer"] = os.environ.get("OPENROUTER_HTTP_REFERER", "https://github.com/gyutaetae/threads-agentic-editor-workflow")
            headers["X-Title"] = os.environ.get("OPENROUTER_APP_TITLE", "threads-agentic-editor-workflow")

        response = requests.post(
            endpoint,
            headers=headers,
            json=request_body,
            timeout=120,
        )
        if response.ok:
            return response.json()
        if is_size_limit(response) and output_tokens > 300 and attempt < 3:
            next_tokens = max(300, int(output_tokens * 0.65))
            print(
                f"{provider} request exceeded token limits; retrying with "
                f"max_completion_tokens={next_tokens} (attempt {attempt}/3)."
            )
            output_tokens = next_tokens
            continue
        if response.status_code == 429 and attempt < 3:
            delay = retry_delay_seconds(response) + 2
            print(f"{provider} rate limited; retrying in {delay:.1f}s (attempt {attempt}/3).")
            time.sleep(delay)
            continue
        raise SystemExit(f"{provider} API error {response.status_code}:\n{response.text}")

    raise SystemExit(f"{provider} API did not return a response after retries.")


def call_groq(api_key: str, model: str, prompt: str, max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS) -> dict:
    return call_llm("groq", api_key, model, prompt, max_output_tokens)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one approved Threads chain with an OpenAI-compatible LLM.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--candidates-path", required=True)
    parser.add_argument("--playbook-path", default="docs/threads-channel-playbook.md")
    parser.add_argument("--history-path", default="content-history.jsonl")
    parser.add_argument("--output-path", default="approved-thread-chain.txt")
    parser.add_argument("--spec-output-path")
    parser.add_argument("--metadata-path", default="daily-editor/auto-thread-metadata.json")
    parser.add_argument("--metrics-path", default="threads-post-metrics.csv")
    parser.add_argument("--quote-bank-path", default="data/quote_bank.json")
    parser.add_argument("--weekly-memory-path", default="daily-editor/memory/weekly-editorial-memory.md")
    parser.add_argument("--learnings-path", default="docs/learnings.md")
    parser.add_argument("--skills-library-dir", default="docs/thread-pattern-library.md", help="Pattern library path. Accepts the consolidated docs file or a legacy directory.")
    parser.add_argument("--curation-log-path", default="daily-editor/curation/codex-curation-log.jsonl")
    parser.add_argument("--attempt-history-path")
    parser.add_argument("--attempt-cooldown-days", type=int, default=DEFAULT_ATTEMPT_COOLDOWN_DAYS)
    parser.add_argument("--review-dir", default="daily-editor/review")
    parser.add_argument("--run-log-dir", default="daily-editor/runs")
    parser.add_argument("--evaluation-dir", default="daily-editor/evaluations")
    parser.add_argument("--skip-evaluator", action="store_true")
    parser.add_argument("--guarantee-daily", action="store_true")
    parser.add_argument("--evaluator-provider", choices=["groq", "openrouter", "openai"], default=os.environ.get("EVALUATOR_PROVIDER"))
    parser.add_argument("--evaluator-model", default=os.environ.get("EVALUATOR_MODEL"))
    parser.add_argument("--post-slot", choices=["morning", "evening"], default=os.environ.get("POST_SLOT", "morning"))
    parser.add_argument("--posts-per-day", type=int, choices=[1, 2], default=int(os.environ.get("POSTS_PER_DAY", "1")))
    parser.add_argument("--experiment-group", default=os.environ.get("EXPERIMENT_GROUP", "manual"))
    parser.add_argument("--generation-candidates", type=int, default=int(os.environ.get("GENERATION_CANDIDATES", str(DEFAULT_GENERATION_CANDIDATES))))
    parser.add_argument("--provider", choices=["groq", "openrouter", "openai"], default=os.environ.get("LLM_PROVIDER", DEFAULT_PROVIDER))
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=int(os.environ.get("LLM_MAX_OUTPUT_TOKENS") or os.environ.get("GROQ_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS))),
    )
    args = parser.parse_args()

    if args.model is None:
        args.model = default_model_for_provider(args.provider)

    api_key = api_key_for_provider(args.provider)
    if not api_key:
        env_name = {
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
        }[args.provider]
        raise SystemExit(f"{env_name} is required.")

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
    curation_records = load_curation_log(Path(args.curation_log_path))
    attempted_urls = (
        load_recent_attempted_urls(Path(args.attempt_history_path), args.date, args.attempt_cooldown_days)
        if args.attempt_history_path
        else set()
    )
    review_dir = Path(args.review_dir)
    selected_candidates = choose_candidates(
        candidates,
        args.post_slot,
        max(1, args.generation_candidates),
        curation_records,
        attempted_urls,
    )
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
        text = ""
        data = None
        json_error = None
        generation_error = ""
        generation_provider = args.provider
        generation_model = args.model
        generation_actual_model = args.model
        provider_chain = fallback_provider_chain(args.provider, args.model)
        for provider_index, provider_config in enumerate(provider_chain):
            generation_provider = provider_config["provider"]
            generation_model = provider_config["model"]
            for parse_attempt in range(1, 3):
                try:
                    payload = call_llm(
                        generation_provider,
                        provider_config["api_key"],
                        generation_model,
                        prompt,
                        args.max_output_tokens,
                        response_schema=THREAD_CANDIDATE_SCHEMA,
                    )
                except SystemExit as exc:
                    generation_error = f"{generation_provider} generation failed: {exc}"
                    print(generation_error)
                    break
                generation_actual_model = str(payload.get("model") or generation_model)
                text = extract_text(payload)
                try:
                    data = normalize_thread_candidate(extract_json(text), selected_candidate, routing)
                    json_error = None
                    generation_error = ""
                    break
                except (json.JSONDecodeError, ValueError) as exc:
                    json_error = exc
                    generation_error = f"{generation_provider} returned malformed JSON: {exc}"
                    if parse_attempt < 2:
                        print(f"{generation_provider} returned malformed JSON; retrying generation once.")
            if data is not None:
                break
            if provider_index + 1 < len(provider_chain):
                next_provider = provider_chain[provider_index + 1]["provider"]
                print(f"{generation_provider} returned malformed JSON after retries; trying {next_provider}.")

        if data is None:
            failure_reason = generation_error
            if not failure_reason and json_error:
                failure_reason = f"{generation_provider} returned malformed JSON: {json_error}"
            if not failure_reason:
                failure_reason = "model returned no extractable thread JSON"
            fallback_thread_text = build_fallback_thread(selected_candidate, routing, analysis)
            try:
                validate_thread(fallback_thread_text)
                fallback_gate = quality_gate(fallback_thread_text, routing, recent_hooks, recent_history)
            except SystemExit as fallback_exc:
                fallback_gate = {
                    "quality_score": 0,
                    "decision": "discard",
                    "reasons": [
                        failure_reason,
                        f"Fallback thread failed validation: {fallback_exc}",
                    ],
                    "revision_suggestions": ["Review the raw model output and regenerate manually."],
                }

            if fallback_gate.get("decision") != "discard":
                fallback_gate["decision"] = "draft"
                fallback_gate.setdefault("reasons", []).append(
                    "Fallback content is review-only and can never replace the pinned Gemma writer for auto-publishing."
                )
                generated_options.append(
                    {
                        "option": index,
                        "provider": generation_provider,
                        "model": generation_model,
                        "actual_model": generation_actual_model,
                        "candidate": selected_candidate,
                        "analysis": analysis,
                        "routing": routing,
                        "quote_context": quote_context,
                        "data": {
                            "thread_text": fallback_thread_text,
                            "topic": routing["human_signal_type"],
                            "source_count": 1 if selected_candidate.get("url") else 0,
                            "format": routing["format_type"],
                            "source_name": selected_candidate.get("title") or selected_candidate.get("name") or "",
                            "source_url": selected_candidate.get("url") or "",
                            "quote_used": False,
                            "quote_id": "",
                        },
                        "thread_text": fallback_thread_text,
                        "quality_score": fallback_gate["quality_score"],
                        "quality_decision": fallback_gate["decision"],
                        "quality_reasons": [
                            failure_reason,
                            *fallback_gate["reasons"],
                        ],
                        "revision_suggestions": fallback_gate["revision_suggestions"],
                        "writer_prompt": prompt,
                        "model_output_raw": text,
                    }
                )
                continue

            generated_options.append(
                {
                    "option": index,
                    "provider": generation_provider,
                    "model": generation_model,
                    "actual_model": generation_actual_model,
                    "candidate_title": selected_candidate.get("title"),
                    "candidate_url": selected_candidate.get("url"),
                    "quality_score": 0,
                    "quality_decision": "discard",
                    "quality_reasons": [failure_reason],
                    "raw_text_preview": text[:1200],
                    "writer_prompt": prompt,
                    "model_output_raw": text,
                }
            )
            continue

        thread_text = normalize_thread_text(str(data.get("thread_text", "")).strip())
        try:
            validate_thread(thread_text)
            gate = quality_gate(thread_text, routing, recent_hooks, recent_history)
        except SystemExit as exc:
            gate = {
                "quality_score": 0,
                "decision": "discard",
                "reasons": [str(exc)],
                "revision_suggestions": ["Regenerate with stronger format compliance."],
            }
        if gate["decision"] == "discard":
            fallback_thread_text = build_fallback_thread(selected_candidate, routing, analysis)
            try:
                validate_thread(fallback_thread_text)
                fallback_gate = quality_gate(fallback_thread_text, routing, recent_hooks, recent_history)
            except SystemExit:
                fallback_gate = {"decision": "discard"}
            if fallback_gate.get("decision") != "discard":
                thread_text = fallback_thread_text
                fallback_gate["decision"] = "draft"
                fallback_gate.setdefault("reasons", []).append(
                    "Fallback content is review-only after the model candidate failed the canonical contract."
                )
                gate = fallback_gate

        generated_options.append(
            {
                "option": index,
                "provider": generation_provider,
                "model": generation_model,
                "actual_model": generation_actual_model,
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
        if args.attempt_history_path:
            append_generation_attempts(Path(args.attempt_history_path), args.date, generated_options)
        raise SystemExit("All generated options failed before thread extraction.")

    selected_candidate = best["candidate"]
    analysis = best["analysis"]
    routing = best["routing"]
    data = best["data"]
    thread_text = best["thread_text"]
    selected_provider = best.get("provider") or args.provider
    selected_model = best.get("model") or args.model
    selected_actual_model = best.get("actual_model") or selected_model
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
    evaluator_provider = args.evaluator_provider or selected_provider
    evaluator_model = args.evaluator_model or selected_model
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
            evaluator_payload = call_llm(
                evaluator_provider,
                api_key_for_provider(evaluator_provider),
                evaluator_model,
                evaluator_prompt,
                min(args.max_output_tokens, 800),
            )
            evaluator_text = extract_text(evaluator_payload)
            evaluator_result = extract_json(evaluator_text)
            evaluator_result["model_output_raw"] = evaluator_text
        except SystemExit as exc:
            evaluator_result = fallback_evaluation(f"Evaluator failed: {exc}")
        except Exception as exc:
            evaluator_result = fallback_evaluation(f"Evaluator failed: {exc}")

    if not args.skip_evaluator:
        gate = apply_evaluator_gate(gate, evaluator_result)

    publish_mode = "primary"
    revision_attempted = False
    revision_outcome = "not_needed"
    if (
        args.guarantee_daily
        and gate["decision"] == "draft"
        and int(gate.get("quality_score") or 0) >= DRAFT_QUALITY_SCORE
        and not args.skip_evaluator
    ):
        revision_attempted = True
        revision_outcome = "failed"
        revision_prompt = build_revision_prompt(
            thread_text=thread_text,
            candidate=selected_candidate,
            routing=routing,
            analysis=analysis,
            quality_reasons=gate["reasons"],
            revision_suggestions=[
                *gate["revision_suggestions"],
                *list(evaluator_result.get("revision_suggestions") or []),
            ],
            evaluator_result=evaluator_result,
        )
        try:
            revision_payload = call_llm(
                selected_provider,
                api_key_for_provider(selected_provider),
                selected_model,
                revision_prompt,
                args.max_output_tokens,
                response_schema=THREAD_CANDIDATE_SCHEMA,
            )
            revision_text = extract_text(revision_payload)
            revised_data = normalize_thread_candidate(
                extract_json(revision_text),
                selected_candidate,
                routing,
            )
            revised_thread = normalize_thread_text(str(revised_data.get("thread_text", "")).strip())
            validate_thread(revised_thread)
            revised_gate = quality_gate(revised_thread, routing, recent_hooks, recent_history)
            revised_evaluator_prompt = build_evaluator_prompt(
                thread_text=revised_thread,
                routing=routing,
                analysis=analysis,
                recent_history=recent_history,
                persistent_learnings=persistent_learnings,
                skill_library=skill_library,
            )
            revised_evaluator_payload = call_llm(
                evaluator_provider,
                api_key_for_provider(evaluator_provider),
                evaluator_model,
                revised_evaluator_prompt,
                min(args.max_output_tokens, 800),
            )
            revised_evaluator_text = extract_text(revised_evaluator_payload)
            revised_evaluator_result = extract_json(revised_evaluator_text)
            revised_evaluator_result["model_output_raw"] = revised_evaluator_text
            revised_gate = apply_evaluator_gate(revised_gate, revised_evaluator_result)
            revised_gate = apply_daily_guarantee_gate(
                revised_gate,
                revised_evaluator_result,
                revision_attempted=True,
            )
            if revised_gate["decision"] == "publish":
                data = revised_data
                thread_text = revised_thread
                gate = revised_gate
                evaluator_prompt = revised_evaluator_prompt
                evaluator_result = revised_evaluator_result
                quote_used = data.get("quote_used") is True
                quote_id = str(data.get("quote_id") or "").strip()
                quote_suggestion = validate_quote_selection(thread_text, data, source_item)
                publish_mode = "revised"
                revision_outcome = "publish"
            else:
                revision_outcome = revised_gate["decision"]
        except SystemExit as exc:
            revision_outcome = f"error: {exc}"
        except Exception as exc:
            revision_outcome = f"error: {exc}"

    metadata = {
        "date": args.date,
        "provider": selected_provider,
        "model": selected_model,
        "actual_model": selected_actual_model,
        "requested_provider": args.provider,
        "requested_model": args.model,
        "post_slot": args.post_slot,
        "posts_per_day": args.posts_per_day,
        "experiment_group": args.experiment_group,
        "generation_candidates": len(selected_candidates),
        "selected_option": best["option"],
        "publish_mode": publish_mode,
        "revision_attempted": revision_attempted,
        "revision_outcome": revision_outcome,
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
        "pattern_library_path": args.skills_library_dir,
        "curation_log_path": args.curation_log_path,
        "curation_records_used": len(curation_records),
        "selected_candidate_curation_bonus": curation_bonus(selected_candidate, curation_records),
        "evaluator": {
            "provider": evaluator_provider,
            "model": evaluator_model,
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
                "provider": option.get("provider"),
                "model": option.get("model"),
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
        "artifact_type": data.get("artifact_type") or routing.get("artifact_type", ""),
        "artifact_output": data.get("artifact_output") or routing.get("artifact_output", ""),
        "reader_test": data.get("reader_test") or routing.get("reader_test", ""),
        "failure_judgment": data.get("failure_judgment") or routing.get("failure_judgment", ""),
        "hook_pattern": data.get("hook_pattern") or classify_hook_pattern(thread_text),
        "structure_pattern": data.get("structure_pattern", ""),
        "closer_pattern": data.get("closer_pattern", ""),
        "reusable_unit_type": data.get("reusable_unit_type") or routing.get("reusable_unit_type", ""),
        "quote_used": quote_used,
        "quote_id": quote_id,
        "quote_speaker": quote_suggestion.get("speaker", "") if quote_suggestion else "",
        "quote_source_url": quote_suggestion.get("source_url", "") if quote_suggestion else "",
    }

    spec_path = Path(args.spec_output_path) if args.spec_output_path else Path(args.output_path).with_name("approved-thread-spec.json")
    spec_metadata = {
        "topic": metadata["topic"],
        "format": metadata["format"],
        "workflow_stage": metadata["workflow_stage"],
        "failure_mode": metadata["failure_mode"],
        "artifact_type": metadata["artifact_type"],
        "reusable_unit_type": metadata["reusable_unit_type"],
        "hook_pattern": metadata["hook_pattern"],
        "source_name": metadata["source_name"],
        "source_urls": [metadata["source_url"]] if metadata["source_url"] else [],
    }
    thread_spec = build_thread_spec(
        thread_text,
        metadata=spec_metadata,
        origin=f"auto_{selected_provider}",
        generation={
            "provider": selected_provider,
            "requested_model": selected_model,
            "actual_model": selected_actual_model,
            "prompt_contract_version": PROMPT_CONTRACT_VERSION,
        },
    )
    spec_report = validate_thread_spec(thread_spec, require_metadata=True)
    if spec_report.errors:
        gate["decision"] = "discard"
        gate["reasons"].extend(spec_report.errors)
    metadata_warnings = [warning for warning in spec_report.warnings if warning.startswith("ThreadSpec metadata")]
    if metadata_warnings and gate["decision"] == "publish":
        gate["decision"] = "draft"
        gate["reasons"].extend(f"ThreadSpec warning: {warning}" for warning in metadata_warnings)
    metadata["quality_decision"] = gate["decision"]
    metadata["quality_reasons"] = gate["reasons"]
    metadata["revision_suggestions"] = gate["revision_suggestions"]
    metadata["thread_spec_path"] = str(spec_path)
    write_spec(spec_path, thread_spec)

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
            "pattern_library_path": args.skills_library_dir,
            "curation_log_path": args.curation_log_path,
            "curation_records_used": len(curation_records),
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
    if args.attempt_history_path:
        append_generation_attempts(Path(args.attempt_history_path), args.date, generated_options)

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
