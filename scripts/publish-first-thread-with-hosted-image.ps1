param(
    [string]$AssetsPath = "",
    [string]$ThreadPath = "",
    [string]$AltText = "프로 개발자의 AI agent 작업법 카드",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $AssetsPath) {
    $AssetsPath = Join-Path $repoRoot "threads-hosted-assets.json"
}

if (-not $ThreadPath) {
    $ThreadPath = Join-Path $repoRoot "approved-thread-chain.txt"
}

if (-not (Test-Path -LiteralPath $AssetsPath)) {
    throw "$AssetsPath not found. Run .\upload-thread-image-github.ps1 first."
}

$assets = Get-Content -LiteralPath $AssetsPath -Raw | ConvertFrom-Json

$args = @(
    (Join-Path $PSScriptRoot "threads_auto_upload.py"),
    "publish-chain",
    "--thread-path",
    $ThreadPath,
    "--image-url",
    $assets.image_url,
    "--alt-text",
    $AltText
)

if ($DryRun) {
    $args += "--dry-run"
}

python @args
