$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$source = Join-Path $repoRoot "skills\threads-agentic-editor"
$targetRoot = Join-Path $HOME ".codex\skills"
$target = Join-Path $targetRoot "threads-agentic-editor"

if (-not (Test-Path -LiteralPath $source)) {
    throw "Skill source not found: $source"
}

New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
}

Copy-Item -LiteralPath $source -Destination $targetRoot -Recurse -Force

Write-Host "Installed skill to $target"
Write-Host "Restart Codex if the skill does not appear immediately."

