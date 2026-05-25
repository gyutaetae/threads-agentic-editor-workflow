# Threads Image Hosting: GitHub Raw URL

This workflow turns a local card image into a public HTTPS URL that the Threads API can use.

## One-Time Setup

Recommended: use GitHub CLI browser login.

GitHub CLI is installed locally at:

```text
C:\Users\kym70\tools\gh\bin\gh.exe
```

Run:

```powershell
C:\Users\kym70\tools\gh\bin\gh.exe auth login -w
```

Choose:

```text
GitHub.com
HTTPS
Login with a web browser
```

Alternative: create a GitHub token:

1. Open GitHub Developer Settings.
2. Create a classic personal access token.
3. Give it `public_repo` permission for a public asset repo.
4. In PowerShell, set it only for the current terminal:

```powershell
$env:GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
```

Do not paste this token into chat.

## Upload Card Image

Preferred:

```powershell
.\upload-thread-image-gh.ps1
```

Token fallback:

```powershell
.\upload-thread-image-github.ps1
```

This creates or reuses a public repo named `threads-assets`, uploads:

```text
assets/threads-first-post-card.png
```

Then saves the public image URL to:

```text
threads-hosted-assets.json
```

## Test Publish With Image

```powershell
.\publish-first-thread-with-hosted-image.ps1 -DryRun
```

## Real Publish

Make sure these are already set:

```powershell
$env:THREADS_USER_ID = "YOUR_THREADS_USER_ID"
$env:THREADS_ACCESS_TOKEN = "YOUR_LONG_LIVED_THREADS_TOKEN"
```

Then run:

```powershell
.\publish-first-thread-with-hosted-image.ps1
```

The image is attached to the first post. The remaining parts in `approved-thread-chain.txt` are posted as replies.
