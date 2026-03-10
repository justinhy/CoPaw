# reinstall.ps1 - 重新安装 CoPaw (从源码)
param(
    [string]$Extras = "",  # 额外依赖，如 "dev,ollama"
    [switch]$Quiet = $false,
    [switch]$SkipFrontend = $false  # 跳过前端构建
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

Write-Host "Reinstalling CoPaw from source..." -ForegroundColor Cyan
Write-Host "  Project root: $projectRoot" -ForegroundColor Gray

# 切换到项目目录
Push-Location $projectRoot

try {
    # 构建安装命令
    $installCmd = "pip install -e ."
    if ($Extras) {
        $installCmd = "pip install -e `".[$Extras]`""
    }
    
    Write-Host "  Running: $installCmd" -ForegroundColor Gray
    Write-Host ""
    
    if ($Quiet) {
        $output = Invoke-Expression $installCmd 2>&1 | Out-Null
    } else {
        Invoke-Expression $installCmd
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Installation failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
    # 构建前端
    if (-not $SkipFrontend) {
        Write-Host ""
        Write-Host "Building frontend..." -ForegroundColor Yellow
        
        Push-Location "$projectRoot\console"
        try {
            if (-not (Test-Path "node_modules")) {
                Write-Host "  Installing npm dependencies..." -ForegroundColor Gray
                npm ci 2>&1 | Out-Null
            }
            Write-Host "  Running npm run build..." -ForegroundColor Gray
            npm run build 2>&1 | Out-Null
            
            # 复制 dist 到 src/copaw/console
            Write-Host "  Copying dist to src/copaw/console..." -ForegroundColor Gray
            $destDir = "$projectRoot\src\copaw\console"
            if (-not (Test-Path $destDir)) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
            Copy-Item -Path "$projectRoot\console\dist\*" -Destination $destDir -Recurse -Force
            
            Write-Host "  Frontend built successfully!" -ForegroundColor Green
        } finally {
            Pop-Location
        }
    }
    
    Write-Host ""
    Write-Host "CoPaw reinstalled successfully!" -ForegroundColor Green
    Write-Host "Run .\scripts\restart.ps1 to start the service." -ForegroundColor Cyan
    
} finally {
    Pop-Location
}
