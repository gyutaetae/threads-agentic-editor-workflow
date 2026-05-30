param(
    [Parameter(Mandatory = $true)][string]$PostId,
    [string]$Window = "manual",
    [string]$MetricsPath = ".\threads-post-metrics.csv"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    python .\scripts\threads_auto_upload.py collect-metrics `
        --post-id $PostId `
        --window $Window `
        --metrics-path $MetricsPath
}
finally {
    Pop-Location
}
