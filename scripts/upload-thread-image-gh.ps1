param(
    [string]$ImagePath = "",
    [string]$Repo = "threads-assets",
    [string]$AssetPath = "assets/threads-first-post-card.png",
    [string]$Branch = "main",
    [string]$OutputPath = ".\threads-hosted-assets.json"
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $ImagePath) {
    $ImagePath = Join-Path $repoRoot "threads-first-post-card.png"
}
if ($OutputPath -eq ".\threads-hosted-assets.json") {
    $OutputPath = Join-Path $repoRoot "threads-hosted-assets.json"
}

function Resolve-Gh {
    $command = Get-Command gh -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $localGh = Join-Path $HOME "tools\gh\bin\gh.exe"
    if (Test-Path -LiteralPath $localGh) {
        return $localGh
    }

    throw "GitHub CLI not found. Expected gh on PATH or at $localGh"
}

$gh = Resolve-Gh
$resolvedImage = Resolve-Path -LiteralPath $ImagePath

& $gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: $gh auth login -w"
}

$owner = (& $gh api user --jq ".login").Trim()
if (-not $owner) {
    throw "Could not read GitHub username from gh auth."
}

$token = (& $gh auth token).Trim()
if (-not $token) {
    throw "Could not read GitHub token from gh auth."
}

$headers = @{
    Authorization = "Bearer $token"
    Accept = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
    "User-Agent" = "threads-agent-publisher"
}

$repoJson = & $gh api "/repos/$owner/$Repo" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $gh repo create "$owner/$Repo" --public --description "Public image assets for Threads agent publishing workflow" --add-readme
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create GitHub repo $owner/$Repo"
    }
    Start-Sleep -Seconds 2
}

$encodedPath = ($AssetPath -split "/" | ForEach-Object { [uri]::EscapeDataString($_) }) -join "/"
$contentUri = "https://api.github.com/repos/$owner/$Repo/contents/$encodedPath"
$sha = $null
try {
    $existing = Invoke-RestMethod -Method Get -Uri "$contentUri`?ref=$Branch" -Headers $headers
    $sha = $existing.sha
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -ne 404) {
        throw
    }
}

$body = @{
    message = "Upload Threads card image"
    content = [Convert]::ToBase64String([IO.File]::ReadAllBytes($resolvedImage))
    branch = $Branch
}

if ($sha) {
    $body.sha = $sha
}

$json = $body | ConvertTo-Json -Depth 10 -Compress
Invoke-RestMethod -Method Put -Uri $contentUri -Headers $headers -Body $json -ContentType "application/json" | Out-Null

$rawUrl = "https://raw.githubusercontent.com/$owner/$Repo/$Branch/$AssetPath"
$result = [ordered]@{
    owner = $owner
    repo = $Repo
    branch = $Branch
    asset_path = $AssetPath
    image_path = $resolvedImage.Path
    image_url = $rawUrl
    uploaded_at = (Get-Date).ToString("s")
}

$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

Write-Host "Hosted image URL:"
Write-Host $rawUrl
Write-Host ""
Write-Host "Saved metadata to $OutputPath"
Write-Host ""
Write-Host "Dry-run Threads publish command:"
Write-Host ".\publish-first-thread-with-hosted-image.ps1 -DryRun"
