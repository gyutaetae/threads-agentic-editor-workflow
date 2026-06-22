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
AUTO_PUBLISH_THRESHOLD=90
```

The dashboard reads candidates and history from GitHub, creates two draft options, records edit-derived learning candidates, and dispatches the existing `Publish Threads Chain` workflow.

## Loop

1. Pick one of two drafts.
2. Edit it in the dashboard.
3. Save edited diff as a learning candidate.
4. Run dry-run or auto-publish when the quality score passes.
5. Promote learning candidates later only after post metrics prove the edit helped.
