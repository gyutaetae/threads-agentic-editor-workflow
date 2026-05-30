param(
    [string]$ThreadPath = ".\approved-thread-chain.txt",
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    $argsList = @(
        ".\scripts\prepublish_quality_gate.py",
        "--thread-path", $ThreadPath
    )

    if ($Strict) {
        $argsList += "--strict"
    }

    python @argsList
}
finally {
    Pop-Location
}
