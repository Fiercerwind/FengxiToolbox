[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [ValidateRange(1, 100)]
    [int]$SyncEvery = 5,
    [string]$StatePath = ""
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[fx-package-sync] $Message"
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$resolvedRoot = (Resolve-Path $RepoRoot).Path
$syncScript = Join-Path $PSScriptRoot "fx_git_sync.ps1"
if (-not (Test-Path $syncScript)) {
    throw "Missing GitHub sync script: $syncScript"
}

if ([string]::IsNullOrWhiteSpace($StatePath)) {
    $stateDirectory = Join-Path $env:LOCALAPPDATA "FengxiToolbox"
    $StatePath = Join-Path $stateDirectory "package-sync-state.json"
} else {
    $stateDirectory = Split-Path -Parent $StatePath
}

if (-not (Test-Path $stateDirectory)) {
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
}

$state = [ordered]@{
    successfulPackageCount = 0
    syncEvery = $SyncEvery
}

if (Test-Path $StatePath) {
    try {
        $saved = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
        if ($null -ne $saved.successfulPackageCount) {
            $state.successfulPackageCount = [Math]::Max(0, [int]$saved.successfulPackageCount)
        }
    } catch {
        Write-Step "Ignoring unreadable sync counter and starting from zero."
    }
}

$state.syncEvery = $SyncEvery
$state.successfulPackageCount++
$state | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding UTF8

if ($state.successfulPackageCount -lt $SyncEvery) {
    Write-Step "Successful packages since last GitHub sync: $($state.successfulPackageCount)/$SyncEvery"
    exit 0
}

Write-Step "Reached $($state.successfulPackageCount) successful packages. Syncing GitHub..."
try {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $syncScript -RepoRoot $resolvedRoot
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub sync exited with code $LASTEXITCODE."
    }

    $state.successfulPackageCount = 0
    $state | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding UTF8
    Write-Step "GitHub sync completed. Counter reset to 0/$SyncEvery."
} catch {
    $state | ConvertTo-Json | Set-Content -LiteralPath $StatePath -Encoding UTF8
    Write-Warning "GitHub sync failed. The counter remains at $($state.successfulPackageCount), so the next successful package will retry. $($_.Exception.Message)"
}
