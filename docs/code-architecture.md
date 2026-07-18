# Code Architecture

## Modules

- `scripts/thread_spec.py`: parsing, normalization, rendering, spec construction, and canonical validation.
- `scripts/prepublish_quality_gate.py`: CLI presentation for the shared validation report.
- `scripts/generate_auto_thread.py`: candidate generation, editorial routing, scoring, and evaluator logic; no independent structural contract.
- `scripts/daily_publish_guard.py`: KST-day Threads reconciliation, manual-post blocking, and fail-closed error recording.
- `scripts/threads_auto_upload.py`: API publishing and logging; validates with the shared contract before creating containers.
- `schemas/thread-spec-v1.schema.json`: portable persisted contract.
- `schemas/thread-candidate-v1.schema.json`: strict, minimal model-output contract.

## Boundaries

- Structural validation answers whether a chain conforms.
- Editorial scoring answers whether a conforming chain is useful enough.
- Duplicate detection answers whether the idea is sufficiently novel.
- Provider/model selection answers how the candidate is generated, not what format is valid.
- Threads API state answers whether a post already exists; the repository history is a synchronized projection, not the authority for the daily skip decision.

## Tests

- Unit-test text parsing, role ordering, the canonical Part 1 request card, headings, length, source placement, reusable action, and warnings.
- Keep generator routing and editorial scoring tests separate from contract tests.
- Test both direct script execution imports and package-style test imports.
