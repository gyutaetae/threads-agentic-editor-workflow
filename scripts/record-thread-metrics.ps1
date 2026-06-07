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
    [int]$ChainReplies = 0,
    [int]$OwnReplies = 0,
    [int]$AudienceReplies = -1,
    [int]$Reposts = 0,
    [int]$Quotes = 0,
    [int]$FollowsGained = 0,
    [string]$Notes = "",
    [string]$Path = ".\threads-post-metrics.csv"
)

$ErrorActionPreference = "Stop"

$cardUsedValue = $CardUsed -match "^(true|1|yes)$"

if (-not (Test-Path -LiteralPath $Path)) {
    "date,post_id,thread_url,format,topic,hook,source_count,card_used,posted_at,views,likes,replies,chain_replies,own_replies,audience_replies,reposts,quotes,follows_gained,notes" |
        Set-Content -LiteralPath $Path -Encoding UTF8
} else {
    $existingRows = @(Import-Csv -LiteralPath $Path)
    if ($existingRows.Count -gt 0 -and -not ($existingRows[0].PSObject.Properties.Name -contains "audience_replies")) {
        foreach ($existingRow in $existingRows) {
            foreach ($name in @("chain_replies", "own_replies", "audience_replies")) {
                if (-not ($existingRow.PSObject.Properties.Name -contains $name)) {
                    $existingRow | Add-Member -NotePropertyName $name -NotePropertyValue 0
                }
            }
            $existingReplies = if ($existingRow.replies) { [int]$existingRow.replies } else { 0 }
            $existingChainReplies = if ($existingRow.chain_replies) { [int]$existingRow.chain_replies } else { 0 }
            $existingOwnReplies = if ($existingRow.own_replies) { [int]$existingRow.own_replies } else { 0 }
            $existingRow.audience_replies = [Math]::Max($existingReplies - $existingChainReplies - $existingOwnReplies, 0)
        }
        $existingRows | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    }
}

if ($AudienceReplies -lt 0) {
    $AudienceReplies = [Math]::Max($Replies - $ChainReplies - $OwnReplies, 0)
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
    chain_replies = $ChainReplies
    own_replies = $OwnReplies
    audience_replies = $AudienceReplies
    reposts = $Reposts
    quotes = $Quotes
    follows_gained = $FollowsGained
    notes = $Notes
}

$row | Export-Csv -LiteralPath $Path -Append -NoTypeInformation -Encoding UTF8
Write-Host "Recorded metrics row in $Path"
