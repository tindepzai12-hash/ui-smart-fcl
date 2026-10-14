param([Parameter(Mandatory=$true)][string]$Archive,[string]$Python='python')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
& $Python (Join-Path $PSScriptRoot 'scripts\restore.py') $Archive
if ($LASTEXITCODE -ne 0) { throw 'Khôi phục thất bại. Dữ liệu cũ được giữ nguyên.' }
