# Threads API Auto-Post Setup

Goal: publish approved AI-agent posts from the local growth console to your existing Threads account through the official Threads Graph API.

Current workflow:

1. Generate A/B candidates with the daily editor workflow.
2. Save the approved reply chain to `approved-thread-chain.txt`.
3. Run `.\scripts\publish-approved-chain.ps1 -DryRun`.
4. If the preview is correct, run `.\scripts\publish-approved-chain.ps1`.

## Required Meta Setup

You need a Meta developer app with Threads API access.

Required scopes:

- `threads_basic`
- `threads_content_publish`

Optional later:

- `threads_manage_insights` for analytics.

For your own account or app tester accounts, you can often test before full production review. Publishing for other users requires Meta app review and Advanced Access.

Also add your intended Threads account as a Threads tester in the Meta developer console while the app is in development mode.

## Local Environment

Open PowerShell in `C:\Users\kym70`.

Set app values:

```powershell
$env:THREADS_APP_ID = "YOUR_THREADS_APP_ID"
$env:THREADS_APP_SECRET = "YOUR_THREADS_APP_SECRET"
$env:THREADS_REDIRECT_URI = "YOUR_REGISTERED_REDIRECT_URI"
```

The redirect URI must exactly match the callback URL configured in the Threads API settings in the Meta developer dashboard.

## 1. Build Authorization URL

```powershell
.\threads-build-auth-url.ps1 -Open
```

Python alternative:

```powershell
python .\threads_auto_upload.py auth-url
```

Authorize the app in the browser. After approval, Threads redirects to your redirect URI with a `code=...` query parameter.

Copy the `code` value quickly. Authorization codes expire quickly.

## 2. Exchange Code For Short-Lived Token

```powershell
.\threads-exchange-code.ps1 -Code "CODE_FROM_REDIRECT_URL"
```

Python alternative:

```powershell
python .\threads_auto_upload.py exchange-code --code "CODE_FROM_REDIRECT_URL"
```

The response should include:

```json
{
  "access_token": "...",
  "user_id": "..."
}
```

Set:

```powershell
$env:THREADS_SHORT_LIVED_ACCESS_TOKEN = "ACCESS_TOKEN_FROM_RESPONSE"
$env:THREADS_USER_ID = "USER_ID_FROM_RESPONSE"
```

## 3. Exchange For Long-Lived Token

```powershell
.\threads-exchange-long-lived-token.ps1
```

Python alternative:

```powershell
python .\threads_auto_upload.py long-token
```

The response should include a longer-lived `access_token`.

Set:

```powershell
$env:THREADS_ACCESS_TOKEN = "LONG_LIVED_ACCESS_TOKEN_FROM_RESPONSE"
```

`THREADS_USER_ID` is no longer required for publishing. The publisher verifies the current account through the token before posting.

## 4. Verify Account

```powershell
.\threads-get-me.ps1
```

Python alternative:

```powershell
python .\threads_auto_upload.py me
```

Confirm the returned `id` and `username` are the intended existing Threads account.

## 5. Dry Run Approved Post

Save the approved thread chain as:

```text
C:\Users\kym70\threads-agentic-editor-workflow\approved-thread-chain.txt
```

Then run:

```powershell
.\scripts\publish-approved-chain.ps1 -DryRun
```

Python alternative:

```powershell
python .\scripts\threads_auto_upload.py publish-approved-chain --dry-run
```

Check:

- Korean text is not broken.
- Post is not misleading.
- Source is included if needed.
- It is under 500 characters when possible.

## 6. Publish

```powershell
.\scripts\publish-approved-chain.ps1
```

Python alternative:

```powershell
python .\scripts\threads_auto_upload.py publish-approved-chain
```

The script uses the two-step Threads publishing flow:

1. `POST https://graph.threads.net/v1.0/{user-id}/threads`
2. `POST https://graph.threads.net/v1.0/{user-id}/threads_publish`

## Token Refresh

Refresh the long-lived token before it expires:

```powershell
.\threads-refresh-token.ps1
```

Then update:

```powershell
$env:THREADS_ACCESS_TOKEN = "NEW_ACCESS_TOKEN"
```

## Safety Rules

- Never put access tokens in the HTML console.
- Keep tokens in PowerShell environment variables only.
- Always run `-DryRun` before publishing.
- Do not auto-publish unreviewed AI-generated text.
- If a post contains facts, keep the source URL in the approved post or verify it manually.

## Current Source Basis

The Threads API launch and capabilities were announced publicly in June 2024. The publishing flow uses Threads Graph API under `graph.threads.net`, with a container creation step and a publish step. Current third-party docs and public examples continue to show the same two-step pattern with `threads_basic` and `threads_content_publish` scopes.
