# copaw-dev.ps1 - 全局 CoPaw 开发命令
# 放置在 PATH 中，可从任意位置调用

param(
    [string]$ProjectPath = "D:\代码\thirdpart\copaw",
    [int]$Port = 1012,
    [string]$HostAddr = "127.0.0.1",
    [string]$Extras = "",
    [switch]$NoReinstall = $false,
    [switch]$NoRestart = $false,
    [switch]$Background = $false,
    [switch]$Stop = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host @"
CoPaw Development Helper

Usage: copaw-dev [options]

Options:
    -ProjectPath   CoPaw project path (default: D:\代码\thirdpart\copaw)
    -Port          Server port (default: 1012)
    -HostAddr      Server host (default: 127.0.0.1)
    -Extras        Extra dependencies, e.g. "dev,ollama"
    -NoReinstall   Skip pip install
    -NoRestart     Skip service restart
    -Background    Run in background
    -Stop          Only stop the service
    -Help          Show this help

Examples:
    copaw-dev                    # Full: reinstall + restart
    copaw-dev -NoReinstall       # Only restart (no reinstall)
    copaw-dev -Stop              # Only stop
    copaw-dev -Port 8080         # Use different port
    copaw-dev -Extras "dev,ollama"  # Install with extras

"@
    exit 0
}

$scriptsPath = Join-Path $ProjectPath "scripts"

# 检查脚本目录是否存在
if (-not (Test-Path $scriptsPath)) {
    Write-Host "ERROR: Scripts directory not found: $scriptsPath" -ForegroundColor Red
    Write-Host "Make sure ProjectPath is correct." -ForegroundColor Red
    exit 1
}

if ($Stop) {
    & "$scriptsPath\stop.ps1" -Port $Port
    exit $LASTEXITCODE
}

& "$scriptsPath\dev.ps1" `
    -Port $Port `
    -HostAddr $HostAddr `
    -Extras $Extras `
    -NoReinstall:$NoReinstall `
    -NoRestart:$NoRestart `
    -Background:$Background
