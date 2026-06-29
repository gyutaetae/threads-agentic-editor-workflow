param(
    [string]$ThreadPath = ".\approved-thread-chain.txt",
    [string]$Topic = "research ai workflow",
    [string]$Format = "A",
    [string]$ContentAxis = "",
    [string]$FormatType = "",
    [string]$PostGoal = "",
    [string]$FinalCandidateScore = "",
    [string]$QualityScore = "",
    [string]$SourceType = "",
    [string]$PostSlot = "",
    [string]$ExperimentGroup = "",
    [string]$Model = "",
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
    [switch]$QuoteUsed,
    [string]$QuoteId = "",
    [string]$QuoteSpeaker = "",
    [string]$QuoteSourceUrl = "",
    [string]$HumanSignalSource = "",
    [string]$HumanSignalType = "",
    [string]$ResearchProblem = "",
    [string]$HookPattern = "",
    [string]$StructurePattern = "",
    [string]$CloserPattern = "",
    [string]$ReusableUnitType = "",
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

    $argsList = @(".\scripts\threads_auto_upload.py", "publish-approved-chain")

    function Add-OptionalArg([string]$Name, [object]$Value) {
        if ($null -ne $Value -and [string]$Value -ne "") {
            $script:argsList += $Name
            $script:argsList += [string]$Value
        }
    }

    Add-OptionalArg "--thread-path" $ThreadPath
    Add-OptionalArg "--topic" $Topic
    Add-OptionalArg "--format" $Format
    Add-OptionalArg "--content-axis" $ContentAxis
    Add-OptionalArg "--format-type" $FormatType
    Add-OptionalArg "--post-goal" $PostGoal
    Add-OptionalArg "--final-candidate-score" $FinalCandidateScore
    Add-OptionalArg "--quality-score" $QualityScore
    Add-OptionalArg "--source-type" $SourceType
    Add-OptionalArg "--post-slot" $PostSlot
    Add-OptionalArg "--experiment-group" $ExperimentGroup
    Add-OptionalArg "--model" $Model
    Add-OptionalArg "--source-count" $SourceCount
    Add-OptionalArg "--source-name" $SourceName
    Add-OptionalArg "--source-url" $SourceUrl
    Add-OptionalArg "--series" $Series
    Add-OptionalArg "--series-part" $SeriesPart
    Add-OptionalArg "--public-theme" $PublicTheme
    Add-OptionalArg "--topic-pillar" $TopicPillar
    Add-OptionalArg "--workflow-stage" $WorkflowStage
    Add-OptionalArg "--failure-mode" $FailureMode
    Add-OptionalArg "--solution-pattern" $SolutionPattern
    Add-OptionalArg "--bad-request" $BadRequest
    Add-OptionalArg "--quote-id" $QuoteId
    Add-OptionalArg "--quote-speaker" $QuoteSpeaker
    Add-OptionalArg "--quote-source-url" $QuoteSourceUrl
    Add-OptionalArg "--human-signal-source" $HumanSignalSource
    Add-OptionalArg "--human-signal-type" $HumanSignalType
    Add-OptionalArg "--research-problem" $ResearchProblem
    Add-OptionalArg "--hook-pattern" $HookPattern
    Add-OptionalArg "--structure-pattern" $StructurePattern
    Add-OptionalArg "--closer-pattern" $CloserPattern
    Add-OptionalArg "--reusable-unit-type" $ReusableUnitType

    if ($CardUsed) {
        $argsList += "--card-used"
    }

    if ($QuoteUsed) {
        $argsList += "--quote-used"
    }

    if ($DryRun) {
        $argsList += "--dry-run"
    }

    python @argsList
}
finally {
    Pop-Location
}
