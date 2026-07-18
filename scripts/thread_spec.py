import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SPEC_VERSION = "1.0"
PROMPT_CONTRACT_VERSION = "thread-spec-v1"
PART_ROLES = ("hook", "diagnosis", "action", "source")
MAX_CHARS = 500
MIN_PART_CHARS = 40

SEPARATOR_RE = re.compile(r"(?m)^\s*---\s*$")
SECTION_LABEL_RE = re.compile(r"(?im)^\s*(?:main|reply\s*\d+|reply\s*n|답글\s*\d+)\s*:\s*")
URL_RE = re.compile(r"https?://\S+")
BRACKET_HEADING_RE = re.compile(r"^\[[^\]\n]{2,80}\]\s*(?:\n|$)")
QUOTE_LINE_RE = re.compile(r"(?m)^\s*[\"“][^\"”]+[\"”]\s*$")
CHECK_ITEM_RE = re.compile(r"^\s*(?:\d+[.)]|[-*•—])\s+\S+")

HYPE_WORDS = ["무조건", "혁명", "논문 끝", "개발자 끝", "역대급", "미친 생산성", "뒤처집니다", "끝입니다"]
FORBIDDEN_TEXT = [
    "[한 줄 원칙",
    "한 줄 원칙:",
    "Reply 1:",
    "Reply 2:",
    "Reply 3:",
    "[초안 작성 모드]",
    "초안 작성 모드",
]
PRACTICAL_MARKERS = [
    "예시 프롬프트",
    "바로 써볼 프롬프트",
    "저장해둘 프롬프트",
    "저장해두고 적용해볼 프롬프트",
    "오늘 적용할 문장",
    "AI agent에게 이렇게 시켜보세요",
    "논문 읽을 때 붙여 넣을 문장",
    "다음 요약 전에 써볼 질문",
    "체크리스트",
    "프로토콜",
    "매트릭스",
    "표로",
    "규칙",
    "claim",
    "evidence",
    "citation",
    "limitation",
]
INTERPRETATION_MARKERS = [
    "[나의 견해]",
    "우리 해석",
    "내가 적용하려는 해석",
    "account interpretation",
]
HOOK_CONSEQUENCE_MARKERS = ["흐려", "애매", "흔들", "놓치", "실패", "위험", "잘못", "검증", "근거", "설명 못", "확인해야", "재현"]
REQUIRED_METADATA_FIELDS = [
    "topic",
    "format",
    "workflow_stage",
    "failure_mode",
    "artifact_type",
    "reusable_unit_type",
    "hook_pattern",
    "source_name",
    "source_urls",
]


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    part_lengths: list[int] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "part_lengths": self.part_lengths,
        }


def normalize_part(part: str) -> str:
    text = "\n".join(line.rstrip() for line in str(part).strip().splitlines()).strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def split_thread_text(raw: str) -> list[str]:
    return [normalize_part(part) for part in SEPARATOR_RE.split(str(raw).strip()) if part.strip()]


def render_parts(parts: list[str]) -> str:
    return "\n---\n".join(normalize_part(part) for part in parts if str(part).strip())


def build_thread_spec(
    thread_text: str,
    metadata: dict[str, Any] | None = None,
    origin: str = "legacy_import",
    generation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    parts = split_thread_text(thread_text)
    spec: dict[str, Any] = {
        "spec_version": SPEC_VERSION,
        "origin": origin,
        "parts": [
            {"role": PART_ROLES[index] if index < len(PART_ROLES) else f"extra_{index + 1}", "text": text}
            for index, text in enumerate(parts)
        ],
        "metadata": metadata or {},
    }
    if generation:
        spec["generation"] = generation
    return spec


def thread_text_from_spec(spec: dict[str, Any]) -> str:
    return render_parts([str(part.get("text", "")) for part in spec.get("parts", [])])


def _diagnosis_item_count(text: str) -> int:
    lines = [line.strip() for line in text.splitlines()[1:] if line.strip()]
    explicit = [line for line in lines if CHECK_ITEM_RE.match(line)]
    if explicit:
        return len(explicit)
    return len([line for line in lines if len(line) >= 8])


def _validate_quote_catalog(joined: str, catalog_path: Path, report: ValidationReport) -> None:
    if not catalog_path.exists():
        return
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for quote in catalog:
        names = [quote.get("speaker", ""), quote.get("speaker_ko", "")]
        if not any(name and name in joined for name in names):
            continue
        if quote.get("quote_ko") not in joined:
            report.errors.append(f"Quote attributed to {quote.get('speaker')} must use the cataloged Korean text.")
        if quote.get("source_url") not in joined:
            report.errors.append(f"Quote attributed to {quote.get('speaker')} must include its verified source URL.")
        if "인용 원문:" not in joined:
            report.errors.append("A famous-person quote must label its primary source with '인용 원문:'.")


def validate_thread_spec(
    spec: dict[str, Any],
    quote_catalog_path: Path | None = None,
    require_metadata: bool = False,
) -> ValidationReport:
    report = ValidationReport()
    if spec.get("spec_version") != SPEC_VERSION:
        report.errors.append(f"spec_version must be {SPEC_VERSION}.")

    raw_parts = spec.get("parts")
    if not isinstance(raw_parts, list):
        report.errors.append("parts must be an array.")
        return report
    if len(raw_parts) != len(PART_ROLES):
        report.errors.append("Thread must have exactly 4 parts: hook, diagnosis, action, source.")

    texts: list[str] = []
    for index, part in enumerate(raw_parts):
        if not isinstance(part, dict):
            report.errors.append(f"Part {index + 1} must be an object.")
            continue
        expected_role = PART_ROLES[index] if index < len(PART_ROLES) else None
        role = part.get("role")
        if expected_role and role != expected_role:
            report.errors.append(f"Part {index + 1} role must be '{expected_role}', not '{role}'.")
        text = normalize_part(str(part.get("text", "")))
        texts.append(text)
        report.part_lengths.append(len(text))
        if len(text) > MAX_CHARS:
            report.errors.append(f"Part {index + 1} is {len(text)} chars; limit is {MAX_CHARS}.")
        if len(text) < MIN_PART_CHARS:
            report.warnings.append(f"Part {index + 1} is very short; check whether it adds value.")
        if SECTION_LABEL_RE.match(text):
            report.errors.append(f"Part {index + 1} starts with a drafting label such as Main: or Reply n:.")

    if len(texts) != len(PART_ROLES):
        return report

    hook, diagnosis, action, source = texts
    joined = "\n".join(texts)

    if BRACKET_HEADING_RE.match(hook):
        report.errors.append("Part 1 must start with the problem hook, not a bracket heading.")
    for index, text in enumerate(texts[1:], start=2):
        if not BRACKET_HEADING_RE.match(text):
            report.errors.append(f"Part {index} must start with a role-specific Korean bracket heading.")

    for index, text in enumerate(texts[:3], start=1):
        if URL_RE.search(text):
            report.errors.append(f"Part {index} contains a source URL; move all source links to Part 4.")

    if _diagnosis_item_count(diagnosis) < 3:
        report.warnings.append("Part 2 should contain at least 3 concrete diagnosis checks or criteria.")
    if not any(marker in action for marker in PRACTICAL_MARKERS) and not QUOTE_LINE_RE.search(action):
        report.errors.append("Part 3 needs a copyable prompt, checklist, protocol, matrix, or rule.")
    if not URL_RE.search(source):
        report.errors.append("Part 4 must include at least one full source URL.")
    if "- 볼 부분:" not in source and "인용 원문:" not in source:
        report.errors.append("Part 4 must explain the source with '- 볼 부분:' or '인용 원문:'.")
    if not any(marker in source for marker in INTERPRETATION_MARKERS):
        report.errors.append("Part 4 must separate source facts from account interpretation, normally with '[나의 견해]'.")

    for forbidden in FORBIDDEN_TEXT:
        if forbidden in joined:
            report.errors.append(f"Thread contains forbidden generated label: {forbidden}")
    if "```" in joined or '{"role"' in joined or '"tools"' in joined:
        report.errors.append("Publishable text must not contain code fences or JSON-style prompts.")
    if any(word in joined for word in HYPE_WORDS):
        report.errors.append("Thread contains banned hype language.")
    if "왜 좋은 요청일까요?" in joined:
        report.errors.append("Use practical framing, not '왜 좋은 요청일까요?'.")
    if "notebooklm.google" in joined.lower():
        report.errors.append("Reference reply must link to an actual example, not the NotebookLM product homepage.")

    if "좋은 요청:" in hook:
        quoted_lines = QUOTE_LINE_RE.findall(hook.split("좋은 요청:", 1)[1])
        if any(re.match(r'^\s*["“]\s*\d+\.', line) for line in quoted_lines):
            report.errors.append("Good-request lines should not include 1./2./3./4. numbering inside the quotes.")

    if not any(marker in hook for marker in HOOK_CONSEQUENCE_MARKERS):
        report.warnings.append("Part 1 may be flat; name a concrete research-work consequence.")
    if joined.count("[핵심 한 줄]") >= 2:
        report.warnings.append("Repeated generic '[핵심 한 줄]' labels make the chain feel templated.")

    if require_metadata:
        metadata = spec.get("metadata")
        if not isinstance(metadata, dict):
            report.errors.append("metadata must be an object.")
        else:
            missing = [field for field in REQUIRED_METADATA_FIELDS if field not in metadata]
            if missing:
                report.errors.append(f"ThreadSpec metadata is missing required fields: {', '.join(missing)}")
            empty = [
                field
                for field in REQUIRED_METADATA_FIELDS
                if field in metadata and metadata.get(field) in (None, "", [])
            ]
            if empty:
                report.warnings.append(f"ThreadSpec metadata has empty fingerprint fields: {', '.join(empty)}")

    if quote_catalog_path:
        _validate_quote_catalog(joined, quote_catalog_path, report)
    return report


def validate_thread_text(
    thread_text: str,
    quote_catalog_path: Path | None = None,
    metadata: dict[str, Any] | None = None,
    require_metadata: bool = False,
    origin: str = "legacy_import",
) -> ValidationReport:
    spec = build_thread_spec(thread_text, metadata=metadata, origin=origin)
    return validate_thread_spec(spec, quote_catalog_path=quote_catalog_path, require_metadata=require_metadata)


def raise_for_report(report: ValidationReport, strict: bool = False) -> None:
    failures = list(report.errors)
    if strict:
        failures.extend(report.warnings)
    if failures:
        raise SystemExit("\n".join(failures))


def load_spec(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_spec(path: Path, spec: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_report(report: ValidationReport) -> None:
    print(f"Checked ThreadSpec ({len(report.part_lengths)} parts)")
    for index, length in enumerate(report.part_lengths, start=1):
        print(f"- Part {index}: {length} chars")
    if report.warnings:
        print("\nWarnings:")
        for warning in report.warnings:
            print(f"- {warning}")
    if report.errors:
        print("\nErrors:")
        for error in report.errors:
            print(f"- {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build, validate, or render the canonical ThreadSpec.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--thread-path", default="approved-thread-chain.txt")
    build.add_argument("--output-path", default="approved-thread-spec.json")
    build.add_argument("--metadata-path")
    build.add_argument("--origin", default="legacy_import")

    validate = subparsers.add_parser("validate")
    validate.add_argument("--spec-path")
    validate.add_argument("--thread-path", default="approved-thread-chain.txt")
    validate.add_argument("--quote-catalog-path", default="data/verified-quotes.json")
    validate.add_argument("--require-metadata", action="store_true")
    validate.add_argument("--strict", action="store_true")

    render = subparsers.add_parser("render")
    render.add_argument("--spec-path", default="approved-thread-spec.json")
    render.add_argument("--output-path", default="approved-thread-chain.txt")

    args = parser.parse_args()
    if args.command == "build":
        metadata = {}
        if args.metadata_path:
            metadata = json.loads(Path(args.metadata_path).read_text(encoding="utf-8"))
        thread_text = Path(args.thread_path).read_text(encoding="utf-8")
        spec = build_thread_spec(thread_text, metadata=metadata, origin=args.origin)
        write_spec(Path(args.output_path), spec)
        print(f"Wrote {args.output_path}")
        return 0

    if args.command == "validate":
        quote_path = Path(args.quote_catalog_path)
        if args.spec_path:
            report = validate_thread_spec(
                load_spec(Path(args.spec_path)),
                quote_catalog_path=quote_path,
                require_metadata=args.require_metadata,
            )
        else:
            thread_text = Path(args.thread_path).read_text(encoding="utf-8")
            report = validate_thread_text(thread_text, quote_catalog_path=quote_path)
        print_report(report)
        if report.errors or (args.strict and report.warnings):
            return 1
        print("\nQuality gate passed.")
        return 0

    spec = load_spec(Path(args.spec_path))
    Path(args.output_path).write_text(thread_text_from_spec(spec) + "\n", encoding="utf-8")
    print(f"Wrote {args.output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
