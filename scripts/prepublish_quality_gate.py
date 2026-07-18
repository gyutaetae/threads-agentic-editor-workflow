import argparse
import sys
from pathlib import Path

try:
    from scripts.thread_spec import load_spec, print_report, render_parts, split_thread_text, thread_text_from_spec, validate_thread_spec, validate_thread_text
except ModuleNotFoundError:
    from thread_spec import load_spec, print_report, render_parts, split_thread_text, thread_text_from_spec, validate_thread_spec, validate_thread_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a ThreadSpec or legacy chain before publishing.")
    parser.add_argument("--thread-path", default="approved-thread-chain.txt")
    parser.add_argument("--spec-path")
    parser.add_argument("--quote-catalog-path", default="data/verified-quotes.json")
    parser.add_argument("--require-metadata", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    quote_path = Path(args.quote_catalog_path)
    if args.spec_path:
        spec = load_spec(Path(args.spec_path))
        report = validate_thread_spec(
            spec,
            quote_catalog_path=quote_path,
            require_metadata=args.require_metadata,
        )
        thread_path = Path(args.thread_path)
        if thread_path.exists():
            rendered_spec = thread_text_from_spec(spec)
            rendered_text = render_parts(split_thread_text(thread_path.read_text(encoding="utf-8")))
            if rendered_spec != rendered_text:
                report.errors.append("ThreadSpec parts do not match the publishable thread text.")
        checked = args.spec_path
    else:
        thread_text = Path(args.thread_path).read_text(encoding="utf-8")
        report = validate_thread_text(thread_text, quote_catalog_path=quote_path)
        checked = args.thread_path

    print(f"Checked {checked}")
    print_report(report)
    if report.errors or (args.strict and report.warnings):
        return 1
    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
