[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$RemoteName = "origin",
    [string]$CommitMessagePrefix = "chore(sync): auto backup"
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args,
        [switch]$AllowFailure,
        [switch]$CaptureOutput
    )

    if ($CaptureOutput) {
        $output = & git @Args 2>&1
        $code = $LASTEXITCODE
    } else {
        & git @Args
        $code = $LASTEXITCODE
        $output = @()
    }

    if (-not $AllowFailure -and $code -ne 0) {
        $joined = $Args -join " "
        throw "git $joined failed with exit code $code."
    }

    return @{
        Code = $code
        Output = @($output)
    }
}

function Write-Step {
    param([string]$Message)
    Write-Host "[fx-git-sync] $Message"
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$resolvedRoot = (Resolve-Path $RepoRoot).Path
Set-Location $resolvedRoot

if (-not (Test-Path ".git")) {
    throw "The target path is not a Git repository: $resolvedRoot"
}

$branchResult = Invoke-Git -Args @("rev-parse", "--abbrev-ref", "HEAD") -CaptureOutput
$currentBranch = ($branchResult.Output | Select-Object -First 1).ToString().Trim()

if ([string]::IsNullOrWhiteSpace($currentBranch) -or $currentBranch -eq "HEAD") {
    throw "Auto sync requires a checked-out branch. Detached HEAD is not supported."
}

Write-Step "Repository: $resolvedRoot"
Write-Step "Branch: $currentBranch"

$statusResult = Invoke-Git -Args @("status", "--porcelain=v1", "--untracked-files=all") -CaptureOutput
$statusLines = @($statusResult.Output | Where-Object { $_.ToString().Trim() -ne "" })
$hasChanges = $statusLines.Count -gt 0

if ($hasChanges) {
    Write-Step "Staging local changes..."
    Invoke-Git -Args @("add", "-A") | Out-Null

    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss K")
    $commitMessage = "$CommitMessagePrefix $timestamp"

    Write-Step "Creating commit: $commitMessage"
    Invoke-Git -Args @("commit", "-m", $commitMessage) | Out-Null
} else {
    Write-Step "No local changes detected."
}

Write-Step "Fetching remote state..."
Invoke-Git -Args @("fetch", $RemoteName, "--prune") | Out-Null

$upstreamResult = Invoke-Git -Args @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}") -CaptureOutput -AllowFailure
$hasUpstream = $upstreamResult.Code -eq 0

if ($hasUpstream) {
    $remoteRef = ($upstreamResult.Output | Select-Object -First 1).ToString().Trim()
    Write-Step "Upstream: $remoteRef"

    $distanceResult = Invoke-Git -Args @("rev-list", "--left-right", "--count", "HEAD...$remoteRef") -CaptureOutput
    $counts = ($distanceResult.Output | Select-Object -First 1).ToString().Trim() -split "\s+"
    $ahead = [int]$counts[0]
    $behind = [int]$counts[1]

    if ($behind -gt 0) {
        Write-Step "Remote is ahead by $behind commit(s). Rebasing before push..."
        Invoke-Git -Args @("pull", "--rebase", $RemoteName, $currentBranch) | Out-Null
    }

    if ($ahead -gt 0 -or $hasChanges -or $behind -gt 0) {
        Write-Step "Pushing branch to GitHub..."
        Invoke-Git -Args @("push") | Out-Null
    } else {
        Write-Step "Branch is already up to date."
    }
} else {
    Write-Step "No upstream configured. Creating origin/$currentBranch..."
    Invoke-Git -Args @("push", "--set-upstream", $RemoteName, $currentBranch) | Out-Null
}

Write-Step "Sync completed."
