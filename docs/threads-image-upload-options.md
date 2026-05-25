# Threads Image Auto-Upload Options

Threads API does not upload local image files directly.

To publish an image through API, the image must be available at a public HTTPS URL:

```text
media_type=IMAGE
image_url=https://...
alt_text=...
```

## Option A. Manual Image Attach First

Best for Day 1.

Workflow:

1. Generate `threads-first-post-card.png`.
2. Open Threads web/app.
3. Attach the image manually.
4. Paste the post text.

Pros:

- Fastest
- No hosting setup
- Best while testing content-market fit

Cons:

- Not fully automatic

## Option B. GitHub Pages

Good if you want free public image URLs.

Workflow:

1. Create a public GitHub repo, for example `threads-assets`.
2. Upload images to `/assets/`.
3. Enable GitHub Pages.
4. Use image URL like:

```text
https://YOUR_USERNAME.github.io/threads-assets/assets/threads-first-post-card.png
```

Pros:

- Free
- Simple
- Good enough for static cards

Cons:

- Public repo
- Requires git/GitHub setup

## Option B2. GitHub Raw URL

Fastest automated option for this workspace.

Workflow:

1. Create a GitHub token with `public_repo` permission.
2. Set it in PowerShell:

```powershell
$env:GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"
```

3. Upload the current card:

```powershell
.\upload-thread-image-gh.ps1
```

If you prefer token-only REST upload:

```powershell
.\upload-thread-image-github.ps1
```

4. Publish the thread chain with the hosted image:

```powershell
.\publish-first-thread-with-hosted-image.ps1 -DryRun
.\publish-first-thread-with-hosted-image.ps1
```

Pros:

- No GitHub CLI needed
- No GitHub Pages setup needed
- Produces a direct public HTTPS image URL

Cons:

- Public repo
- Needs one GitHub token

## Option C. Cloudflare R2

Best long-term.

Needed values:

```text
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_R2_BUCKET
CLOUDFLARE_R2_ACCESS_KEY_ID
CLOUDFLARE_R2_SECRET_ACCESS_KEY
PUBLIC_R2_BASE_URL
```

Pros:

- Clean automation
- Good for many images
- Public CDN URL

Cons:

- More setup

## Option D. Cloudinary

Good for quick media upload APIs.

Needed values:

```text
CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET
```

Pros:

- Easy image upload API
- Returns public HTTPS URL

Cons:

- Third-party dependency
- Free tier limits

## Current Script Support

`threads_auto_upload.py` now supports image URL publishing:

```powershell
python .\threads_auto_upload.py publish `
  --image-url "https://PUBLIC_IMAGE_URL.png" `
  --alt-text "프로 개발자의 AI agent 작업법 카드"
```

For a reply chain with the image attached to the first post:

```powershell
python .\threads_auto_upload.py publish-chain `
  --thread-path .\approved-thread-chain.txt `
  --image-url "https://PUBLIC_IMAGE_URL.png" `
  --alt-text "프로 개발자의 AI agent 작업법 카드"
```

Use dry run first:

```powershell
python .\threads_auto_upload.py publish-chain --dry-run
```

## Recommendation

For Day 1:

- manually attach `threads-first-post-card.png`
- use `approved-thread-chain.txt` as the reply chain text

After Day 1:

- set up GitHub Pages or Cloudinary
- publish image posts via API
