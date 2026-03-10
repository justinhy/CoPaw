# restart.ps1 - 重启 CoPaw 服务
param(
    [int]$Port = 1012,
    [string]$HostAddr = "127.0.0.1",
    [switch]$Background = $false
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$copawExe = "$env:APPDATA\Python\Python313\Scripts\copaw.exe"

# 检查 copaw 是否存在
if (-not (Test-Path $copawExe)) {
    # 尝试查找其他可能的路径
    $copawExe = Get-Command copaw -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $copawExe) {
        Write-Host "ERROR: copaw.exe not found. Run reinstall.ps1 first." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Restarting CoPaw..." -ForegroundColor Cyan
Write-Host "  Port: $Port" -ForegroundColor Gray
Write-Host "  Host: $HostAddr" -ForegroundColor Gray

# 停止现有服务
& "$scriptDir\stop.ps1" -Port $Port

# 等待端口释放
Start-Sleep -Milliseconds 500

# 启动服务
Write-Host "Starting CoPaw..." -ForegroundColor Yellow

if ($Background) {
    # 后台启动
    $job = Start-Job -ScriptBlock {
        param($copawExe, $HostAddr, $Port)
        & $copawExe app --host $HostAddr --port $Port 2>&1
    } -ArgumentList $copawExe, $HostAddr, $Port
    Write-Host "CoPaw started in background (Job ID: $($job.Id))" -ForegroundColor Green
    Write-Host "  Console: http://${HostAddr}:$Port/" -ForegroundColor Cyan
} else {
    # 前台启动
    Write-Host "  Console: http://${HostAddr}:$Port/" -ForegroundColor Cyan
    Write-Host "  Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host ""
    & $copawExe app --host $HostAddr --port $Port
}
