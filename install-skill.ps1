$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$targetRoot = Join-Path $HOME ".codex\skills"
$skills = @(
    "threads-agentic-editor",
    "threads-post-publisher"
)

New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null

foreach ($skill in $skills) {
    $source = Join-Path $repoRoot "skills\$skill"
    $target = Join-Path $targetRoot $skill

    if (-not (Test-Path -LiteralPath $source)) {
        throw "Skill source not found: $source"
    }

    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }

    Copy-Item -LiteralPath $source -Destination $targetRoot -Recurse -Force
    Write-Host "Installed skill to $target"
}

Write-Host "Restart Codex if updated skills do not appear immediately."
