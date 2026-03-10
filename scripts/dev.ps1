# dev.ps1 - CoPaw 开发流程（重装 + 重启）
param(
    [int]$Port = 1012,
    [string]$HostAddr = "127.0.0.1",
    [string]$Extras = "",          # 额外依赖，如 "dev,ollama"
    [switch]$NoReinstall = $false, # 跳过重装
    [switch]$NoRestart = $false,   # 跳过重启
    [switch]$Background = $false   # 后台运行
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CoPaw Development Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: 停止服务
if (-not $NoRestart) {
    Write-Host "[1/3] Stopping existing service..." -ForegroundColor Yellow
    & "$scriptDir\stop.ps1" -Port $Port
    Start-Sleep -Milliseconds 500
}

# Step 2: 重新安装
if (-not $NoReinstall) {
    Write-Host ""
    Write-Host "[2/3] Reinstalling from source..." -ForegroundColor Yellow
    & "$scriptDir\reinstall.ps1" -Extras $Extras -Quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Reinstall failed. Aborting." -ForegroundColor Red
        exit $LASTEXITCODE
    }
} else {
    Write-Host ""
    Write-Host "[2/3] Skipping reinstall (--no-reinstall)" -ForegroundColor Gray
}

# Step 3: 重启服务
if (-not $NoRestart) {
    Write-Host ""
    Write-Host "[3/3] Starting service..." -ForegroundColor Yellow
    & "$scriptDir\restart.ps1" -Port $Port -HostAddr $HostAddr -Background:$Background
} else {
    Write-Host ""
    Write-Host "[3/3] Skipping restart (--no-restart)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Done." -ForegroundColor Green
}
