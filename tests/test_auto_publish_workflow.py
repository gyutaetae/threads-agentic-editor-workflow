import unittest
from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/auto-publish-daily-thread.yml")


class AutoPublishWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_watchdogs_collect_candidates_in_fresh_runner(self) -> None:
        collect_block = self.workflow.split("- name: Collect candidates", 1)[1].split(
            "- name: Generate approved chain", 1
        )[0]
        self.assertIn("if: steps.daily_guard.outputs.should_generate == 'true'", collect_block)
        self.assertNotIn("run_mode != 'watchdog'", collect_block)

    def test_generation_fallback_and_attempt_ledger_are_enabled(self) -> None:
        self.assertIn('OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}', self.workflow)
        self.assertIn("OPENAI_MODEL: ${{ vars.OPENAI_MODEL || 'gpt-5.6-terra' }}", self.workflow)
        self.assertIn('LLM_FALLBACK_PROVIDERS: openai,groq', self.workflow)
        self.assertIn('--attempt-history-path ".\\daily-editor\\state\\generation-attempts.jsonl"', self.workflow)
        self.assertIn('git add -f daily-editor/state/generation-attempts.jsonl', self.workflow)

    def test_default_generation_count_preserves_rate_limit_headroom(self) -> None:
        self.assertIn("GENERATION_CANDIDATES: ${{ vars.GENERATION_CANDIDATES || '1' }}", self.workflow)

    def test_optional_reserve_directories_are_staged_independently(self) -> None:
        self.assertIn('Test-Path ".\\daily-editor\\reserve\\available"', self.workflow)
        self.assertIn('Test-Path ".\\daily-editor\\reserve\\used"', self.workflow)
        self.assertNotIn('git add -f daily-editor/reserve/available daily-editor/reserve/used', self.workflow)


if __name__ == "__main__":
    unittest.main()
