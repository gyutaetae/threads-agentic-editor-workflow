param(
    [string]$PostId = "",
    [string]$ThreadUrl = "",
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [int]$Views = -1,
    [int]$Likes = -1,
    [int]$Replies = -1,
    [int]$Reposts = -1,
    [int]$Quotes = -1,
    [int]$FollowsGained = -1,
    [string]$Notes = "",
    [string]$Path = ".\threads-post-metrics.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Path)) {
    throw "$Path not found. Record the post first with .\record-thread-metrics.ps1"
}

$rows = @(Import-Csv -LiteralPath $Path)
if ($rows.Count -eq 0) {
    throw "$Path has no rows to update."
}

$targetIndex = -1
for ($i = $rows.Count - 1; $i -ge 0; $i--) {
    $row = $rows[$i]
    $matchesPost = $PostId -and $row.post_id -eq $PostId
    $matchesUrl = $ThreadUrl -and $row.thread_url -eq $ThreadUrl
    $matchesDate = (-not $PostId) -and (-not $ThreadUrl) -and $row.date -eq $Date
    if ($matchesPost -or $matchesUrl -or $matchesDate) {
        $targetIndex = $i
        break
    }
}

if ($targetIndex -lt 0) {
    throw "No matching metrics row found. Pass -PostId, -ThreadUrl, or -Date."
}

$target = $rows[$targetIndex]
if ($PostId) { $target.post_id = $PostId }
if ($ThreadUrl) { $target.thread_url = $ThreadUrl }
if ($Views -ge 0) { $target.views = $Views }
if ($Likes -ge 0) { $target.likes = $Likes }
if ($Replies -ge 0) { $target.replies = $Replies }
if ($Reposts -ge 0) { $target.reposts = $Reposts }
if ($Quotes -ge 0) { $target.quotes = $Quotes }
if ($FollowsGained -ge 0) { $target.follows_gained = $FollowsGained }
if ($Notes) {
    $target.notes = (($target.notes, $Notes) | Where-Object { $_ }) -join " | "
}

$rows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
Write-Host "Updated metrics row $($targetIndex + 1) in $Path"
