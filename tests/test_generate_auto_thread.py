import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.generate_auto_thread import (
    THREAD_CANDIDATE_SCHEMA,
    build_evaluator_prompt,
    build_fallback_thread,
    classify_hook_pattern,
    call_groq,
    call_llm,
    choose_candidates,
    curation_bonus,
    extract_json,
    extract_text,
    load_recent_history,
    load_curation_log,
    main,
    normalize_thread_candidate,
    quality_gate,
    read_skill_library,
    safe_slug,
    select_content_format,
    validate_quote_selection,
    validate_thread,
)


SUGGESTION = {
    "id": "karpathy-predict-before-absorbing",
    "speaker": "Andrej Karpathy",
    "speaker_ko": "안드레이 카파시",
    "quote_ko": "정보를 받아들이기 전에 먼저 예측해보는 것이 이상적입니다.",
    "source_url": "https://karpathy.ai/tweets.html",
}


class QuoteSelectionTests(unittest.TestCase):
    def test_verified_quote_selection_passes(self) -> None:
        thread = (
            '안드레이 카파시는 "정보를 받아들이기 전에 먼저 예측해보는 것이 이상적입니다."라고 말했습니다.\n'
            "인용 원문:\nhttps://karpathy.ai/tweets.html"
        )
        result = validate_quote_selection(
            thread,
            {"quote_used": True, "quote_id": SUGGESTION["id"]},
            {"quote_suggestion": SUGGESTION},
        )
        self.assertEqual(result, SUGGESTION)

    def test_unsupplied_quote_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            validate_quote_selection(
                "안드레이 카파시",
                {"quote_used": True, "quote_id": SUGGESTION["id"]},
                {},
            )

    def test_quote_id_is_empty_when_unused(self) -> None:
        with self.assertRaises(SystemExit):
            validate_quote_selection(
                "No quote",
                {"quote_used": False, "quote_id": SUGGESTION["id"]},
                {},
            )


class FormatRouterTests(unittest.TestCase):
    def test_legacy_candidate_maps_to_new_router_format(self) -> None:
        candidate = {
            "title": "citation verification workflow",
            "description": "Check whether references support claims.",
            "content_axis": "checklist",
            "format_type": "copy_checklist",
            "post_goal": "save",
        }
        analysis = {"workflow_action": "AI가 만든 reference를 claim과 따로 검증한다."}
        routing = select_content_format(candidate, analysis, "2026-06-22", "morning")
        self.assertEqual(routing["format_type"], "research_checklist")
        self.assertEqual(routing["human_signal_type"], "citation_doubt")
        self.assertEqual(routing["reusable_unit_type"], "verification_checklist")

    def test_friday_evening_routes_to_weekly_review(self) -> None:
        candidate = {"title": "paper summary", "post_goal": "save"}
        routing = select_content_format(candidate, {}, "2026-06-26", "evening")
        self.assertEqual(routing["format_type"], "weekly_review_advice")

    def test_method_gap_routes_to_reproducibility_artifact(self) -> None:
        candidate = {
            "title": "paper method reproduction workflow",
            "description": "Turn method sections into reproducible steps.",
            "post_goal": "save",
        }
        routing = select_content_format(candidate, {}, "2026-06-30", "morning")
        self.assertEqual(routing["human_signal_type"], "method_understanding_gap")
        self.assertEqual(routing["failure_mode"], "method_steps_not_reproducible")
        self.assertEqual(routing["artifact_type"], "reproducibility_protocol")
        self.assertIn("재현 프로토콜", routing["artifact_output"])
        self.assertIn("재현 순서", routing["reader_test"])
        self.assertIn("방법론 복사", routing["failure_judgment"])

    def test_recent_history_infers_artifact_type_from_old_failure_mode(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "date": "2026-06-28",
                        "failure_mode": "claim_reference_mismatch",
                        "hook": "논문 작업을 AI에게 한 번에 맡기면",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            recent = load_recent_history(path)

        self.assertEqual(recent[0]["artifact_type"], "citation_support_table")


class ThreadValidationTests(unittest.TestCase):
    def test_two_part_chain_fails_fixed_master_template(self) -> None:
        thread = (
            "AI 요약이 너무 깔끔하면 먼저 claim과 evidence를 분리해야 합니다.\n\n"
            "읽기 쉬운 요약과 검증 가능한 연구 노트는 다릅니다.\n"
            "---\n"
            "바로 써볼 프롬프트:\n"
            "\"이 논문의 claim을 나누고, 각 claim을 받치는 evidence와 limitation을 표로 정리해줘.\""
        )
        with self.assertRaises(SystemExit):
            validate_thread(thread)

    def test_fixed_master_template_chain_passes(self) -> None:
        thread = (
            "논문 초안을 AI에게 맡길 때 자주 생기는 문제가 있습니다.\n\n"
            "\"이 문장 더 학술적으로 고쳐줘\"라고만 시키면 claim과 evidence 연결은 남지 않을 수 있습니다.\n"
            "---\n"
            "[먼저 확인할 것]\n"
            "초안 검수는 문장 품질보다 연결 구조를 먼저 봐야 합니다.\n\n"
            "1. claim이 분리되는가\n2. evidence 위치가 남는가\n3. citation 범위가 보이는가\n"
            "---\n"
            "[저장해둘 프롬프트]\n"
            "논문 읽을 때 붙여 넣을 문장:\n\n"
            "\"이 초안을 claim, evidence, limitation, citation으로 나눠줘.\"\n"
            "---\n"
            "[참고 논문]\n"
            "https://github.com/example/research-skills\n"
            "- 볼 부분: source fact를 workflow로 바꾸는 단서\n\n"
            "[나의 견해]\n"
            "source가 실제로 제공한 것과 내가 적용하려는 해석을 나눠보세요."
        )
        validate_thread(thread)

    def test_chain_without_reusable_unit_fails(self) -> None:
        with self.assertRaises(SystemExit):
            validate_thread("AI 시대에는 논문을 다르게 읽어야 합니다.")

    def test_paper_keyword_alone_is_not_personal_diary_hook(self) -> None:
        self.assertEqual(classify_hook_pattern("논문 citation을 검증할 때 먼저 볼 것은 claim입니다."), "direct_claim")

    def test_repeated_hook_pattern_warns_without_blocking_publish(self) -> None:
        thread = (
            "AI가 붙인 citation이 claim을 실제로 받치는지 먼저 확인해야 합니다.\n"
            "---\n"
            "[먼저 확인할 것]\n"
            "검증 체크리스트:\n"
            "1. claim을 분리한다\n"
            "2. citation 원문 위치를 찾는다\n"
            "3. evidence가 claim을 직접 지지하는지 표시한다\n"
            "---\n"
            "[저장해둘 프롬프트]\n"
            "오늘 적용할 문장:\n\n"
            "\"각 claim마다 citation이 실제로 받치는 범위를 표시해줘.\"\n"
            "---\n"
            "[참고 논문]\n"
            "https://github.com/example/research-skills\n"
            "- 볼 부분: source fact를 citation 검증 기준으로 바꾸는 단서\n\n"
            "[나의 견해]\n"
            "source가 실제로 제공한 것과 우리 해석을 분리하세요."
        )
        gate = quality_gate(
            thread,
            {"format_type": "research_checklist", "human_signal_source": "inferred"},
            [{"pattern": "direct_claim"}, {"pattern": "direct_claim"}, {"pattern": "direct_claim"}],
        )
        self.assertEqual(gate["decision"], "publish")
        self.assertEqual(gate["quality_score"], 92)

    def test_same_recent_artifact_warns_without_hard_blocking(self) -> None:
        thread = (
            "방법론 설명과 재현 가능한 절차는 다릅니다.\n\n"
            "AI가 방법을 잘 요약해도 input, 순서, 설정값이 빠지면 다시 실행할 수 없습니다.\n"
            "---\n"
            "[먼저 확인할 것]\n"
            "재현 프로토콜은 설명보다 실행 조건을 봅니다.\n\n"
            "1. input이 분리되는가\n"
            "2. procedure가 순서대로 남는가\n"
            "3. output check가 보이는가\n"
            "---\n"
            "[저장해둘 프롬프트]\n"
            "논문 읽을 때 붙여 넣을 문장:\n\n"
            "\"방법론을 input, procedure, parameter, output, check로 나눠줘.\"\n"
            "---\n"
            "[참고 논문]\n"
            "https://github.com/example/research-skills\n"
            "- 볼 부분: source fact를 재현 절차로 바꾸는 단서\n\n"
            "[나의 견해]\n"
            "source가 실제로 제공한 절차와 우리 해석을 분리하세요."
        )
        routing = {
            "format_type": "better_prompt_pattern",
            "human_signal_source": "inferred",
            "workflow_stage": "method_understanding",
            "failure_mode": "method_steps_not_reproducible",
            "artifact_type": "reproducibility_protocol",
        }
        gate = quality_gate(
            thread,
            routing,
            recent_history=[
                {
                    "workflow_stage": "method_understanding",
                    "failure_mode": "method_steps_not_reproducible",
                    "artifact_type": "reproducibility_protocol",
                    "hook_pattern": "direct_claim",
                }
            ],
        )
        self.assertEqual(gate["decision"], "publish")
        self.assertIn("Near-duplicate risk", " ".join(gate["reasons"]))


class SelfImprovementLoopTests(unittest.TestCase):
    def test_safe_slug_keeps_korean_and_removes_punctuation(self) -> None:
        self.assertEqual(safe_slug("2026-06-22 citation 검증!!"), "2026-06-22-citation-검증")

    def test_read_skill_library_collects_markdown_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "citation.md").write_text("# Citation\n검증 규칙", encoding="utf-8")
            (root / "ignore.txt").write_text("ignore", encoding="utf-8")
            text = read_skill_library(root)
        self.assertIn("citation.md", text)
        self.assertIn("검증 규칙", text)
        self.assertNotIn("ignore", text)

    def test_read_skill_library_accepts_consolidated_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "thread-pattern-library.md"
            path.write_text("# Pattern Library\ncitation 검증", encoding="utf-8")
            text = read_skill_library(path)
        self.assertIn("Pattern Library", text)
        self.assertIn("citation 검증", text)

    def test_evaluator_prompt_contains_thread_and_learning_context(self) -> None:
        prompt = build_evaluator_prompt(
            thread_text="바로 써볼 프롬프트:\n\"claim과 citation을 분리해줘.\"",
            routing={"format_type": "research_checklist"},
            analysis={"workflow_action": "citation 검증"},
            recent_history=[],
            persistent_learnings="citation은 claim 지지 여부를 본다.",
            skill_library="Citation Verification",
        )
        self.assertIn("Return JSON only", prompt)
        self.assertIn("citation은 claim 지지 여부를 본다.", prompt)
        self.assertIn("바로 써볼 프롬프트", prompt)

    def test_extract_text_reads_chat_completion_payload(self) -> None:
        payload = {"choices": [{"message": {"content": '{"thread_text":"ok"}'}}]}
        self.assertEqual(extract_text(payload), '{"thread_text":"ok"}')

    def test_extract_json_repairs_backslash_newline(self) -> None:
        data = extract_json('{"thread_text":"첫 줄\\\n둘째 줄"}')
        self.assertEqual(data["thread_text"], "첫 줄\n둘째 줄")

    def test_thread_candidate_uses_deterministic_source_metadata(self) -> None:
        payload = {
            "hook": "문제를 확인해야 합니다.",
            "diagnosis": "[먼저 확인할 것]\n1. claim\n2. evidence\n3. limitation",
            "action": "[저장해둘 프롬프트]\nclaim과 evidence를 연결해줘.",
            "source": "[참고 자료]\nhttps://example.com\n- 볼 부분: 근거 구조\n[나의 견해] 검증표로 바꿉니다.",
            "quote_used": False,
            "quote_id": "",
        }
        candidate = {"title": "Trusted source", "url": "https://example.com"}
        routing = {"human_signal_type": "evidence", "format_type": "research_checklist"}

        normalized = normalize_thread_candidate(payload, candidate, routing)

        self.assertEqual(normalized["source_name"], "Trusted source")
        self.assertEqual(normalized["source_url"], "https://example.com")
        self.assertEqual(normalized["source_count"], 1)
        self.assertEqual(len(normalized["thread_text"].split("\n---\n")), 4)

    def test_fallback_thread_passes_quality_gate(self) -> None:
        routing = {
            "research_problem": "AI가 붙인 citation이 claim을 실제로 받치는지 검증하기 어렵다.",
            "format_type": "agent_role_split",
        }
        analysis = {"workflow_action": "claim, evidence, citation을 분리해 검증한다."}
        candidate = {"title": "example/research-skills", "url": "https://github.com/example/research-skills"}
        thread = build_fallback_thread(candidate, routing, analysis)
        validate_thread(thread)
        self.assertNotIn("GitHub stars는 인기 신호일 뿐이고", thread)
        self.assertIn("[저장해둘 프롬프트]", thread)
        self.assertNotEqual(quality_gate(thread, routing)["decision"], "discard")

    def test_curation_log_boosts_matching_future_signals(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "curation.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "codex_gate_decision": "keep",
                        "selected_content_axis": "official_update",
                        "selected_format_type": "tiny_source_case",
                        "preferred_future_signals": ["superseded fact", "research workflow"],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            records = load_curation_log(path)

        candidate = {
            "title": "Superseded fact memory update",
            "description": "A research workflow for current and old facts.",
            "content_axis": "official_update",
            "format_type": "tiny_source_case",
            "score": {"total": 30},
        }
        self.assertGreater(curation_bonus(candidate, records), 0)

    def test_choose_candidates_uses_curation_bonus(self) -> None:
        records = [
            {
                "codex_gate_decision": "keep",
                "preferred_future_signals": ["superseded fact"],
            }
        ]
        candidates = [
            {"title": "generic paper", "score": {"total": 40}, "url": "https://example.com/a"},
            {"title": "superseded fact workflow", "score": {"total": 36}, "url": "https://example.com/b"},
        ]
        selected = choose_candidates(candidates, count=1, curation_records=records)
        self.assertEqual(selected[0]["url"], "https://example.com/b")

    def test_groq_size_limit_retries_with_smaller_completion_budget(self) -> None:
        class FakeResponse:
            def __init__(self, status_code: int, text: str = "", payload: dict | None = None) -> None:
                self.status_code = status_code
                self.text = text
                self._payload = payload or {}
                self.ok = status_code < 400

            def json(self) -> dict:
                return self._payload

        calls = []

        def fake_post(*args, **kwargs):
            calls.append(kwargs["json"]["max_completion_tokens"])
            if len(calls) == 1:
                return FakeResponse(
                    413,
                    '{"error":{"message":"Request too large on tokens per minute","code":"rate_limit_exceeded"}}',
                )
            return FakeResponse(200, payload={"choices": [{"message": {"content": '{"thread_text":"ok"}'}}]})

        with patch("scripts.generate_auto_thread.requests.post", side_effect=fake_post):
            payload = call_groq("key", "model", "prompt", max_output_tokens=900)

        self.assertEqual(extract_text(payload), '{"thread_text":"ok"}')
        self.assertEqual(calls, [900, 585])

    def test_groq_gpt_oss_uses_json_and_hidden_reasoning_options(self) -> None:
        class FakeResponse:
            ok = True
            status_code = 200
            text = ""

            def json(self) -> dict:
                return {"choices": [{"message": {"content": '{"thread_text":"ok"}'}}]}

        request_bodies = []

        def fake_post(*args, **kwargs):
            request_bodies.append(kwargs["json"])
            return FakeResponse()

        with patch("scripts.generate_auto_thread.requests.post", side_effect=fake_post):
            call_groq("key", "openai/gpt-oss-120b", "prompt", max_output_tokens=500)

        body = request_bodies[0]
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertFalse(body["include_reasoning"])
        self.assertEqual(body["reasoning_effort"], "low")

    def test_pinned_gemma_uses_strict_schema_and_required_parameters(self) -> None:
        class FakeResponse:
            ok = True
            status_code = 200
            text = ""

            def json(self) -> dict:
                return {"choices": [{"message": {"content": '{"thread_text":"ok"}'}}]}

        calls = []

        def fake_post(*args, **kwargs):
            calls.append((args, kwargs))
            return FakeResponse()

        with patch("scripts.generate_auto_thread.requests.post", side_effect=fake_post):
            call_llm(
                "openrouter",
                "key",
                "google/gemma-4-26b-a4b-it:free",
                "prompt",
                max_output_tokens=500,
                response_schema=THREAD_CANDIDATE_SCHEMA,
            )

        args, kwargs = calls[0]
        self.assertEqual(args[0], "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(kwargs["json"]["model"], "google/gemma-4-26b-a4b-it:free")
        response_format = kwargs["json"]["response_format"]
        self.assertEqual(response_format["type"], "json_schema")
        self.assertTrue(response_format["json_schema"]["strict"])
        self.assertEqual(response_format["json_schema"]["schema"], THREAD_CANDIDATE_SCHEMA)
        self.assertEqual(kwargs["json"]["provider"], {"require_parameters": True})
        self.assertEqual(kwargs["json"]["max_tokens"], 500)
        self.assertNotIn("max_completion_tokens", kwargs["json"])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer key")
        self.assertIn("HTTP-Referer", kwargs["headers"])
        self.assertIn("X-Title", kwargs["headers"])

    def test_malformed_model_json_uses_fallback_thread(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_path = root / "candidates.json"
            output_path = root / "approved-thread-chain.txt"
            metadata_path = root / "metadata.json"
            playbook_path = root / "playbook.md"
            metrics_path = root / "metrics.csv"
            candidates_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "example/research-skills",
                            "url": "https://github.com/example/research-skills",
                            "source_type": "github_repo",
                            "content_axis": "checklist",
                            "format_type": "research_checklist",
                            "post_goal": "save",
                            "score": {"total": 42},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            playbook_path.write_text("Write practical Korean Threads posts.", encoding="utf-8")

            llm_calls = []

            def fake_call_llm(*args, **kwargs):
                llm_calls.append((args, kwargs))
                return {"choices": [{"message": {"content": "not json at all"}}]}

            argv = [
                "generate_auto_thread.py",
                "--date",
                "2026-06-27",
                "--candidates-path",
                str(candidates_path),
                "--playbook-path",
                str(playbook_path),
                "--output-path",
                str(output_path),
                "--metadata-path",
                str(metadata_path),
                "--metrics-path",
                str(metrics_path),
                "--history-path",
                str(root / "missing-history.jsonl"),
                "--quote-bank-path",
                str(root / "missing-quotes.json"),
                "--weekly-memory-path",
                str(root / "missing-memory.md"),
                "--learnings-path",
                str(root / "missing-learnings.md"),
                "--skills-library-dir",
                str(root / "missing-skills"),
                "--curation-log-path",
                str(root / "missing-curation.jsonl"),
                "--review-dir",
                str(root / "review"),
                "--run-log-dir",
                str(root / "runs"),
                "--evaluation-dir",
                str(root / "evaluations"),
                "--skip-evaluator",
            ]

            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "LLM_FALLBACK_PROVIDER": ""}), patch.object(sys, "argv", argv), patch(
                "scripts.generate_auto_thread.call_llm", side_effect=fake_call_llm
            ):
                self.assertEqual(main(), 2)

            thread = (root / "review" / "2026-06-27-morning-draft-thread.txt").read_text(encoding="utf-8")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        validate_thread(thread)
        self.assertEqual(len(llm_calls), 2)
        self.assertIn("openrouter returned malformed JSON", metadata["quality_reasons"][0])
        self.assertEqual(metadata["provider"], "openrouter")
        self.assertEqual(metadata["model"], "google/gemma-4-26b-a4b-it:free")
        self.assertEqual(metadata["quality_decision"], "draft")
        self.assertEqual(metadata["artifact_type"], "summary_verification_grid")
        self.assertIn("설명 못하면", metadata["reader_test"])

    def test_openrouter_malformed_json_falls_back_to_groq(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_path = root / "candidates.json"
            output_path = root / "approved-thread-chain.txt"
            metadata_path = root / "metadata.json"
            playbook_path = root / "playbook.md"
            metrics_path = root / "metrics.csv"
            candidates_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "Claim evidence workflow",
                            "url": "https://github.com/example/claim-evidence-workflow",
                            "source_type": "github_repo",
                            "content_axis": "checklist",
                            "format_type": "research_checklist",
                            "post_goal": "save",
                            "score": {"total": 42},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            playbook_path.write_text("Write practical Korean Threads posts.", encoding="utf-8")
            thread_text = (
                "논문 요약을 AI에게 맡길 때 먼저 봐야 할 기준이 있습니다.\n\n"
                "문장보다 claim과 evidence 연결이 먼저입니다.\n"
                "---\n"
                "[먼저 확인할 것]\n"
                "1. claim이 한 문장으로 분리되는가\n"
                "2. evidence가 표나 실험과 연결되는가\n"
                "3. limitation이 남아 있는가\n"
                "---\n"
                "[저장해둘 프롬프트]\n"
                "AI agent에게 이렇게 시켜보세요.\n\n"
                "\"이 요약을 claim, evidence, limitation으로 나누고 각 claim의 근거 위치를 표시해줘.\"\n"
                "---\n"
                "[나의 견해]\n"
                "source fact: claim과 evidence를 분리해 보는 workflow 자료입니다.\n"
                "우리 해석: 초안 전에 검증표를 먼저 만들면 citation 오류를 줄일 수 있습니다.\n"
                "https://github.com/example/claim-evidence-workflow"
            )

            calls = []

            def fake_call_llm(provider, api_key, model, prompt, max_output_tokens=500, response_schema=None):
                calls.append(provider)
                if provider == "openrouter":
                    return {"choices": [{"message": {"content": "not json at all"}}]}
                return {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        **dict(zip(("hook", "diagnosis", "action", "source"), thread_text.split("\n---\n"))),
                                        "quote_used": False,
                                        "quote_id": "",
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ]
                }

            argv = [
                "generate_auto_thread.py",
                "--date",
                "2026-06-27",
                "--candidates-path",
                str(candidates_path),
                "--playbook-path",
                str(playbook_path),
                "--output-path",
                str(output_path),
                "--metadata-path",
                str(metadata_path),
                "--metrics-path",
                str(metrics_path),
                "--history-path",
                str(root / "missing-history.jsonl"),
                "--quote-bank-path",
                str(root / "missing-quotes.json"),
                "--weekly-memory-path",
                str(root / "missing-memory.md"),
                "--learnings-path",
                str(root / "missing-learnings.md"),
                "--skills-library-dir",
                str(root / "missing-skills"),
                "--curation-log-path",
                str(root / "missing-curation.jsonl"),
                "--review-dir",
                str(root / "review"),
                "--run-log-dir",
                str(root / "runs"),
                "--evaluation-dir",
                str(root / "evaluations"),
                "--skip-evaluator",
            ]

            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "openrouter-key",
                    "GROQ_API_KEY": "groq-key",
                    "LLM_FALLBACK_PROVIDER": "groq",
                },
            ), patch.object(sys, "argv", argv), patch(
                "scripts.generate_auto_thread.call_llm", side_effect=fake_call_llm
            ):
                self.assertEqual(main(), 2)

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(calls, ["openrouter", "openrouter", "groq"])
        self.assertEqual(metadata["provider"], "groq")
        self.assertEqual(metadata["requested_provider"], "openrouter")
        self.assertEqual(metadata["quality_decision"], "draft")

    def test_provider_api_error_uses_fallback_thread(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates_path = root / "candidates.json"
            output_path = root / "approved-thread-chain.txt"
            metadata_path = root / "metadata.json"
            playbook_path = root / "playbook.md"
            metrics_path = root / "metrics.csv"
            candidates_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "research summary verification",
                            "url": "https://github.com/example/research-summary-verification",
                            "source_type": "github_repo",
                            "content_axis": "checklist",
                            "format_type": "research_checklist",
                            "post_goal": "save",
                            "score": {"total": 42},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            playbook_path.write_text("Write practical Korean Threads posts.", encoding="utf-8")

            argv = [
                "generate_auto_thread.py",
                "--date",
                "2026-06-27",
                "--candidates-path",
                str(candidates_path),
                "--playbook-path",
                str(playbook_path),
                "--output-path",
                str(output_path),
                "--metadata-path",
                str(metadata_path),
                "--metrics-path",
                str(metrics_path),
                "--history-path",
                str(root / "missing-history.jsonl"),
                "--quote-bank-path",
                str(root / "missing-quotes.json"),
                "--weekly-memory-path",
                str(root / "missing-memory.md"),
                "--learnings-path",
                str(root / "missing-learnings.md"),
                "--skills-library-dir",
                str(root / "missing-skills"),
                "--curation-log-path",
                str(root / "missing-curation.jsonl"),
                "--review-dir",
                str(root / "review"),
                "--run-log-dir",
                str(root / "runs"),
                "--evaluation-dir",
                str(root / "evaluations"),
                "--skip-evaluator",
            ]

            with patch.dict(
                os.environ,
                {"OPENROUTER_API_KEY": "test-key", "LLM_FALLBACK_PROVIDER": ""},
            ), patch.object(sys, "argv", argv), patch(
                "scripts.generate_auto_thread.call_llm", side_effect=SystemExit("openrouter API error 400")
            ):
                self.assertEqual(main(), 2)

            thread = (root / "review" / "2026-06-27-morning-draft-thread.txt").read_text(encoding="utf-8")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        validate_thread(thread)
        self.assertIn("openrouter generation failed", metadata["quality_reasons"][0])
        self.assertEqual(metadata["quality_decision"], "draft")


if __name__ == "__main__":
    unittest.main()
