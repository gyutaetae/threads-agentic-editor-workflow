import argparse
import re
import sys
from pathlib import Path


MAX_CHARS = 500
MAX_PARTS = 4
CHECKLIST_RE = re.compile(r"(?m)^\s*(\d+)\.\s+")
URL_RE = re.compile(r"https?://\S+")


def read_parts(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8").strip()
    return [part.strip() for part in raw.split("\n---\n") if part.strip()]


def has_explanation_for(parts: list[str], number: str) -> bool:
    expected_prefix = f"{number}."
    return any(part.lstrip().startswith(expected_prefix) and len(part) >= 120 for part in parts[1:])


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an approved Threads chain before publishing.")
    parser.add_argument("--thread-path", default="approved-thread-chain.txt")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    path = Path(args.thread_path)
    parts = read_parts(path)
    errors = []
    warnings = []

    if not parts:
        errors.append("No thread parts found.")
    elif len(parts) > MAX_PARTS:
        errors.append(f"Thread has {len(parts)} parts; limit is {MAX_PARTS} (main + up to 3 replies).")

    for index, part in enumerate(parts, start=1):
        if len(part) > MAX_CHARS:
            errors.append(f"Part {index} is {len(part)} chars; limit is {MAX_CHARS}.")
        if len(part) < 40:
            warnings.append(f"Part {index} is very short; check whether it adds value.")

    main = parts[0] if parts else ""
    checklist_numbers = CHECKLIST_RE.findall(main)
    if len(checklist_numbers) >= 3:
        for number in checklist_numbers:
            if not has_explanation_for(parts, number):
                warnings.append(f"Checklist item {number} has no dedicated explanation reply.")
    else:
        warnings.append("Main post does not contain a clear numbered checklist.")

    joined = "\n".join(parts)
    if "repo" in joined.lower() and not URL_RE.search(joined):
        warnings.append("Repo-based post has no source links.")

    if not any(marker in main for marker in ["놓치는", "놓칩니다", "먼저", "실수", "차이", "보다"]):
        warnings.append("Main hook may be flat; consider a sharper reversal or diagnostic claim.")

    if "해석" not in joined and "예시" not in joined:
        warnings.append("Chain may not clearly separate source facts from interpretation.")

    print(f"Checked {path} ({len(parts)} parts)")
    for index, part in enumerate(parts, start=1):
        print(f"- Part {index}: {len(part)} chars")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")
        return 1

    if args.strict and warnings:
        return 1

    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
