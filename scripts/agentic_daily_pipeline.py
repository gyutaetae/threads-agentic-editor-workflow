import argparse
import base64
import re
import textwrap
import xml.etree.ElementTree as ET
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests


GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

OFFICIAL_FEEDS = [
    {
        "source": "OpenAI Developers",
        "url": "https://developers.openai.com/rss.xml",
        "our_angle": "OpenAI 업데이트를 논문 읽기, 요약, 출처 검증 workflow 관점으로 번역",
    },
    {
        "source": "arXiv cs.CL",
        "url": "https://export.arxiv.org/rss/cs.CL",
        "our_angle": "새 NLP/LLM 논문을 연구자가 따라 쓸 수 있는 읽기/검증 workflow로 번역",
    },
    {
        "source": "GitHub AI & ML",
        "url": "https://github.blog/ai-and-ml/feed/",
        "our_angle": "AI/ML 도구 흐름을 research agent와 논문 작업 자동화 관점으로 해석",
    },
]

SOURCE_POLICY = {
    "github_repo": {
        "reliability": "stable",
        "fact_boundary": "Facts: repo name, URL, stars, language, description, README text. Interpretation: how it changes research reading, drafting, citation, or review workflow.",
    },
    "official_feed": {
        "reliability": "stable",
        "fact_boundary": "Facts: official post title, URL, summary, published date. Interpretation: research workflow impact and account angle.",
    },
}

QUERIES = [
    {
        "category": "Paper summarization",
        "query": 'paper summarization LLM research assistant in:readme,description stars:>20',
        "our_angle": "논문 요약을 초록 재작성보다 contribution/evidence/limitation 추출로 바꾸는 법",
    },
    {
        "category": "Literature review",
        "query": '"literature review" LLM AI research in:readme,description stars:>20',
        "our_angle": "related work를 논문 나열이 아니라 evidence matrix로 만드는 법",
    },
    {
        "category": "Research assistant",
        "query": '"research assistant" LLM papers in:readme,description stars:>20',
        "our_angle": "AI research assistant를 검색 도구가 아니라 읽기/비교/검증 workflow로 쓰는 법",
    },
    {
        "category": "Citation verification",
        "query": 'citation verification reference checker LLM in:readme,description stars:>10',
        "our_angle": "AI가 만든 reference를 원문 metadata와 citation claim으로 검증하는 법",
    },
    {
        "category": "Research agent architecture",
        "query": 'multi-agent research paper LLM in:readme,description stars:>20',
        "our_angle": "reader, synthesizer, reviewer, editor agent를 분리해 논문 작업을 안정화하는 법",
    },
    {
        "category": "Academic writing",
        "query": 'academic writing LLM papers citation in:readme,description stars:>20',
        "our_angle": "AI 초안을 문장 생성이 아니라 주장-근거-인용 구조로 검수하는 법",
    },
]

KEYWORDS = {
    "paper": 6,
    "papers": 6,
    "research": 6,
    "literature review": 7,
    "citation": 6,
    "reference": 5,
    "summarization": 5,
    "summary": 4,
    "academic": 5,
    "arxiv": 5,
    "evidence": 5,
    "reviewer": 4,
    "agent": 4,
    "workflow": 4,
    "llm": 3,
}

REQUIRED_RELEVANCE_TERMS = [
    "paper",
    "papers",
    "research",
    "literature",
    "citation",
    "reference",
    "summarization",
    "summary",
    "academic",
    "arxiv",
    "evidence",
    "writing",
    "scholar",
]


def load_used_sources(history_path: Path) -> tuple[set[str], set[str]]:
    urls = set()
    names = set()
    if not history_path.exists():
        return urls, names

    for line in history_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("source_url"):
            urls.add(str(entry["source_url"]).strip().lower())
        if entry.get("source_name"):
            names.add(str(entry["source_name"]).strip().lower())
    return urls, names


def filter_used_sources(candidates: list[dict], history_path: Path) -> list[dict]:
    used_urls, used_names = load_used_sources(history_path)
    if not used_urls and not used_names:
        return candidates

    filtered = []
    skipped = []
    for item in candidates:
        url = str(item.get("url") or "").strip().lower()
        name = str(item.get("name") or item.get("title") or "").strip().lower()
        if url in used_urls or name in used_names:
            skipped.append(item.get("title") or item.get("name") or url)
            continue
        filtered.append(item)

    if skipped:
        print(f"Skipped {len(skipped)} previously used source(s): {', '.join(skipped[:5])}")
    return filtered


def github_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or read_gh_token()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "threads-agentic-editor",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def read_gh_token() -> str | None:
    gh_candidates = [
        "gh",
        str(Path.home() / "tools" / "gh" / "bin" / "gh.exe"),
    ]
    for gh in gh_candidates:
        try:
            result = subprocess.run(
                [gh, "auth", "token"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue

        token = result.stdout.strip()
        if result.returncode == 0 and token:
            return token
    return None


def collect_github(per_query: int) -> list[dict]:
    headers = github_headers()
    collected = []
    seen = set()

    for query in QUERIES:
        params = {
            "q": query["query"],
            "sort": "stars",
            "order": "desc",
            "per_page": per_query,
        }
        response = requests.get(GITHUB_SEARCH_URL, headers=headers, params=params, timeout=30)
        if response.status_code >= 400:
            print(f"Warning: skipped {query['category']} because GitHub returned {response.status_code}: {response.text[:160]}")
            continue
        data = response.json()

        for repo in data.get("items", []):
            full_name = repo.get("full_name")
            if not full_name or full_name in seen:
                continue

            visible_text = " ".join(
                [
                    full_name,
                    repo.get("description") or "",
                    " ".join(repo.get("topics") or []),
                ]
            ).lower()
            if not any(term in visible_text for term in REQUIRED_RELEVANCE_TERMS):
                continue

            seen.add(full_name)
            collected.append(
                {
                    "source_type": "github_repo",
                    "category": query["category"],
                    "name": full_name,
                    "title": full_name,
                    "url": repo.get("html_url"),
                    "description": repo.get("description") or "",
                    "stars": repo.get("stargazers_count") or 0,
                    "forks": repo.get("forks_count") or 0,
                    "language": repo.get("language"),
                    "topics": repo.get("topics") or [],
                    "updated_at": repo.get("updated_at"),
                    "pushed_at": repo.get("pushed_at"),
                    "our_angle": query["our_angle"],
                    "reliability": SOURCE_POLICY["github_repo"]["reliability"],
                    "fact_boundary": SOURCE_POLICY["github_repo"]["fact_boundary"],
                }
            )

    return collected


def collect_official_feeds(per_feed: int) -> list[dict]:
    collected = []
    headers = {"User-Agent": "threads-agentic-editor"}
    for feed in OFFICIAL_FEEDS:
        try:
            response = requests.get(feed["url"], headers=headers, timeout=30)
            if response.status_code >= 400:
                print(f"Warning: skipped feed {feed['source']} because HTTP {response.status_code}")
                continue
            root = ET.fromstring(response.content)
        except Exception as exc:
            print(f"Warning: skipped feed {feed['source']}: {exc}")
            continue

        entries = parse_feed_entries(root)[:per_feed]
        for entry in entries:
            visible_text = f"{entry['title']} {entry['summary']}".lower()
            if not any(term in visible_text for term in REQUIRED_RELEVANCE_TERMS):
                continue
            collected.append(
                {
                    "source_type": "official_feed",
                    "category": feed["source"],
                    "name": entry["title"],
                    "title": entry["title"],
                    "url": entry["url"],
                    "description": entry["summary"],
                    "stars": 0,
                    "forks": 0,
                    "language": None,
                    "topics": [],
                    "updated_at": entry["published"],
                    "pushed_at": entry["published"],
                    "our_angle": feed["our_angle"],
                    "reliability": SOURCE_POLICY["official_feed"]["reliability"],
                    "fact_boundary": SOURCE_POLICY["official_feed"]["fact_boundary"],
                }
            )
    return collected


def parse_feed_entries(root: ET.Element) -> list[dict]:
    entries = []
    if strip_ns(root.tag) == "rss" or root.find("channel") is not None:
        for item in root.findall("./channel/item"):
            entries.append(
                {
                    "title": text_of(item, "title"),
                    "url": text_of(item, "link"),
                    "summary": clean_text(text_of(item, "description")),
                    "published": text_of(item, "pubDate"),
                }
            )
    else:
        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            link = ""
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                link = link_el.attrib.get("href", "")
            entries.append(
                {
                    "title": text_of(entry, "{http://www.w3.org/2005/Atom}title"),
                    "url": link,
                    "summary": clean_text(text_of(entry, "{http://www.w3.org/2005/Atom}summary")),
                    "published": text_of(entry, "{http://www.w3.org/2005/Atom}updated"),
                }
            )
    return [entry for entry in entries if entry["title"] and entry["url"]]


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def text_of(parent: ET.Element, name: str) -> str:
    child = parent.find(name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:500]


def enrich_readmes(candidates: list[dict], top_n: int) -> list[dict]:
    headers = github_headers()
    github_items = [item for item in candidates if item.get("source_type") == "github_repo"]
    ranked = sorted(github_items, key=lambda item: item["score"]["total"], reverse=True)[:top_n]
    for item in ranked:
        api_url = f"https://api.github.com/repos/{item['name']}/readme"
        try:
            response = requests.get(api_url, headers=headers, timeout=30)
            if response.status_code >= 400:
                item["readme_summary"] = ""
                continue
            payload = response.json()
            raw = base64.b64decode(payload.get("content", "")).decode("utf-8", errors="ignore")
            item["readme_summary"] = summarize_readme(raw)
        except Exception:
            item["readme_summary"] = ""
    return candidates


def summarize_readme(raw: str) -> str:
    text = re.sub(r"```.*?```", " ", raw, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text).strip()
    return textwrap.shorten(text, width=900, placeholder="...")


def score_candidate(item: dict) -> dict:
    text = " ".join(
        [
            item.get("name") or "",
            item.get("description") or "",
            " ".join(item.get("topics") or []),
            item.get("category") or "",
        ]
    ).lower()

    keyword_score = sum(weight for key, weight in KEYWORDS.items() if key in text)
    stars = int(item.get("stars") or 0)
    forks = int(item.get("forks") or 0)

    is_official = item.get("source_type") == "official_feed"
    trend = 14 if is_official else min(20, stars // 1000 + forks // 200)
    utility = min(20, keyword_score + (4 if "workflow" in text or "tool" in text or "matrix" in text else 0))
    novelty = min(15, 9 + (4 if "citation" in text or "literature review" in text or "multi-agent" in text else 0))
    authority = 15 if is_official else min(15, 8 + min(7, stars // 5000))
    our_angle = min(20, 10 + keyword_score // 2)
    virality = min(10, 4 + (3 if any(k in text for k in ["paper", "citation", "literature", "academic"]) else 0))

    total = trend + utility + novelty + authority + our_angle + virality

    item["score"] = {
        "total": total,
        "trend": trend,
        "utility": utility,
        "novelty": novelty,
        "authority": authority,
        "our_angle": our_angle,
        "virality": virality,
    }
    item["draft_angles"] = {
        "A_broad": make_broad_angle(item),
        "B_deep": make_deep_angle(item),
    }
    if item.get("source_type") == "official_feed":
        item["risk"] = "Official updates are authoritative, but the research workflow angle is our interpretation. Avoid overstating product impact."
    else:
        item["risk"] = "GitHub stars show popularity, not research quality. Verify README/release details before making factual claims."
    return item


def make_broad_angle(item: dict) -> str:
    if item.get("source_type") == "official_feed":
        return "공식 업데이트를 그냥 요약하지 말고, 연구자가 내일 논문 작업에서 바꿀 점으로 번역한다."
    category = item.get("category", "")
    if "Literature" in category:
        return "AI에게 related work를 맡길 때 핵심은 문장 생성보다 논문 간 차이를 표로 고정하는 것이다."
    if "Citation" in category:
        return "AI가 만든 reference는 글감이 아니라 검증 대상이다."
    if "Paper" in category:
        return "논문 요약은 초록 재작성보다 주장, 근거, 한계 추출이 먼저다."
    return "AI 연구 도구를 볼 때 기능보다 먼저 봐야 할 것은 출처, 근거, 검증 흐름이다."


def make_deep_angle(item: dict) -> str:
    if item.get("source_type") == "official_feed":
        return f"{item.get('title')}에서 봐야 할 것은 새 기능 자체보다 논문 읽기/쓰기 workflow에 어떤 검증 구조를 추가하는지다."
    category = item.get("category", "")
    if "Research agent" in category:
        return "research agent는 reader, synthesizer, reviewer, editor를 분리해야 citation과 주장 검증이 쉬워진다."
    if "Academic writing" in category:
        return "AI 초안의 품질은 문체보다 problem-gap-contribution과 citation alignment에서 갈린다."
    return f"{item.get('name')}에서 볼 것은 기능 목록보다 논문 작업을 어떻게 읽기, 비교, 쓰기, 검증으로 나누는지다."


def write_outputs(candidates: list[dict], output_dir: Path, date: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ranked = sorted(candidates, key=lambda item: item["score"]["total"], reverse=True)

    json_path = output_dir / f"{date}-candidates.json"
    md_path = output_dir / f"{date}-brief.md"

    json_path.write_text(json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# Daily Research AI Editor Brief: {date}",
        "",
        "Use this with `$threads-agentic-editor` to draft A/B Threads options.",
        "",
        "## Top Candidates",
        "",
    ]

    for index, item in enumerate(ranked[:10], start=1):
        score = item["score"]
        lines.extend(
            [
                f"### {index}. {item['title']}",
                "",
                f"- Score: {score['total']} (trend {score['trend']}, utility {score['utility']}, novelty {score['novelty']}, authority {score['authority']}, angle {score['our_angle']}, virality {score['virality']})",
                f"- Category: {item['category']}",
                f"- Stars: {item['stars']}",
                f"- Language: {item.get('language') or 'Unknown'}",
                f"- URL: {item['url']}",
                f"- Description: {item.get('description') or 'No description'}",
                f"- README summary: {item.get('readme_summary') or 'Not collected'}",
                f"- Our angle: {item['our_angle']}",
                f"- Reliability: {item.get('reliability', 'unknown')}",
                f"- Facts vs interpretation: {item.get('fact_boundary', 'Separate source facts from our angle.')}",
                f"- A안: {item['draft_angles']['A_broad']}",
                f"- B안: {item['draft_angles']['B_deep']}",
                f"- Risk: {item['risk']}",
                "",
            ]
        )

    md_path.write_text("\n".join(lines), encoding="utf-8")
    write_prompt(output_dir, date, ranked[:5])

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    if ranked:
        print(f"Top candidate: {ranked[0]['title']} ({ranked[0]['score']['total']})")


def write_prompt(output_dir: Path, date: str, top_items: list[dict]) -> None:
    prompt_path = output_dir / f"{date}-draft-prompt.md"
    lines = [
        f"# Draft Prompt: {date}",
        "",
        "Use `$threads-agentic-editor`.",
        "",
        "Task:",
        "",
        "Create A/B Threads drafts from today's candidates. A안 should be broad and punchy. B안 should be deeper and more technical. Include card copy, sources, and risk notes. Do not publish.",
        "",
        "Candidates:",
        "",
    ]
    for index, item in enumerate(top_items, start=1):
        lines.extend(
            [
                f"{index}. {item['title']}",
                f"   URL: {item['url']}",
                f"   Score: {item['score']['total']}",
                f"   Description: {item.get('description') or ''}",
                f"   README: {item.get('readme_summary') or 'Not collected'}",
                f"   A angle: {item['draft_angles']['A_broad']}",
                f"   B angle: {item['draft_angles']['B_deep']}",
                f"   Facts vs interpretation: {item.get('fact_boundary', 'Separate source facts from our angle.')}",
                f"   Risk: {item['risk']}",
                "",
            ]
        )
    prompt_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {prompt_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and score daily research AI Threads candidates.")
    parser.add_argument("--per-query", type=int, default=5)
    parser.add_argument("--per-feed", type=int, default=5)
    parser.add_argument("--readme-top", type=int, default=5)
    parser.add_argument("--output-dir", default="daily-editor")
    parser.add_argument("--history-path", default="content-history.jsonl")
    parser.add_argument("--date", default=datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    raw_candidates = collect_github(args.per_query) + collect_official_feeds(args.per_feed)
    raw_candidates = filter_used_sources(raw_candidates, Path(args.history_path))
    if not raw_candidates:
        raise SystemExit("No unused candidates found. Add new source queries or review content-history.jsonl.")
    candidates = [score_candidate(item) for item in raw_candidates]
    candidates = enrich_readmes(candidates, args.readme_top)
    write_outputs(candidates, Path(args.output_dir), args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
