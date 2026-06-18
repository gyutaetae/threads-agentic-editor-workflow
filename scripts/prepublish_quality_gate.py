import argparse
import re
import sys
from pathlib import Path


MAX_CHARS = 500
MAX_PARTS = 4
CHECKLIST_RE = re.compile(r"(?m)^\s*(\d+)\.\s+")
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
    elif len(parts) != MAX_PARTS:
        errors.append(f"Thread has {len(parts)} parts; expected exactly {MAX_PARTS} (main + 3 replies).")

    for index, part in enumerate(parts, start=1):
        if len(part) > MAX_CHARS:
            errors.append(f"Part {index} is {len(part)} chars; limit is {MAX_CHARS}.")
        if len(part) < 40:
            warnings.append(f"Part {index} is very short; check whether it adds value.")

    main = parts[0] if parts else ""
    joined = "\n".join(parts)

    for forbidden in FORBIDDEN_TEXT:
        if forbidden in joined:
            errors.append(f"Thread contains forbidden generated label: {forbidden}")

    if "```" in joined or '{"role"' in joined or '"tools"' in joined:
        errors.append("Example prompt should be natural quoted Korean text, not a code block or JSON object.")

    if main and ("나쁜 요청:" not in main or "좋은 요청:" not in main):
        errors.append("Main post must include both '나쁜 요청:' and '좋은 요청:' sections.")

    if "좋은 요청:" in main:
        good_request = main.split("좋은 요청:", 1)[1]
        quoted_good_lines = QUOTE_LINE_RE.findall(good_request)
        if len(quoted_good_lines) < 4:
            errors.append("Main post must include at least four quoted good-request examples.")

    checklist_numbers = CHECKLIST_RE.findall(main)
    if len(checklist_numbers) >= 3:
        for number in checklist_numbers:
            if not has_explanation_for(parts, number):
                warnings.append(f"Checklist item {number} has no dedicated explanation reply.")

    if "repo" in joined.lower() and not URL_RE.search(joined):
        warnings.append("Repo-based post has no source links.")

    if len(parts) >= 3 and not parts[2].startswith("예시 프롬프트:"):
        errors.append("Part 3 must start with '예시 프롬프트:'.")

    if len(parts) >= 4:
        if not parts[3].startswith("참고해서 볼 만한 것들:"):
            errors.append("Part 4 must start with '참고해서 볼 만한 것들:'.")
        if not URL_RE.search(parts[3]):
            errors.append("Reference reply must include at least one full clickable URL starting with https://.")

    if not any(marker in main for marker in ["흐려", "애매", "흔들", "놓치", "실패", "위험", "잘못", "검증", "근거"]):
        warnings.append("Main hook may be flat; consider a sharper diagnostic consequence.")

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
