param(
    [Parameter(Mandatory = $true)][string]$PostId,
    [string]$Window = "manual",
    [string]$MetricsPath = ".\threads-post-metrics.csv",
    [int]$OwnReplies = -1
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $argsList = @(
        ".\scripts\threads_auto_upload.py",
        "collect-metrics",
        "--post-id", $PostId,
        "--window", $Window,
        "--metrics-path", $MetricsPath
    )

    if ($OwnReplies -ge 0) {
        $argsList += @("--own-replies", $OwnReplies)
    }

    python @argsList
}
finally {
    Pop-Location
}
