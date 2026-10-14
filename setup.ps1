param([string]$Python='python')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) { throw 'Cài Python 3.11+ và thêm Python vào PATH, hoặc truyền -Python với đường dẫn python.exe.' }
& $Python -m pip install --target (Join-Path $PSScriptRoot 'vendor') -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Cài dependency Python thất bại.' }
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'dist\index.html'))) {
  & npm.cmd install --no-audit --no-fund
  if ($LASTEXITCODE -ne 0) { throw 'Cài dependency frontend thất bại.' }
  & node.exe (Join-Path $PSScriptRoot 'scripts\build.mjs')
  if ($LASTEXITCODE -ne 0) { throw 'Build frontend thất bại.' }
}
$langFolder=Join-Path $PSScriptRoot 'tools\tessdata'
New-Item -ItemType Directory -Force -Path $langFolder | Out-Null
foreach ($langName in @('eng','vie','osd')) {
  $langFile=Join-Path $langFolder "$langName.traineddata"
  if (-not (Test-Path -LiteralPath $langFile)) { Invoke-WebRequest -Uri "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/$langName.traineddata" -OutFile $langFile }
}
Write-Host 'Cài xong thư viện. OCR cần Tesseract executable: winget install UB-Mannheim.TesseractOCR'
Write-Host 'Chạy: .\start-local.ps1. Kiểm tra OCR tại Cài đặt; không cần OpenAI API key.'
