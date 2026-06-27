import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path

from threads_auto_upload import (
    env,
    get_thread_insights,
    parse_insights,
    update_metrics_row,
)


WINDOWS = {
    "24h": timedelta(hours=24),
    "72h": timedelta(hours=72),
}


def parse_posted_at(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def shorten_note(value: object, max_chars: int = 180) -> str:
    text = " ".join(str(value).split())
    return text[:max_chars]


def due_windows(row: dict, now: datetime) -> list[str]:
    posted_at = parse_posted_at(row.get("posted_at", ""))
    if posted_at is None:
        return []
    if posted_at.tzinfo is None:
        posted_at = posted_at.astimezone()

    notes = row.get("notes", "")
    age = now - posted_at
    due = []
    for label, minimum_age in WINDOWS.items():
        if (
            age >= minimum_age
            and f"metrics collected: {label}" not in notes
            and f"metrics skipped: {label}" not in notes
        ):
            due.append(label)
    return due


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect due 24h/72h Threads metrics for posted rows.")
    parser.add_argument("--metrics-path", default="threads-post-metrics.csv")
    parser.add_argument("--metrics", default="views,likes,replies,reposts,quotes")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--access-token", default=None)
    args = parser.parse_args()

    metrics_path = Path(args.metrics_path)
    rows = read_rows(metrics_path)
    if not rows:
        print(f"No rows found in {metrics_path}")
        return 0

    access_token = env("THREADS_ACCESS_TOKEN", args.access_token)
    metric_names = [metric.strip() for metric in args.metrics.split(",") if metric.strip()]
    now = datetime.now().astimezone()
    collected = 0
    skipped = 0

    for row in rows:
        post_id = row.get("post_id", "")
        if not post_id:
            continue
        for label in due_windows(row, now):
            try:
                payload = get_thread_insights(access_token, post_id, metric_names)
            except SystemExit as exc:
                note = f"metrics skipped: {label}: {shorten_note(exc)}"
                update_metrics_row(str(metrics_path), post_id, {}, note)
                skipped += 1
                print(f"Skipped {label} metrics for {post_id}: {shorten_note(exc)}")
                continue
            metrics = parse_insights(payload)
            note = f"metrics collected: {label}"
            if update_metrics_row(str(metrics_path), post_id, metrics, note):
                collected += 1
                print(f"Collected {label} metrics for {post_id}: {metrics}")
            if collected >= args.limit:
                return 0

    if collected == 0:
        if skipped:
            print(f"No metrics collected; skipped {skipped} unavailable metric window(s).")
        else:
            print("No due metrics windows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
