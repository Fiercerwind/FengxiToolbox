[CmdletBinding()]
param(
    [string]$TaskName = "FengxiToolbox Auto Sync to GitHub",
    [string]$DailyAt = "21:30",
    [string]$RepoRoot = "",
    [switch]$RunAtLogon
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$resolvedRoot = (Resolve-Path $RepoRoot).Path
$syncScript = Join-Path $PSScriptRoot "fx_git_sync.ps1"

if (-not (Test-Path $syncScript)) {
    throw "Missing sync script: $syncScript"
}

$triggerTime = [datetime]::ParseExact($DailyAt, "HH:mm", $null)
$taskUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-WindowStyle", "Hidden",
    "-File", "`"$syncScript`"",
    "-RepoRoot", "`"$resolvedRoot`""
) -join " "

$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument $arguments
$triggers = @(
    New-ScheduledTaskTrigger -Daily -At $triggerTime
)

if ($RunAtLogon) {
    $triggers += New-ScheduledTaskTrigger -AtLogOn
}

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

$principal = New-ScheduledTaskPrincipal -UserId $taskUser -LogonType Interactive -RunLevel Limited

$description = "Auto-commit and push FengxiToolbox changes to GitHub for rollback safety."

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Principal $principal `
    -Description $description `
    -Force | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName

Write-Host "Registered scheduled task: $($task.TaskName)"
Write-Host "User: $taskUser"
Write-Host "Daily at: $DailyAt"
Write-Host "Next run time: $($info.NextRunTime)"
if ($RunAtLogon) {
    Write-Host "Additional trigger: At logon"
}
