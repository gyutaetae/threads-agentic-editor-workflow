param(
    [string]$ThreadPath = ".\approved-thread-chain.txt",
    [string]$Topic = "research ai workflow",
    [string]$Format = "A",
    [int]$SourceCount = 0,
    [string]$SourceName = "",
    [string]$SourceUrl = "",
    [string]$Series = "",
    [string]$SeriesPart = "",
    [string]$PublicTheme = "",
    [string]$TopicPillar = "",
    [string]$WorkflowStage = "",
    [string]$FailureMode = "",
    [string]$SolutionPattern = "",
    [string]$BadRequest = "",
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
        "--source-count", $SourceCount,
        "--source-name", $SourceName,
        "--source-url", $SourceUrl,
        "--series", $Series,
        "--series-part", $SeriesPart,
        "--public-theme", $PublicTheme,
        "--topic-pillar", $TopicPillar,
        "--workflow-stage", $WorkflowStage,
        "--failure-mode", $FailureMode,
        "--solution-pattern", $SolutionPattern,
        "--bad-request", $BadRequest
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
