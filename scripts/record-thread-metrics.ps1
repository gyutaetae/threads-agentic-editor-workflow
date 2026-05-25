param(
    [Parameter(Mandatory = $true)][string]$Topic,
    [Parameter(Mandatory = $true)][string]$Hook,
    [string]$PostId = "",
    [string]$ThreadUrl = "",
    [string]$Format = "A",
    [int]$SourceCount = 0,
    [string]$CardUsed = "true",
    [int]$Views = 0,
    [int]$Likes = 0,
    [int]$Replies = 0,
    [int]$Reposts = 0,
    [int]$Quotes = 0,
    [int]$FollowsGained = 0,
    [string]$Notes = "",
    [string]$Path = ".\threads-post-metrics.csv"
)

$ErrorActionPreference = "Stop"

$cardUsedValue = $CardUsed -match "^(true|1|yes)$"

if (-not (Test-Path -LiteralPath $Path)) {
    "date,post_id,thread_url,format,topic,hook,source_count,card_used,posted_at,views,likes,replies,reposts,quotes,follows_gained,notes" |
        Set-Content -LiteralPath $Path -Encoding UTF8
}

$row = [pscustomobject]@{
    date = (Get-Date -Format "yyyy-MM-dd")
    post_id = $PostId
    thread_url = $ThreadUrl
    format = $Format
    topic = $Topic
    hook = $Hook
    source_count = $SourceCount
    card_used = $cardUsedValue
    posted_at = (Get-Date -Format "s")
    views = $Views
    likes = $Likes
    replies = $Replies
    reposts = $Reposts
    quotes = $Quotes
    follows_gained = $FollowsGained
    notes = $Notes
}

$row | Export-Csv -LiteralPath $Path -Append -NoTypeInformation -Encoding UTF8
Write-Host "Recorded metrics row in $Path"
