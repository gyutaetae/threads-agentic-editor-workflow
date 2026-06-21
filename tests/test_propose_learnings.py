import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.propose_learnings import build_proposals, read_logs, render_learnings_markdown, render_skill_markdown


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class ProposeLearningsTests(unittest.TestCase):
    def test_promotes_good_learning_and_skill_candidate(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(
                root / "runs" / "run-1.json",
                {
                    "run_id": "run-1",
                    "topic": "AI citation 검증",
                    "format": "research_checklist",
                    "thread_url": "https://www.threads.net/@arxiv.ai/post/1",
                    "post_ids": ["1"],
                    "final_thread_parts": [
                        "citation이 있다는 것과 claim을 받친다는 것은 다릅니다.",
                        "바로 써볼 프롬프트: claim과 citation을 분리해줘.",
                    ],
                },
            )
            write_json(
                root / "evals" / "run-1.eval.json",
                {
                    "run_id": "run-1",
                    "evaluation": {
                        "score": 88,
                        "decision": "publish",
                        "learning_candidate": "citation 글은 reference 존재 여부보다 claim 지지 여부를 먼저 묻는다.",
                        "revision_suggestions": ["출처가 말하는 것과 우리가 적용할 방식을 더 분리한다."],
                        "skill_candidate": {
                            "name": "citation_verification",
                            "summary": "claim-citation-evidence table을 중심으로 citation 검증 글을 구성한다.",
                        },
                    },
                },
            )
            (root / "metrics.csv").write_text(
                "post_id,thread_url,likes,audience_replies,reposts,quotes,saves,profile_visits,follows_gained\n"
                "1,https://www.threads.net/@arxiv.ai/post/1,3,0,1,0,0,0,0\n",
                encoding="utf-8",
            )

            records = read_logs(root / "runs", root / "evals", root / "metrics.csv")
            proposals = build_proposals(records, existing_learnings="", min_score=85)

        self.assertEqual(len(proposals["learning_candidates"]), 1)
        self.assertEqual(proposals["learning_candidates"][0]["evidence"][0]["engagement"], 1)
        self.assertEqual(proposals["skill_candidates"][0]["name"], "citation_verification")

        markdown = render_learnings_markdown(proposals, min_score=85)
        self.assertIn("citation 글은 reference 존재 여부보다 claim 지지 여부", markdown)

        skill_markdown = render_skill_markdown(proposals["skill_candidates"][0])
        self.assertIn("claim-citation-evidence table", skill_markdown)
        self.assertIn("run-1", skill_markdown)

    def test_dedupes_existing_learning(self) -> None:
        record = {
            "run_id": "run-1",
            "run": {"topic": "논문 요약", "format": "workflow_observation"},
            "evaluation": {
                "score": 90,
                "decision": "publish",
                "learning_candidate": "AI 요약은 claim과 evidence로 나눠 검증한다.",
            },
            "metric": None,
            "average_engagement": 0,
        }
        proposals = build_proposals(
            [record],
            existing_learnings="- AI 요약은 claim과 evidence로 나눠 검증한다.",
            min_score=85,
        )
        self.assertEqual(proposals["learning_candidates"], [])

    def test_repeated_revision_becomes_candidate(self) -> None:
        records = []
        for index in range(2):
            records.append(
                {
                    "run_id": f"run-{index}",
                    "run": {"topic": "source case", "format": "tiny_source_case"},
                    "evaluation": {
                        "score": 70,
                        "decision": "revise",
                        "revision_suggestions": ["출처가 말하는 것과 우리가 적용할 방식을 더 분리한다."],
                    },
                    "metric": None,
                    "average_engagement": 0,
                }
            )

        proposals = build_proposals(records, existing_learnings="", min_score=85)

        self.assertEqual(len(proposals["revision_candidates"]), 1)
        self.assertEqual(proposals["revision_candidates"][0]["count"], 2)


if __name__ == "__main__":
    unittest.main()
