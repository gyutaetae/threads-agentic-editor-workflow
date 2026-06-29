import argparse
import json
import re
import sys
from pathlib import Path


MAX_CHARS = 500
MIN_PARTS = 1
MAX_PARTS = 4
CHECKLIST_RE = re.compile(r"(?m)^\s*(\d+)\.\s+")
URL_RE = re.compile(r"https?://\S+")
SECTION_LABEL_RE = re.compile(r"(?im)^\s*(?:main|reply\s*\d+|reply\s*n|답글\s*\d+)\s*:\s*")
SEPARATOR_RE = re.compile(r"(?m)^\s*---\s*$")
QUOTE_LINE_RE = re.compile(r"(?m)^\s*[\"“][^\"”]+[\"”]\s*$")
BRACKET_HEADING_RE = re.compile(r"^\[[^\]\n]{4,80}\]\s*(?:\n|$)")
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
    return re.sub(r"\n{3,}", "\n\n", text)


def read_parts(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8").strip()
    return [normalize_part(part) for part in SEPARATOR_RE.split(raw) if part.strip()]


def has_explanation_for(parts: list[str], number: str) -> bool:
    expected_prefix = f"{number}."
    return any(part.lstrip().startswith(expected_prefix) and len(part) >= 120 for part in parts[1:])


def good_request_lines(main: str) -> list[str]:
    if "좋은 요청:" not in main:
        return []
    good_request = main.split("좋은 요청:", 1)[1]
    return QUOTE_LINE_RE.findall(good_request)


def has_reply_heading(part: str) -> bool:
    return bool(BRACKET_HEADING_RE.match(part.strip()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check an approved Threads chain before publishing.")
    parser.add_argument("--thread-path", default="approved-thread-chain.txt")
    parser.add_argument("--quote-catalog-path", default="data/verified-quotes.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    path = Path(args.thread_path)
    parts = read_parts(path)
    errors = []
    warnings = []

    if not parts:
        errors.append("No thread parts found.")
    elif len(parts) < MIN_PARTS or len(parts) > MAX_PARTS:
        errors.append(f"Thread has {len(parts)} parts; expected {MIN_PARTS}-{MAX_PARTS} parts.")

    for index, part in enumerate(parts, start=1):
        if SECTION_LABEL_RE.match(part):
            errors.append(f"Part {index} starts with a drafting label such as Main: or Reply n:.")
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

    quoted_good_lines = good_request_lines(main)
    if "좋은 요청:" in main:
        numbered_good_lines = [
            line for line in quoted_good_lines if re.match(r'^\s*["“]\s*\d+\.', line)
        ]
        if numbered_good_lines:
            errors.append("Good-request lines should not include 1./2./3./4. numbering inside the quotes.")

    checklist_numbers = CHECKLIST_RE.findall(main)
    if len(checklist_numbers) >= 3:
        for number in checklist_numbers:
            if not has_explanation_for(parts, number):
                warnings.append(f"Checklist item {number} has no dedicated explanation reply.")

    if "repo" in joined.lower() and not URL_RE.search(joined):
        warnings.append("Repo-based post has no source links.")

    if "왜 좋은 요청일까요?" in joined:
        errors.append("Use practical framing, not '왜 좋은 요청일까요?'.")

    if URL_RE.search(joined) and "- 볼 부분:" not in joined and "인용 원문:" not in joined:
        errors.append("Source links must include '- 볼 부분:' or a quote source labeled '인용 원문:'.")
    if "notebooklm.google" in joined.lower():
        errors.append("Reference reply must link to an actual example, not the NotebookLM product homepage.")

    reusable_markers = [
        "예시 프롬프트",
        "바로 써볼 프롬프트",
        "저장해둘 프롬프트",
        "저장해두고 적용해볼 프롬프트",
        "실전에서 사용할 프롬프트",
        "오늘 적용할 문장",
        "AI agent에게 이렇게 시켜보세요",
        "논문 읽을 때 붙여 넣을 문장",
        "다음 요약 전에 써볼 질문",
        "체크리스트",
        "claim",
        "evidence",
        "citation",
        "limitation",
    ]
    if not any(marker in joined for marker in reusable_markers):
        errors.append("Chain needs a reusable prompt, checklist, agent instruction, or verification work unit.")

    catalog_path = Path(args.quote_catalog_path)
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for quote in catalog:
            speaker_names = [quote.get("speaker", ""), quote.get("speaker_ko", "")]
            if any(name and name in joined for name in speaker_names):
                if quote.get("quote_ko") not in joined:
                    errors.append(f"Quote attributed to {quote.get('speaker')} must use the cataloged Korean text.")
                if quote.get("source_url") not in joined:
                    errors.append(f"Quote attributed to {quote.get('speaker')} must include its verified source URL.")
                if "인용 원문:" not in joined:
                    errors.append("A famous-person quote must label its primary source with '인용 원문:'.")

    if not any(marker in main for marker in ["흐려", "애매", "흔들", "놓치", "실패", "위험", "잘못", "검증", "근거"]):
        warnings.append("Main hook may be flat; consider a sharper diagnostic consequence.")

    if joined.count("[핵심 한 줄]") >= 2:
        warnings.append("Repeated generic '[핵심 한 줄]' labels make replies feel templated.")

    has_source_application = False
    for part in parts:
        if URL_RE.search(part) and "- 볼 부분:" in part:
            url_match = URL_RE.search(part)
            if not url_match:
                continue
            before_url = part[: url_match.start()].strip()
            after_url = part[url_match.end() :].strip()
            has_source_application = (
                len(before_url) >= 20 and len(after_url) >= 40
            ) or ("[참고 논문]" in part and "[나의 견해]" in part)

    if URL_RE.search(joined) and not has_source_application:
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
