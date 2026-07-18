# Architecture Decisions

## ADR-001: The playbook owns channel format

**Decision:** `docs/threads-channel-playbook.md` is the only source of truth for chain shape and voice. Skills describe procedure and handoff only.

**Intent:** Prevent the editor skill, generator prompt, and quality gate from drifting independently.

## ADR-002: Fix semantic roles, not repeated wording

**Decision:** Every chain has exactly four roles: `hook`, `diagnosis`, `action`, `source`. Parts 2-4 use role-specific bracket headings. A bad/good request card and `[핵심 한 줄]` are optional surface patterns, not mandatory structure.

**Intent:** Keep manual and automatic output recognizable without making the account feel factory-generated.

## ADR-003: One shared validator with phase strictness

**Decision:** All paths call `scripts/thread_spec.py`. Contract errors always block. Warnings may remain in a review draft, but strict prepublish validation blocks warnings.

**Intent:** Drafting can produce repairable output while no publishing path bypasses the canonical contract.

## ADR-004: Pin the automatic generation model

**Decision:** The unattended writer uses OpenRouter with the full slug `google/gemma-4-26b-a4b-it:free`. The provider and slug are workflow constants, not repository-variable overrides. The writer must return the strict `ThreadCandidate v1` JSON Schema. No alternate provider may produce an automatically publishable replacement; a failed Gemma run becomes a review draft.

**Intent:** The free router selects among available free models, so style and quality cannot be expected to remain stable across runs.

## ADR-005: Progressive duplicate checks

**Decision:** Check exact identity first, structured editorial fingerprints second, and semantic similarity only for survivors. A semantic model may explain borderline overlap but does not make the final blocking decision alone.

**Intent:** Deterministic checks are cheap and auditable; embeddings help paraphrases; an LLM-only judge is too variable for the source of truth.

## ADR-006: Treat the platform as the publication ledger

**Decision:** Before generation and again immediately before publishing, query the Threads API for the current KST calendar day. Any authored top-level post, including a quote post, blocks the day's automatic publish. Replies and reposts do not. Newly observed posts are appended to local history with `origin=external_manual`; missing editorial fields remain explicitly unclassified.

**Intent:** Manual posts made outside GitHub Actions must still prevent a duplicate daily post and become visible to later duplicate and metrics processing.

## ADR-007: Fail closed and preserve evidence

**Decision:** If the daily platform check cannot establish that publishing is safe, do not publish. Record token/API failures under `daily-editor/failures/`. If generation, contract validation, or quality review fails, retain draft/spec/run artifacts without publishing.

**Intent:** Missing credentials or uncertain platform state must not cause an accidental second post, while repairable drafts and diagnostics remain available.
