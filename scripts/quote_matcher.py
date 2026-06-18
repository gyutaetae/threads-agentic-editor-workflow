import argparse
import html
import json
import re
from pathlib import Path

import requests


DEFAULT_CATALOG_PATH = "data/verified-quotes.json"
DEFAULT_HISTORY_PATH = "content-history.jsonl"
DEFAULT_THRESHOLD = 8
RECENT_QUOTE_WINDOW = 3
REQUIRED_FIELDS = {
    "id",
    "speaker",
    "speaker_ko",
    "quote_original",
    "quote_ko",
    "source_url",
    "source_type",
    "verified",
    "actionability",
    "authority",
    "topic_terms",
}


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog(path: Path) -> list[dict]:
    payload = read_json(path)
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"Quote catalog must be a non-empty JSON list: {path}")

    seen_ids = set()
    for quote in payload:
        missing = REQUIRED_FIELDS.difference(quote)
        if missing:
            raise ValueError(f"Quote entry is missing fields {sorted(missing)}: {quote}")
        if quote["id"] in seen_ids:
            raise ValueError(f"Duplicate quote id: {quote['id']}")
        if quote.get("verified") is not True:
            raise ValueError(f"Unverified quote cannot enter the catalog: {quote['id']}")
        if not str(quote["source_url"]).startswith("https://"):
            raise ValueError(f"Quote source must use https://: {quote['id']}")
        if not isinstance(quote["topic_terms"], list) or not quote["topic_terms"]:
            raise ValueError(f"Quote must have topic terms: {quote['id']}")
        seen_ids.add(quote["id"])
    return payload


def load_recent_history(path: Path, limit: int = RECENT_QUOTE_WINDOW) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries[-limit:]


def quote_used_recently(history_path: Path, window: int = RECENT_QUOTE_WINDOW) -> bool:
    return any(entry.get("quote_used") is True for entry in load_recent_history(history_path, window))


def candidate_text(candidate: dict) -> str:
    values = [
        candidate.get("name"),
        candidate.get("title"),
        candidate.get("description"),
        candidate.get("readme_summary"),
        candidate.get("category"),
        candidate.get("our_angle"),
        candidate.get("draft_angles", {}).get("A_broad"),
        candidate.get("draft_angles", {}).get("B_deep"),
    ]
    values.extend(candidate.get("topics") or [])
    return " ".join(str(value) for value in values if value).lower()


def term_matches(text: str, term: str) -> bool:
    normalized = term.strip().lower()
    if not normalized:
        return False
    if re.search(r"[가-힣]", normalized) or " " in normalized:
        return normalized in text
    return re.search(rf"\b{re.escape(normalized)}\b", text) is not None


def score_quote(candidate: dict, quote: dict) -> dict:
    text = candidate_text(candidate)
    matched_terms = [term for term in quote["topic_terms"] if term_matches(text, term)]
    relevance = min(5, len(matched_terms) * 2)
    awkwardness_penalty = -5 if not matched_terms else (-2 if relevance < 3 else 0)
    total = relevance + int(quote["actionability"]) + int(quote["authority"]) + awkwardness_penalty
    return {
        "total": total,
        "relevance": relevance,
        "actionability": int(quote["actionability"]),
        "authority": int(quote["authority"]),
        "awkwardness_penalty": awkwardness_penalty,
        "matched_terms": matched_terms,
    }


def fetch_source_text(url: str, timeout: int = 15) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "threads-agentic-editor/quote-verifier"},
            timeout=timeout,
        )
        response.raise_for_status()
        without_tags = re.sub(r"<[^>]+>", " ", response.text)
        return re.sub(r"\s+", " ", html.unescape(without_tags))
    except requests.RequestException:
        return ""


def attach_quote_suggestions(
    candidates: list[dict],
    catalog: list[dict],
    history_path: Path,
    threshold: int = DEFAULT_THRESHOLD,
    verify_urls: bool = True,
) -> list[dict]:
    if quote_used_recently(history_path):
        for candidate in candidates:
            candidate.pop("quote_suggestion", None)
        return candidates

    source_text_by_url = {}
    for candidate in candidates:
        ranked = []
        for quote in catalog:
            score = score_quote(candidate, quote)
            if score["total"] < threshold:
                continue
            url = quote["source_url"]
            if verify_urls:
                if url not in source_text_by_url:
                    source_text_by_url[url] = fetch_source_text(url)
                if quote["quote_original"] not in source_text_by_url[url]:
                    continue
            ranked.append((score["total"], quote["id"], quote, score))

        if not ranked:
            candidate.pop("quote_suggestion", None)
            continue

        _, _, quote, score = max(ranked, key=lambda item: (item[0], item[1]))
        candidate["quote_suggestion"] = {
            "id": quote["id"],
            "speaker": quote["speaker"],
            "speaker_ko": quote["speaker_ko"],
            "quote_original": quote["quote_original"],
            "quote_ko": quote["quote_ko"],
            "source_url": quote["source_url"],
            "source_type": quote["source_type"],
            "score": score,
        }
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach optional verified quote suggestions to content candidates.")
    parser.add_argument("--candidates-path", required=True)
    parser.add_argument("--output-path")
    parser.add_argument("--catalog-path", default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--history-path", default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    parser.add_argument("--skip-url-verification", action="store_true")
    args = parser.parse_args()

    candidates_path = Path(args.candidates_path)
    candidates = read_json(candidates_path)
    if not isinstance(candidates, list):
        raise SystemExit("Candidates file must contain a JSON list.")

    catalog = load_catalog(Path(args.catalog_path))
    attach_quote_suggestions(
        candidates,
        catalog,
        Path(args.history_path),
        threshold=args.threshold,
        verify_urls=not args.skip_url_verification,
    )

    output_path = Path(args.output_path or args.candidates_path)
    output_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    matched = sum(1 for item in candidates if item.get("quote_suggestion"))
    print(f"Wrote {output_path} with {matched} optional quote suggestion(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
