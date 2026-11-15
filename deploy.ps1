<#
.SYNOPSIS
    Automated Deployment Pipeline for VM2 (web-server - 192.168.56.21)
.DESCRIPTION
    Transfers custom monitoring scripts, Zabbix Agent 2 configurations, and test tools
    from Windows to Ubuntu Server 26.04 LTS via SCP, sanitizes line endings to LF,
    restarts zabbix-agent2, and verifies all 6 metric keys.
.PARAMETER TargetHost
    Target IPv4 address of VM2. Default: 192.168.56.21.
.PARAMETER User
    SSH username on VM2. Default: linux-moniter.
.PARAMETER KeyFile
    Optional path to private SSH key.
.PARAMETER SudoPassword
    Optional sudo password for non-interactive privilege escalation.
.PARAMETER Port
    SSH port. Default: 22.
#>
[CmdletBinding()]
param(
    [string]$TargetHost = "192.168.56.21",
    [string]$User = "linux-moniter",
    [string]$KeyFile = "",
    [string]$SudoPassword = "",
    [int]$Port = 22
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  Zabbix Automation - Automated Remote Deployer to VM2" -ForegroundColor Cyan
Write-Host "  Target Host: ${User}@${TargetHost}:${Port}" -ForegroundColor Cyan
Write-Host "=================================================================="

# 1. Validate Local Repository Files
$RequiredFiles = @(
    "scripts/nginx_custom_metrics.sh",
    "scripts/system_health_check.sh",
    "configs/custom_monitor.conf",
    "tests/simulate_incident.sh",
    "deploy.sh"
)

Write-Host "[1/4] Validating local project artifacts..." -ForegroundColor Yellow
foreach ($file in $RequiredFiles) {
    if (-not (Test-Path -Path $file)) {
        Write-Error "Missing required source file: $file"
        exit 1
    }
}
Write-Host "  -> All local source files verified." -ForegroundColor Green

# 2. Build SSH & SCP Base Arguments
$SshArgs = @("-p", "$Port", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=NUL", "-o", "BatchMode=yes")
$ScpArgs = @("-P", "$Port", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=NUL", "-o", "BatchMode=yes")

if ([string]::IsNullOrWhiteSpace($KeyFile)) {
    $DefaultKey = "$env:USERPROFILE\.ssh\id_ed25519"
    if (Test-Path $DefaultKey) {
        $KeyFile = $DefaultKey
    }
}

if (-not [string]::IsNullOrWhiteSpace($KeyFile)) {
    if (-not (Test-Path $KeyFile)) {
        Write-Error "Specified private key file does not exist: $KeyFile"
        exit 1
    }
    $SshArgs += @("-i", "$KeyFile")
    $ScpArgs += @("-i", "$KeyFile")
}

$RemoteTarget = "${User}@${TargetHost}"
$StagingDir = "/tmp/zabbix_deploy"

# 3. Create Remote Staging Directory and Sync Files
Write-Host "[2/4] Synchronizing files to VM2 staging directory ($StagingDir)..." -ForegroundColor Yellow

$RemoteMkdirCmd = "mkdir -p $StagingDir/scripts $StagingDir/configs $StagingDir/tests"
& ssh.exe @SshArgs $RemoteTarget $RemoteMkdirCmd
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to establish SSH connection to $RemoteTarget."
    exit 1
}

# Copy files
& scp.exe @ScpArgs "scripts/nginx_custom_metrics.sh" "${RemoteTarget}:${StagingDir}/scripts/"
& scp.exe @ScpArgs "scripts/system_health_check.sh" "${RemoteTarget}:${StagingDir}/scripts/"
& scp.exe @ScpArgs "configs/custom_monitor.conf" "${RemoteTarget}:${StagingDir}/configs/"
& scp.exe @ScpArgs "tests/simulate_incident.sh" "${RemoteTarget}:${StagingDir}/tests/"
& scp.exe @ScpArgs "deploy.sh" "${RemoteTarget}:${StagingDir}/"

if ($LASTEXITCODE -ne 0) {
    Write-Error "SCP file transfer encountered errors."
    exit 1
}
Write-Host "  -> All files successfully copied to VM2 staging." -ForegroundColor Green

# 4. Trigger Remote Installation & Verification
Write-Host "[3/4] Triggering remote execution of deploy.sh on VM2..." -ForegroundColor Yellow

if (-not [string]::IsNullOrWhiteSpace($SudoPassword)) {
    $RemoteRunCmd = "SUDO_PASS='$SudoPassword' bash $StagingDir/deploy.sh"
} else {
    $RemoteRunCmd = "bash $StagingDir/deploy.sh"
}

& ssh.exe @SshArgs $RemoteTarget $RemoteRunCmd
$DeployExitCode = $LASTEXITCODE

Write-Host "[4/4] Evaluating deployment outcome..." -ForegroundColor Yellow
if ($DeployExitCode -eq 0) {
    Write-Host "`n==================================================================" -ForegroundColor Green
    Write-Host "  SUCCESS: VM2 Extended Monitoring deployed & verified 100%!" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n==================================================================" -ForegroundColor Red
    Write-Host "  FAILURE: Remote deployment returned non-zero exit code: $DeployExitCode" -ForegroundColor Red
    Write-Host "==================================================================" -ForegroundColor Red
    exit $DeployExitCode
}
