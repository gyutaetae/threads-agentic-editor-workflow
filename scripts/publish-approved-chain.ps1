param(
    [string]$ThreadPath = ".\approved-thread-chain.txt",
    [string]$Topic = "agent repo reading",
    [string]$Format = "A",
    [int]$SourceCount = 0,
    [switch]$CardUsed,
    [switch]$SkipQualityGate,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if (-not $SkipQualityGate) {
        python .\scripts\prepublish_quality_gate.py --thread-path $ThreadPath --strict
    }

    $argsList = @(
        ".\scripts\threads_auto_upload.py",
        "publish-approved-chain",
        "--thread-path", $ThreadPath,
        "--topic", $Topic,
        "--format", $Format,
        "--source-count", $SourceCount
    )

    if ($CardUsed) {
        $argsList += "--card-used"
    }

    if ($DryRun) {
        $argsList += "--dry-run"
    }

    python @argsList
}
finally {
    Pop-Location
}
