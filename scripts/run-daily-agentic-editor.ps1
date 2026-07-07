param(
    [int]$PerQuery = 5,
    [int]$PerFeed = 5,
    [int]$ReadmeTop = 5,
    [switch]$AllowEmpty,
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $args = @(
        ".\scripts\agentic_daily_pipeline.py",
        "--per-query", $PerQuery,
        "--per-feed", $PerFeed,
        "--readme-top", $ReadmeTop,
        "--date", $Date
    )
    if ($AllowEmpty) {
        $args += "--allow-empty"
    }
    python @args
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Next:"
Write-Host "1. Open .\daily-editor\$Date-brief.md"
Write-Host "2. Open .\daily-editor\$Date-draft-prompt.md"
Write-Host "3. Ask Codex to run that prompt."
Write-Host "4. Approve one draft, then save it to .\approved-thread-chain.txt"
