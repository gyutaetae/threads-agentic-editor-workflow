import argparse
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from scripts.thread_spec import build_thread_spec, thread_text_from_spec, validate_thread_spec, write_spec
except ModuleNotFoundError:
    from thread_spec import build_thread_spec, thread_text_from_spec, validate_thread_spec, write_spec


KST = timezone(timedelta(hours=9), "KST")
DEFAULT_AVAILABLE_DIR = Path("daily-editor/reserve/available")
DEFAULT_USED_DIR = Path("daily-editor/reserve/used")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def published_source_urls(history_path: Path) -> set[str]:
    if not history_path.exists():
        return set()
    urls: set[str] = set()
    for line in history_path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        source_url = str(entry.get("source_url") or "").strip()
        if source_url:
            urls.add(source_url)
        for value in entry.get("source_urls") or []:
            value = str(value or "").strip()
            if value:
                urls.add(value)
    return urls


def load_reserve(path: Path) -> tuple[dict, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    reserve_id = str(payload.get("id") or "").strip()
    thread_path_value = str(payload.get("thread_path") or "").strip()
    thread_path = path.parent / thread_path_value if thread_path_value else None
    thread_text = str(payload.get("thread_text") or "").strip()
    if not thread_text and thread_path:
        thread_text = thread_path.read_text(encoding="utf-8").strip()
    metadata = payload.get("metadata")
    if not reserve_id or not thread_text or not isinstance(metadata, dict):
        raise ValueError(f"{path} must contain id, thread_text or thread_path, and metadata")
    payload["_thread_path"] = str(thread_path) if thread_path else ""

    spec = build_thread_spec(
        thread_text,
        metadata=metadata,
        origin="manual_codex",
        generation={
            "provider": "reserve",
            "requested_model": "prevalidated",
            "actual_model": "prevalidated",
            "prompt_contract_version": "reserve-v1",
        },
    )
    report = validate_thread_spec(spec, require_metadata=True)
    if report.errors or report.warnings:
        messages = [*report.errors, *report.warnings]
        raise ValueError(f"{path} failed strict validation: {'; '.join(messages)}")
    return payload, spec


def publish_metadata(payload: dict, spec: dict, selected_path: Path) -> dict:
    metadata = dict(spec["metadata"])
    source_urls = metadata.get("source_urls") or []
    source_url = str(source_urls[0] if source_urls else "")
    main_text = str(spec["parts"][0]["text"])
    return {
        "date": datetime.now(KST).strftime("%Y-%m-%d"),
        "provider": "reserve",
        "model": "prevalidated",
        "actual_model": "prevalidated",
        "requested_provider": "reserve",
        "requested_model": "prevalidated",
        "post_slot": "evening",
        "posts_per_day": 1,
        "experiment_group": "daily_guarantee_reserve",
        "generation_candidates": 0,
        "selected_option": 0,
        "publish_mode": "reserve",
        "reserve_id": payload["id"],
        "reserve_source_path": str(selected_path),
        "topic": metadata.get("topic", "research workflow"),
        "source_count": 1 if source_url else 0,
        "format": metadata.get("format", "research_checklist"),
        "content_axis": metadata.get("content_axis", "paper_to_workflow"),
        "format_type": metadata.get("format_type", metadata.get("format", "research_checklist")),
        "post_goal": metadata.get("post_goal", "save"),
        "final_candidate_score": 100,
        "quality_score": 100,
        "quality_decision": "publish",
        "quality_reasons": ["Prevalidated reserve ThreadSpec selected by the daily guarantee watchdog."],
        "revision_suggestions": [],
        "source_name": metadata.get("source_name", ""),
        "source_url": source_url,
        "source_type": metadata.get("source_type", "official_guideline"),
        "hook_text": next((line.strip() for line in main_text.splitlines() if line.strip()), ""),
        "main_text": main_text,
        "reply_count": 3,
        "series": metadata.get("series", ""),
        "series_part": metadata.get("series_part", ""),
        "public_theme": metadata.get("public_theme", ""),
        "topic_pillar": metadata.get("topic_pillar", metadata.get("topic", "")),
        "workflow_stage": metadata.get("workflow_stage", ""),
        "failure_mode": metadata.get("failure_mode", ""),
        "solution_pattern": metadata.get("solution_pattern", "prevalidated_reserve"),
        "bad_request": metadata.get("bad_request", ""),
        "human_signal_source": metadata.get("human_signal_source", "inferred"),
        "human_signal_type": metadata.get("human_signal_type", ""),
        "research_problem": metadata.get("research_problem", ""),
        "artifact_type": metadata.get("artifact_type", ""),
        "hook_pattern": metadata.get("hook_pattern", ""),
        "structure_pattern": metadata.get("structure_pattern", "scene_checklist_prompt_source"),
        "closer_pattern": metadata.get("closer_pattern", ""),
        "reusable_unit_type": metadata.get("reusable_unit_type", ""),
        "quote_used": False,
        "quote_id": "",
        "quote_speaker": "",
        "quote_source_url": "",
    }


def select_reserve(
    available_dir: Path,
    history_path: Path,
    output_thread: Path,
    output_spec: Path,
    output_metadata: Path,
    selection_path: Path,
) -> dict:
    used_urls = published_source_urls(history_path)
    validation_errors: list[str] = []
    for path in sorted(available_dir.glob("*.json")):
        try:
            payload, spec = load_reserve(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            validation_errors.append(str(exc))
            continue
        source_urls = {str(value).strip() for value in spec["metadata"].get("source_urls") or [] if str(value).strip()}
        if source_urls & used_urls:
            continue
        output_thread.parent.mkdir(parents=True, exist_ok=True)
        output_thread.write_text(thread_text_from_spec(spec) + "\n", encoding="utf-8")
        write_spec(output_spec, spec)
        metadata = publish_metadata(payload, spec, path)
        write_json(output_metadata, metadata)
        selection = {
            "reserve_id": payload["id"],
            "source_path": str(path),
            "thread_path": payload.get("_thread_path", ""),
            "selected_at": datetime.now(KST).isoformat(timespec="seconds"),
        }
        write_json(selection_path, selection)
        return selection

    details = f" Validation errors: {' | '.join(validation_errors)}" if validation_errors else ""
    raise RuntimeError(f"No unused, strictly valid reserve thread is available.{details}")


def consume_reserve(selection_path: Path, available_dir: Path, used_dir: Path) -> Path:
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    source = Path(str(selection.get("source_path") or ""))
    available_root = available_dir.resolve()
    source_resolved = source.resolve()
    if source_resolved.parent != available_root or not source_resolved.exists():
        raise ValueError(f"Reserve selection does not point to an available item: {source}")
    thread_path_value = str(selection.get("thread_path") or "").strip()
    thread_source = Path(thread_path_value).resolve() if thread_path_value else None
    if thread_source and (thread_source.parent != available_root or not thread_source.exists()):
        raise ValueError(f"Reserve selection has an invalid companion thread: {thread_source}")
    used_dir.mkdir(parents=True, exist_ok=True)
    destination = used_dir / source_resolved.name
    if destination.exists():
        raise ValueError(f"Reserve item was already consumed: {destination}")
    thread_destination = used_dir / thread_source.name if thread_source else None
    if thread_destination and thread_destination.exists():
        raise ValueError(f"Reserve thread was already consumed: {thread_destination}")
    shutil.move(str(source_resolved), destination)
    if thread_source:
        assert thread_destination is not None
        shutil.move(str(thread_source), thread_destination)
    return destination


def remaining_reserves(available_dir: Path, history_path: Path) -> int:
    used_urls = published_source_urls(history_path)
    remaining = 0
    for path in sorted(available_dir.glob("*.json")):
        try:
            _, spec = load_reserve(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        source_urls = {str(value).strip() for value in spec["metadata"].get("source_urls") or [] if str(value).strip()}
        if not source_urls & used_urls:
            remaining += 1
    return remaining


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage prevalidated reserve Threads chains.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    select = subparsers.add_parser("select")
    select.add_argument("--available-dir", default=str(DEFAULT_AVAILABLE_DIR))
    select.add_argument("--history-path", default="content-history.jsonl")
    select.add_argument("--output-thread", default="approved-thread-chain.txt")
    select.add_argument("--output-spec", default="approved-thread-spec.json")
    select.add_argument("--output-metadata", default="daily-editor/auto-thread-metadata.json")
    select.add_argument("--selection-path", default="daily-editor/state/reserve-selection.json")

    consume = subparsers.add_parser("consume")
    consume.add_argument("--selection-path", default="daily-editor/state/reserve-selection.json")
    consume.add_argument("--available-dir", default=str(DEFAULT_AVAILABLE_DIR))
    consume.add_argument("--used-dir", default=str(DEFAULT_USED_DIR))

    remaining = subparsers.add_parser("remaining")
    remaining.add_argument("--available-dir", default=str(DEFAULT_AVAILABLE_DIR))
    remaining.add_argument("--history-path", default="content-history.jsonl")

    args = parser.parse_args()
    try:
        if args.command == "select":
            selection = select_reserve(
                available_dir=Path(args.available_dir),
                history_path=Path(args.history_path),
                output_thread=Path(args.output_thread),
                output_spec=Path(args.output_spec),
                output_metadata=Path(args.output_metadata),
                selection_path=Path(args.selection_path),
            )
            print(json.dumps(selection, ensure_ascii=False))
        elif args.command == "consume":
            destination = consume_reserve(
                selection_path=Path(args.selection_path),
                available_dir=Path(args.available_dir),
                used_dir=Path(args.used_dir),
            )
            print(json.dumps({"consumed_path": str(destination)}, ensure_ascii=False))
        else:
            count = remaining_reserves(Path(args.available_dir), Path(args.history_path))
            print(json.dumps({"remaining": count}, ensure_ascii=False))
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
