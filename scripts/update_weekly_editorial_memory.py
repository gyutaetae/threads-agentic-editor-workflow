import argparse
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


ENGAGEMENT_KEYS = ["audience_replies", "reposts", "quotes", "saves", "profile_visits", "follows_gained"]


def int_field(row: dict, key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def parse_date(value: str) -> datetime | None:
    for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"]:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def engagement(row: dict) -> int:
    total = sum(int_field(row, key) for key in ENGAGEMENT_KEYS)
    if total == 0:
        total = int_field(row, "likes")
    return total


def bucket_totals(rows: list[dict], key: str) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for row in rows:
        value = row.get(key) or "unknown"
        totals[value] += engagement(row)
    return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))


def top_rows(rows: list[dict], limit: int = 5) -> list[dict]:
    return sorted(rows, key=engagement, reverse=True)[:limit]


def filter_recent(rows: list[dict], days: int) -> list[dict]:
    now = datetime.now().astimezone()
    cutoff = now - timedelta(days=days)
    recent = []
    for row in rows:
        parsed = parse_date(row.get("posted_at") or row.get("date") or "")
        if parsed is None:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.astimezone()
        if parsed >= cutoff:
            recent.append(row)
    return recent


def bullets_from_totals(totals: dict[str, int], empty: str) -> list[str]:
    if not totals:
        return [f"- {empty}"]
    return [f"- {name}: {score}" for name, score in list(totals.items())[:5]]


def render_memory(rows: list[dict], days: int) -> str:
    recent = filter_recent(rows, days)
    analyzed = recent or rows[-25:]
    enough = len([row for row in analyzed if "metrics collected:" in (row.get("notes") or "")]) >= 20

    lines = [
        "# Weekly Editorial Memory",
        "",
        f"Updated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Window: last {days} days; analyzed posts: {len(analyzed)}",
        "",
        "Use this file as weak guidance until at least 20 posts have 24h/72h metrics.",
        "",
        "## Signal Strength",
        "",
        f"- Current signal: {'usable' if enough else 'early/weak'}",
        f"- Posts with collected metrics: {sum(1 for row in analyzed if 'metrics collected:' in (row.get('notes') or ''))}",
        "",
        "## Winning Slots",
        "",
        *bullets_from_totals(bucket_totals(analyzed, "post_slot"), "No slot data yet."),
        "",
        "## Winning Experiments",
        "",
        *bullets_from_totals(bucket_totals(analyzed, "experiment_group"), "No experiment data yet."),
        "",
        "## Winning Formats",
        "",
        *bullets_from_totals(bucket_totals(analyzed, "format_type"), "No format data yet."),
        "",
        "## Winning Content Axes",
        "",
        *bullets_from_totals(bucket_totals(analyzed, "content_axis"), "No content-axis data yet."),
        "",
        "## Top Posts",
        "",
    ]

    for row in top_rows(analyzed):
        hook = row.get("hook") or ""
        topic = row.get("topic") or ""
        slot = row.get("post_slot") or "unknown"
        fmt = row.get("format_type") or row.get("format") or "unknown"
        lines.append(f"- score {engagement(row)} | {slot} | {fmt} | {topic} | {hook}")

    if not top_rows(analyzed):
        lines.append("- No posts available.")

    lines.extend(
        [
            "",
            "## Editorial Decisions",
            "",
            "- Keep personal proof to 1-2 lines, then show a reusable prompt/checklist.",
            "- Rotate hook surfaces so the account does not feel automated.",
            "- Prefer useful replies, reposts, quotes, saves, profile visits, and follows over views alone.",
            "- If the same hook pattern wins repeatedly, reuse the lesson but change the surface.",
            "",
            "## Next Prompt Guidance",
            "",
            "- Use quote/idea hooks only when they naturally support the workflow.",
            "- If recent posts overuse '만약...', start from a paper/dev diary, failed request, or direct claim.",
            "- If metrics are weak, choose save-worthy practical formats over generic AI news.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Update weekly Threads editorial memory from metrics CSV.")
    parser.add_argument("--metrics-path", default="threads-post-metrics.csv")
    parser.add_argument("--output-path", default="docs/weekly-editorial-memory.md")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()

    rows = read_rows(Path(args.metrics_path))
    output = render_memory(rows, args.days)
    Path(args.output_path).write_text(output, encoding="utf-8")
    print(f"Wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
