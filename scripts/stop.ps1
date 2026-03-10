# stop.ps1 - 停止 CoPaw 服务
param(
    [int]$Port = 1012
)

Write-Host "Stopping CoPaw on port $Port..." -ForegroundColor Yellow

# 查找占用端口的进程
$connections = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"
if ($connections) {
    foreach ($conn in $connections) {
        $pid = ($conn -split '\s+')[-1]
        if ($pid -match '^\d+$' -and $pid -ne '0') {
            Write-Host "  Killing process PID: $pid" -ForegroundColor Gray
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Write-Host "  Process $pid stopped." -ForegroundColor Green
            } catch {
                Write-Host "  Failed to stop process $pid : $_" -ForegroundColor Red
            }
        }
    }
} else {
    # 没有找到端口监听，尝试查找 copaw 进程
    $copawProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -like "*copaw*app*" }
    if ($copawProcesses) {
        foreach ($proc in $copawProcesses) {
            Write-Host "  Killing copaw process PID: $($proc.Id)" -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Host "  CoPaw processes stopped." -ForegroundColor Green
    } else {
        Write-Host "  No CoPaw process found on port $Port." -ForegroundColor Gray
    }
}

Write-Host "Done." -ForegroundColor Green
