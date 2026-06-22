# Threads Workflow Dashboard

Fast MVP dashboard for the `@arxiv.ai` Threads workflow harness.

## Environment

Required on Vercel:

```bash
GITHUB_TOKEN=github token with repo contents + actions workflow dispatch access
GITHUB_OWNER=gyutaetae
GITHUB_REPO=threads-agentic-editor-workflow
GITHUB_BRANCH=master
DASHBOARD_SECRET=shared password for publish and learning writes
AUTO_PUBLISH_THRESHOLD=85
```

The dashboard reads candidates and history from GitHub, creates two draft options, records edit-derived learning candidates, and dispatches the existing `Publish Threads Chain` workflow.

## Loop

1. Pick one of two drafts.
2. Edit it in the dashboard.
3. Save edited diff as a learning candidate.
4. Run dry-run or auto-publish when the quality score passes.
5. Promote learning candidates later only after post metrics prove the edit helped.

## Scoring

Auto-publish is allowed from score 85. The scorer rejects short placeholder text, generic hooks, missing reusable work units, source links without `- 볼 부분:`, and oversized parts.

Metrics are weighted in this order:

1. likes
2. reposts
3. shares/quotes
4. audience comments
5. profile visits

## Crystallization

The dashboard follows a GenericAgent-style loop:

minimal toolset -> A/B drafts -> quality gate -> publish metrics -> user edit diff -> learning candidate -> crystallized skill tree.

Saved user edits influence the next generated draft by preserving useful structure such as part count, reusable-unit labels, and source-inspection labels.
