# Stop Frontend and Backend Servers
# Usage: powershell -ExecutionPolicy Bypass -File scripts/stop_servers.ps1

Write-Host "=== Stopping DEAI Servers ===" -ForegroundColor Cyan

$backendPorts = @(8000, 8001, 8002)
$frontendPorts = @(5173, 5174, 5175, 5176, 5177)
$killedCount = 0
$currentPid = $PID

function Stop-ProcessOnPort {
    param([int]$Port)

    $connections = netstat -ano | Select-String ":$Port\s+" | Select-String "LISTENING"

    foreach ($conn in $connections) {
        if ($conn -match '\s+(\d+)\s*$') {
            $targetPid = [int]$Matches[1]
            if ($targetPid -ne 0 -and $targetPid -ne $script:currentPid) {
                try {
                    $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
                    if ($proc -and $proc.ProcessName -ne "powershell" -and $proc.ProcessName -ne "pwsh") {
                        Write-Host "  Killing $($proc.ProcessName) (PID: $targetPid) on port $Port" -ForegroundColor Yellow
                        Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
                        $script:killedCount++
                    }
                } catch {}
            }
        }
    }
}

Write-Host "`n[Backend] Checking ports: $($backendPorts -join ', ')" -ForegroundColor Green
foreach ($port in $backendPorts) {
    Stop-ProcessOnPort -Port $port
}

Write-Host "`n[Frontend] Checking ports: $($frontendPorts -join ', ')" -ForegroundColor Green
foreach ($port in $frontendPorts) {
    Stop-ProcessOnPort -Port $port
}

$pidFile = Join-Path $PSScriptRoot "..\.server.pid"
if (Test-Path $pidFile) {
    Remove-Item $pidFile -Force
    Write-Host "`n  Removed stale PID file" -ForegroundColor Gray
}

Write-Host "`n=== Done! Killed $killedCount process(es) ===" -ForegroundColor Cyan
