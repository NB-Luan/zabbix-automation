<#
.SYNOPSIS
    Automated Deployment Pipeline for VM2 (web-server - 192.168.56.21)
.DESCRIPTION
    Transfers custom monitoring scripts, Zabbix Agent 2 configurations, and test tools
    from Windows to Ubuntu Server via SCP, sanitizes line endings to LF,
    restarts zabbix-agent2, and verifies all 6 metric keys.
.PARAMETER TargetHost
    Target IPv4 address of VM2. Default: 192.168.56.21 (or $env:WEB_SERVER_IP).
.PARAMETER User
    SSH username on VM2. Default: linux-moniter (or $env:WEB_SERVER_USER).
.PARAMETER KeyFile
    Optional path to private SSH key.
.PARAMETER SudoPassword
    Optional sudo password for non-interactive privilege escalation.
.PARAMETER Port
    SSH port. Default: 22 (or $env:WEB_SERVER_PORT).
#>
[CmdletBinding()]
param(
    [string]$TargetHost = "",
    [string]$User = "",
    [string]$KeyFile = "",
    [string]$SudoPassword = "",
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"

# 1. Load .env Configuration if present in project root
$ProjectRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Get-Location).Path
}

$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not ($line.StartsWith("#")) -and ($line -match "^([^=]+)=(.*)$")) {
            $key = $matches[1].Trim()
            $val = $matches[2].Trim().Trim('"').Trim("'")
            if (-not [System.Environment]::GetEnvironmentVariable($key)) {
                [System.Environment]::SetEnvironmentVariable($key, $val)
            }
        }
    }
}

# Resolve defaults from environment or fallback constants
if ([string]::IsNullOrWhiteSpace($TargetHost)) {
    $TargetHost = if ($env:WEB_SERVER_IP) { $env:WEB_SERVER_IP } else { "192.168.56.21" }
}
if ([string]::IsNullOrWhiteSpace($User)) {
    $User = if ($env:WEB_SERVER_USER) { $env:WEB_SERVER_USER } else { "linux-moniter" }
}
if ($Port -eq 0) {
    $Port = if ($env:WEB_SERVER_PORT) { [int]$env:WEB_SERVER_PORT } else { 22 }
}
if ([string]::IsNullOrWhiteSpace($KeyFile)) {
    if ($env:SSH_KEY_FILE -and (Test-Path $env:SSH_KEY_FILE)) {
        $KeyFile = $env:SSH_KEY_FILE
    } else {
        $EdKey = Join-Path $env:USERPROFILE ".ssh\id_ed25519"
        $RsaKey = Join-Path $env:USERPROFILE ".ssh\id_rsa"
        if (Test-Path $EdKey) {
            $KeyFile = $EdKey
        } elseif (Test-Path $RsaKey) {
            $KeyFile = $RsaKey
        }
    }
}

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  Zabbix Automation - Automated Remote Deployer to VM2" -ForegroundColor Cyan
Write-Host "  Target Host: ${User}@${TargetHost}:${Port}" -ForegroundColor Cyan
Write-Host "=================================================================="

# 2. Validate Local Repository Files
$RequiredFiles = @(
    "scripts/nginx_custom_metrics.sh",
    "scripts/system_health_check.sh",
    "configs/custom_monitor.conf",
    "tests/simulate_incident.sh",
    "deploy.sh"
)

Write-Host "[1/4] Validating local project artifacts..." -ForegroundColor Yellow
foreach ($file in $RequiredFiles) {
    $filePath = Join-Path $ProjectRoot $file
    if (-not (Test-Path -Path $filePath)) {
        Write-Error "Missing required source file: $file"
        exit 1
    }
}
Write-Host "  -> All local source files verified." -ForegroundColor Green

# 3. Build SSH & SCP Base Arguments
$SshArgs = @("-p", "$Port", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=NUL", "-o", "BatchMode=yes")
$ScpArgs = @("-P", "$Port", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=NUL", "-o", "BatchMode=yes")

if (-not [string]::IsNullOrWhiteSpace($KeyFile)) {
    if (Test-Path $KeyFile) {
        $SshArgs += @("-i", "$KeyFile")
        $ScpArgs += @("-i", "$KeyFile")
    }
}

$RemoteTarget = "${User}@${TargetHost}"
$StagingDir = "/tmp/zabbix_deploy"

# 4. Create Remote Staging Directory and Sync Files
Write-Host "[2/4] Synchronizing files to VM2 staging directory ($StagingDir)..." -ForegroundColor Yellow

$RemoteMkdirCmd = "mkdir -p $StagingDir/scripts $StagingDir/configs $StagingDir/tests"
& ssh.exe @SshArgs $RemoteTarget $RemoteMkdirCmd
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to establish SSH connection to $RemoteTarget. Check network or SSH key/password."
    exit 1
}

# Copy files
& scp.exe @ScpArgs (Join-Path $ProjectRoot "scripts/nginx_custom_metrics.sh") "${RemoteTarget}:${StagingDir}/scripts/"
& scp.exe @ScpArgs (Join-Path $ProjectRoot "scripts/system_health_check.sh") "${RemoteTarget}:${StagingDir}/scripts/"
& scp.exe @ScpArgs (Join-Path $ProjectRoot "configs/custom_monitor.conf") "${RemoteTarget}:${StagingDir}/configs/"
& scp.exe @ScpArgs (Join-Path $ProjectRoot "tests/simulate_incident.sh") "${RemoteTarget}:${StagingDir}/tests/"
& scp.exe @ScpArgs (Join-Path $ProjectRoot "deploy.sh") "${RemoteTarget}:${StagingDir}/"

if ($LASTEXITCODE -ne 0) {
    Write-Error "SCP file transfer encountered errors."
    exit 1
}
Write-Host "  -> All files successfully copied to VM2 staging." -ForegroundColor Green

# 5. Trigger Remote Installation & Verification
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
