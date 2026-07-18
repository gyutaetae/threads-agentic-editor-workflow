param(
    [string]$ThreadPath = ".\approved-thread-chain.txt",
    [string]$SpecPath = "",
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

    if ($SpecPath) {
        $argsList += @(
            "--spec-path", $SpecPath,
            "--require-metadata"
        )
    }

    if ($Strict) {
        $argsList += "--strict"
    }

    python @argsList
}
finally {
    Pop-Location
}
