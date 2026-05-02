[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [string]$RepoRoot = "",
    [string]$RemoteName = "origin"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$resolvedRoot = (Resolve-Path $RepoRoot).Path
Set-Location $resolvedRoot

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Version must use semantic version format, for example 3.0.0"
}

if (-not (Test-Path ".git")) {
    throw "The target path is not a Git repository: $resolvedRoot"
}

$status = git status --short
if ($LASTEXITCODE -ne 0) {
    throw "git status failed."
}
if ($status) {
    throw "Working tree is not clean. Commit and push changes before creating a release tag."
}

$tagName = "v$Version"

$localTag = git tag --list $tagName
if ($LASTEXITCODE -ne 0) {
    throw "Failed to list local tags."
}
if ($localTag) {
    throw "Local tag already exists: $tagName"
}

git fetch $RemoteName --tags --prune
if ($LASTEXITCODE -ne 0) {
    throw "Failed to fetch remote tags."
}

$remoteTag = git ls-remote --tags $RemoteName $tagName
if ($LASTEXITCODE -ne 0) {
    throw "Failed to inspect remote tags."
}
if ($remoteTag) {
    throw "Remote tag already exists: $tagName"
}

git tag -a $tagName -m "Release $Version"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create tag: $tagName"
}

git push $RemoteName $tagName
if ($LASTEXITCODE -ne 0) {
    throw "Failed to push tag: $tagName"
}

Write-Host "Created and pushed release tag: $tagName"
Write-Host "GitHub Release workflow should start automatically."
