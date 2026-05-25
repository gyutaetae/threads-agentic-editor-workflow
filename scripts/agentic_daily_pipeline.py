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
        "our_angle": "OpenAI 개발자 업데이트를 Codex/API/agent workflow 관점으로 번역",
    },
    {
        "source": "GitHub Changelog",
        "url": "https://github.blog/changelog/feed/",
        "our_angle": "GitHub 기능 변화를 agentic development workflow 관점으로 해석",
    },
    {
        "source": "GitHub AI & ML",
        "url": "https://github.blog/ai-and-ml/feed/",
        "our_angle": "GitHub AI/ML 흐름을 개발자 작업법과 repo 선택 기준으로 번역",
    },
]

SOURCE_POLICY = {
    "github_repo": {
        "reliability": "stable",
        "fact_boundary": "Facts: repo name, URL, stars, language, description, README text. Interpretation: why it matters and what workflow lesson to draw.",
    },
    "official_feed": {
        "reliability": "stable",
        "fact_boundary": "Facts: official post title, URL, summary, published date. Interpretation: developer workflow impact and account angle.",
    },
}

QUERIES = [
    {
        "category": "Codex workflow",
        "query": 'Codex agent workflow in:readme,description stars:>20',
        "our_angle": "Codex를 큰 요청이 아니라 검증 가능한 작업 단위로 쓰는 법",
    },
    {
        "category": "Claude Code workflow",
        "query": '"Claude Code" agent workflow in:readme,description stars:>20',
        "our_angle": "Claude Code를 terminal-native agent로 운영하는 실전 패턴",
    },
    {
        "category": "Cursor agent workflow",
        "query": 'Cursor agent workflow AI coding in:readme,description stars:>20',
        "our_angle": "IDE-first agent workflow와 CLI agent workflow의 차이",
    },
    {
        "category": "MCP tools",
        "query": 'MCP server Claude Code Cursor agent in:readme,description stars:>50',
        "our_angle": "MCP를 툴 연결이 아니라 작업 환경을 agent에게 넘기는 방식으로 해석",
    },
    {
        "category": "Subagent architecture",
        "query": 'subagent multi-agent architecture LLM in:readme,description stars:>20',
        "our_angle": "subagent를 역할보다 권한 경계로 설계하는 법",
    },
    {
        "category": "Agent eval observability",
        "query": 'AI agent eval observability harness LLM in:readme,description stars:>20',
        "our_angle": "agent를 믿기 전에 로그, 평가, 되돌리기를 설계하는 법",
    },
]

KEYWORDS = {
    "codex": 6,
    "claude": 6,
    "cursor": 5,
    "mcp": 5,
    "agent": 4,
    "subagent": 5,
    "multi-agent": 4,
    "workflow": 4,
    "automation": 3,
    "eval": 3,
    "observability": 3,
    "harness": 4,
}

REQUIRED_RELEVANCE_TERMS = [
    "agent",
    "agentic",
    "llm",
    "mcp",
    "claude",
    "codex",
    "cursor",
    "subagent",
    "multi-agent",
    "multiagent",
    "ai coding",
    "automation",
    "harness",
]


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
            if not any(term in visible_text for term in REQUIRED_RELEVANCE_TERMS + ["developer", "github", "openai", "model"]):
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
    utility = min(20, keyword_score + (4 if "workflow" in text or "tool" in text else 0))
    novelty = min(15, 9 + (4 if "mcp" in text or "subagent" in text else 0))
    authority = 15 if is_official else min(15, 8 + min(7, stars // 5000))
    our_angle = min(20, 10 + keyword_score // 2)
    virality = min(10, 4 + (3 if any(k in text for k in ["codex", "claude", "cursor"]) else 0))

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
        item["risk"] = "Official updates are authoritative, but the developer workflow angle is our interpretation. Avoid overstating product impact."
    else:
        item["risk"] = "GitHub stars show popularity, not quality. Verify README/release details before making factual claims."
    return item


def make_broad_angle(item: dict) -> str:
    if item.get("source_type") == "official_feed":
        return "공식 업데이트를 그냥 요약하지 말고, 개발자가 내일 작업 방식에서 바꿀 점으로 번역한다."
    category = item.get("category", "")
    if "MCP" in category:
        return "요즘 개발자들이 MCP에 꽂히는 이유는 툴 연결보다 agent에게 작업 환경을 넘기기 위해서다."
    if "Codex" in category or "Claude" in category or "Cursor" in category:
        return "AI 코딩툴 잘 쓰는 사람은 프롬프트보다 작업 단위를 먼저 설계한다."
    return "GitHub에서 뜨는 agent repo를 볼 때 star보다 먼저 봐야 할 것은 권한, 로그, 검증 구조다."


def make_deep_angle(item: dict) -> str:
    if item.get("source_type") == "official_feed":
        return f"{item.get('title')}에서 봐야 할 것은 새 기능 자체보다 agent workflow에 어떤 권한/도구 경계를 추가하는지다."
    category = item.get("category", "")
    if "Subagent" in category:
        return "subagent는 역할 분담보다 실패 범위와 권한 경계를 줄이기 위해 설계해야 한다."
    if "eval" in category.lower() or "observability" in category.lower():
        return "agent를 프로덕션에 넣는 순간 핵심은 모델 성능보다 관찰 가능성과 되돌리기다."
    return f"{item.get('name')}에서 볼 것은 기능 목록보다 agent workflow를 어떻게 구조화했는지다."


def write_outputs(candidates: list[dict], output_dir: Path, date: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ranked = sorted(candidates, key=lambda item: item["score"]["total"], reverse=True)

    json_path = output_dir / f"{date}-candidates.json"
    md_path = output_dir / f"{date}-brief.md"

    json_path.write_text(json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# Daily Agentic Editor Brief: {date}",
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
    parser = argparse.ArgumentParser(description="Collect and score daily AI agent Threads candidates.")
    parser.add_argument("--per-query", type=int, default=5)
    parser.add_argument("--per-feed", type=int, default=5)
    parser.add_argument("--readme-top", type=int, default=5)
    parser.add_argument("--output-dir", default="daily-editor")
    parser.add_argument("--date", default=datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    raw_candidates = collect_github(args.per_query) + collect_official_feeds(args.per_feed)
    candidates = [score_candidate(item) for item in raw_candidates]
    candidates = enrich_readmes(candidates, args.readme_top)
    write_outputs(candidates, Path(args.output_dir), args.date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
