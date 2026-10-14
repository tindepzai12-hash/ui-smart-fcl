param([string]$Python='', [switch]$NoBrowser)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $Python) {
  $pythonCommand=Get-Command python -ErrorAction SilentlyContinue
  if ($pythonCommand) { $Python=$pythonCommand.Source } else { $Python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
}
if (-not (Test-Path -LiteralPath $Python)) { throw 'Không tìm thấy Python; chạy với -Python đường dẫn python.exe.' }
try { $service=Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 2; if ($service.service -eq 'U&I SMART') { if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765' }; exit 0 } } catch {}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'dist\index.html'))) { throw 'Chưa có frontend build. Chạy setup.ps1 trước.' }
$argsForPython=@('-u',('"'+(Join-Path $PSScriptRoot 'run.py')+'"'))
$process=Start-Process -FilePath $Python -ArgumentList $argsForPython -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'local.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'local.stderr.log')
$process.Id | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'local.pid')
for ($attempt=0;$attempt -lt 30;$attempt++) {
  Start-Sleep -Milliseconds 500
  try { $service=Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 2; if ($service.ok) { Write-Host 'U&I SMART: http://127.0.0.1:8765'; if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8765' }; exit 0 } } catch {}
}
throw 'Backend chưa khởi động. Xem local.stderr.log và kiểm tra cổng 8765.'
