param(
    [string]$ThreadPath = ".\approved-thread-chain.txt",
    [string]$Topic = "agent repo reading",
    [string]$Format = "A",
    [string]$ContentAxis = "",
    [string]$FormatType = "",
    [string]$PostGoal = "",
    [string]$FinalCandidateScore = "",
    [string]$QualityScore = "",
    [string]$SourceType = "",
    [string]$PostSlot = "",
    [string]$ExperimentGroup = "",
    [string]$Model = "",
    [int]$SourceCount = 0,
    [string]$SourceName = "",
    [string]$SourceUrl = "",
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
        "--content-axis", $ContentAxis,
        "--format-type", $FormatType,
        "--post-goal", $PostGoal,
        "--final-candidate-score", $FinalCandidateScore,
        "--quality-score", $QualityScore,
        "--source-type", $SourceType,
        "--post-slot", $PostSlot,
        "--experiment-group", $ExperimentGroup,
        "--model", $Model,
        "--source-count", $SourceCount,
        "--source-name", $SourceName,
        "--source-url", $SourceUrl
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
