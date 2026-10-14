$ErrorActionPreference='Stop'
$pidFile=Join-Path $PSScriptRoot 'local.pid'
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Host 'Không có PID do script này tạo.'; exit 0 }
$localServiceId=[int](Get-Content -LiteralPath $pidFile)
$proc=Get-CimInstance Win32_Process -Filter "ProcessId=$localServiceId" -ErrorAction SilentlyContinue
$expectedScript=Join-Path $PSScriptRoot 'run.py'
if ($proc -and $proc.CommandLine.Contains($expectedScript)) { Stop-Process -Id $localServiceId; Write-Host 'Đã dừng backend của dự án.' }
Remove-Item -LiteralPath $pidFile
