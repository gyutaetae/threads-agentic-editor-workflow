import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ENGAGEMENT_KEYS = ["audience_replies", "reposts", "quotes", "saves", "profile_visits", "follows_gained"]


def read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9가-힣_-]+", "-", str(text or "").strip())
    slug = re.sub(r"-{2,}", "-", slug).strip("-").lower()
    return slug[:80] or "skill"


def normalize_key(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9가-힣]+", "", str(text or "").lower())


def compact(text: str, max_chars: int = 180) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "..."


def int_field(row: dict, key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def engagement(row: dict) -> int:
    total = sum(int_field(row, key) for key in ENGAGEMENT_KEYS)
    if total == 0:
        total = int_field(row, "likes")
    return total


def read_metrics(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def metric_index(rows: list[dict]) -> dict[str, dict]:
    indexed = {}
    for row in rows:
        if row.get("thread_url"):
            indexed[f"url:{row['thread_url']}"] = row
        if row.get("post_id"):
            indexed[f"post:{row['post_id']}"] = row
    return indexed


def find_metric(run: dict, indexed_metrics: dict[str, dict]) -> dict | None:
    thread_url = run.get("thread_url")
    if thread_url and f"url:{thread_url}" in indexed_metrics:
        return indexed_metrics[f"url:{thread_url}"]
    for post_id in run.get("post_ids") or []:
        if f"post:{post_id}" in indexed_metrics:
            return indexed_metrics[f"post:{post_id}"]
    return None


def read_logs(run_dir: Path, evaluation_dir: Path, metrics_path: Path) -> list[dict]:
    metrics = read_metrics(metrics_path)
    indexed_metrics = metric_index(metrics)
    average_engagement = (
        sum(engagement(row) for row in metrics) / len(metrics)
        if metrics
        else 0
    )

    runs_by_id = {}
    for path in sorted(run_dir.glob("*.json")) if run_dir.exists() else []:
        data = read_json(path)
        if not data:
            continue
        run_id = str(data.get("run_id") or path.stem)
        runs_by_id[run_id] = {"path": path, "data": data}

    records = []
    for path in sorted(evaluation_dir.glob("*.eval.json")) if evaluation_dir.exists() else []:
        data = read_json(path)
        if not data:
            continue
        run_id = str(data.get("run_id") or path.name.removesuffix(".eval.json"))
        run_entry = runs_by_id.get(run_id, {"path": None, "data": {}})
        metric = find_metric(run_entry["data"], indexed_metrics)
        records.append(
            {
                "run_id": run_id,
                "run_path": str(run_entry["path"]) if run_entry["path"] else "",
                "evaluation_path": str(path),
                "run": run_entry["data"],
                "evaluation": data.get("evaluation") or data,
                "metric": metric,
                "average_engagement": average_engagement,
            }
        )
    return records


def record_topic(record: dict) -> str:
    run = record["run"]
    return run.get("topic") or run.get("selected_candidate", {}).get("title") or "unknown"


def record_format(record: dict) -> str:
    run = record["run"]
    evaluation = record["evaluation"]
    return (
        run.get("format")
        or run.get("routing", {}).get("format_type")
        or evaluation.get("format")
        or "unknown"
    )


def promotion_reasons(record: dict, min_score: int) -> list[str]:
    evaluation = record["evaluation"]
    reasons = []
    score = int_field(evaluation, "score")
    decision = str(evaluation.get("decision") or "").lower()
    metric = record.get("metric")
    metric_score = engagement(metric) if metric else 0

    if score >= min_score:
        reasons.append(f"evaluator score {score} >= {min_score}")
    if decision in {"publish", "approved", "keep"}:
        reasons.append(f"decision={decision}")
    if metric and record["average_engagement"] > 0 and metric_score > record["average_engagement"]:
        reasons.append(f"engagement {metric_score} > 최근 평균 {record['average_engagement']:.1f}")
    return reasons


def should_promote_record(record: dict, min_score: int) -> bool:
    evaluation = record["evaluation"]
    score = int_field(evaluation, "score")
    decision = str(evaluation.get("decision") or "").lower()
    return score >= min_score and decision in {"publish", "approved", "keep"}


def proposal_evidence(record: dict, min_score: int) -> dict:
    run = record["run"]
    metric = record.get("metric")
    return {
        "run_id": record["run_id"],
        "topic": record_topic(record),
        "format": record_format(record),
        "thread_url": run.get("thread_url") or "",
        "score": int_field(record["evaluation"], "score"),
        "decision": record["evaluation"].get("decision") or "",
        "engagement": engagement(metric) if metric else None,
        "reasons": promotion_reasons(record, min_score),
    }


def build_learning_candidates(records: list[dict], existing_learnings: str, min_score: int) -> list[dict]:
    existing_key = normalize_key(existing_learnings)
    candidates = []
    seen = set()

    for record in records:
        evaluation = record["evaluation"]
        text = compact(evaluation.get("learning_candidate") or "", 240)
        key = normalize_key(text)
        if not text or key in seen or key in existing_key:
            continue
        if not should_promote_record(record, min_score):
            continue
        seen.add(key)
        candidates.append(
            {
                "text": text,
                "target": "docs/learnings.md",
                "evidence": [proposal_evidence(record, min_score)],
            }
        )
    return candidates


def repeated_revision_candidates(records: list[dict], min_count: int = 2) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    display_text = {}

    for record in records:
        for suggestion in record["evaluation"].get("revision_suggestions") or []:
            text = compact(suggestion, 220)
            key = normalize_key(text)
            if not key:
                continue
            grouped[key].append(record)
            display_text[key] = text

    candidates = []
    for key, grouped_records in grouped.items():
        if len(grouped_records) < min_count:
            continue
        candidates.append(
            {
                "text": display_text[key],
                "count": len(grouped_records),
                "target": "docs/learnings.md or skill update",
                "evidence": [proposal_evidence(record, 0) for record in grouped_records],
            }
        )
    return candidates


def build_skill_candidates(records: list[dict], min_score: int) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    summaries: dict[str, Counter] = defaultdict(Counter)

    for record in records:
        evaluation = record["evaluation"]
        skill = evaluation.get("skill_candidate")
        if not isinstance(skill, dict) or not should_promote_record(record, min_score):
            continue
        name = safe_slug(skill.get("name") or record_format(record))
        grouped[name].append(record)
        if skill.get("summary"):
            summaries[name][compact(skill["summary"], 220)] += 1

    candidates = []
    for name, grouped_records in grouped.items():
        summary = summaries[name].most_common(1)[0][0] if summaries[name] else ""
        candidates.append(
            {
                "name": name,
                "summary": summary,
                "target": f"skills_library/{name}.proposed.md",
                "evidence": [proposal_evidence(record, min_score) for record in grouped_records],
                "records": grouped_records,
            }
        )
    return candidates


def build_proposals(records: list[dict], existing_learnings: str, min_score: int = 85) -> dict:
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "records_analyzed": len(records),
        "learning_candidates": build_learning_candidates(records, existing_learnings, min_score),
        "revision_candidates": repeated_revision_candidates(records),
        "skill_candidates": build_skill_candidates(records, min_score),
    }


def render_evidence(evidence: list[dict]) -> list[str]:
    lines = []
    for item in evidence:
        reasons = "; ".join(item["reasons"]) if item.get("reasons") else "승격 근거 없음"
        metric = "" if item.get("engagement") is None else f"; engagement={item['engagement']}"
        url = f"; {item['thread_url']}" if item.get("thread_url") else ""
        lines.append(
            f"- {item['run_id']} | {item['format']} | {item['topic']} | "
            f"score={item['score']} | {reasons}{metric}{url}"
        )
    return lines


def render_learnings_markdown(proposals: dict, min_score: int) -> str:
    lines = [
        "# 제안된 Learnings",
        "",
        f"생성 시각: {proposals['generated_at']}",
        f"분석한 기록 수: {proposals['records_analyzed']}",
        "",
        "이 파일은 승인 대기열입니다. 사람이 `docs/learnings.md` 또는 `skills_library/`로 승격하기 전까지 생성 규칙으로 읽지 않습니다.",
        "",
        "## 승격 기준",
        "",
        f"- evaluator score가 {min_score} 이상이고 decision이 publish/approved/keep이며 기존 규칙과 중복되지 않을 때 승격합니다.",
        "- 반복 수정 제안은 일회성 문장 문제가 아니라 지속적인 작성 규칙일 때만 승격합니다.",
        "- skill 후보는 여러 글에서 재사용 가능한 실행 경로일 때 승격합니다.",
        "",
        "## Learning 후보",
        "",
    ]

    if not proposals["learning_candidates"]:
        lines.append("- 새로 승격할 durable learning 후보가 없습니다.")
    for index, candidate in enumerate(proposals["learning_candidates"], start=1):
        lines.extend(
            [
                f"### L{index}",
                "",
                f"제안 문장: `- {candidate['text']}`",
                f"승격 위치: `{candidate['target']}`",
                "",
                "근거:",
                *render_evidence(candidate["evidence"]),
                "",
            ]
        )

    lines.extend(["## 반복 수정 후보", ""])
    if not proposals["revision_candidates"]:
        lines.append("- 아직 반복되는 수정 패턴이 없습니다.")
        lines.append("")
    for index, candidate in enumerate(proposals["revision_candidates"], start=1):
        lines.extend(
            [
                f"### R{index}",
                "",
                f"규칙 후보: {candidate['text']}",
                f"반복 횟수: {candidate['count']}",
                f"승격 위치: `{candidate['target']}`",
                "",
                "근거:",
                *render_evidence(candidate["evidence"]),
                "",
            ]
        )

    lines.extend(["## Skill 후보", ""])
    if not proposals["skill_candidates"]:
        lines.append("- 결정화할 skill 후보가 없습니다.")
    for candidate in proposals["skill_candidates"]:
        lines.extend(
            [
                f"- `{candidate['target']}`",
                f"  요약: {candidate['summary'] or '요약 없음.'}",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def final_thread_excerpt(record: dict, max_parts: int = 3) -> list[str]:
    parts = record["run"].get("final_thread_parts") or []
    if not parts and record["run"].get("final_thread"):
        parts = str(record["run"]["final_thread"]).split("---")
    return [compact(part, 260) for part in parts[:max_parts] if str(part).strip()]


def render_skill_markdown(candidate: dict) -> str:
    lines = [
        f"# 제안된 Skill: {candidate['name']}",
        "",
        "상태: proposed",
        "",
        "검토 후 유용한 부분을 기존 skill에 병합하거나 안정된 skill 파일로 이름을 바꿔 승격합니다.",
        "",
        "## 요약",
        "",
        candidate["summary"] or "evaluator가 제공한 요약이 없습니다.",
        "",
        "## 근거",
        "",
        *render_evidence(candidate["evidence"]),
        "",
        "## 재사용 패턴",
        "",
        "- 글이 해결하려는 구체적인 research failure에서 시작합니다.",
        "- source fact와 계정의 적용 해석을 분리합니다.",
        "- 복사 가능한 prompt, checklist, agent instruction 중 하나를 포함합니다.",
        "- 고정 템플릿이 되지 않도록 구조를 유연하게 둡니다.",
        "",
        "## 예시 발췌",
        "",
    ]

    excerpts_added = False
    for record in candidate["records"][:3]:
        excerpts = final_thread_excerpt(record)
        if not excerpts:
            continue
        excerpts_added = True
        lines.append(f"### {record['run_id']}")
        lines.append("")
        for excerpt in excerpts:
            lines.append(f"- {excerpt}")
        lines.append("")
    if not excerpts_added:
        lines.append("- final thread 발췌가 없습니다.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_skill_proposals(skill_candidates: list[dict], skills_library_dir: Path) -> list[Path]:
    written = []
    for candidate in skill_candidates:
        path = skills_library_dir / f"{candidate['name']}.proposed.md"
        write_text(path, render_skill_markdown(candidate))
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Propose self-improvement learnings from Threads run and evaluator logs.")
    parser.add_argument("--run-log-dir", default="daily-editor/runs")
    parser.add_argument("--evaluation-dir", default="daily-editor/evaluations")
    parser.add_argument("--metrics-path", default="threads-post-metrics.csv")
    parser.add_argument("--learnings-path", default="docs/learnings.md")
    parser.add_argument("--output-path", default="daily-editor/proposals/learnings.proposed.md")
    parser.add_argument("--skills-library-dir", default="skills_library")
    parser.add_argument("--min-score", type=int, default=85)
    parser.add_argument("--skip-skill-proposals", action="store_true")
    args = parser.parse_args()

    records = read_logs(Path(args.run_log_dir), Path(args.evaluation_dir), Path(args.metrics_path))
    existing_learnings = Path(args.learnings_path).read_text(encoding="utf-8") if Path(args.learnings_path).exists() else ""
    proposals = build_proposals(records, existing_learnings, args.min_score)
    write_text(Path(args.output_path), render_learnings_markdown(proposals, args.min_score))
    print(f"Wrote {args.output_path}")

    if not args.skip_skill_proposals:
        written = write_skill_proposals(proposals["skill_candidates"], Path(args.skills_library_dir))
        for path in written:
            print(f"Wrote {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
