# Start rag-api-demo in offline mode (no xAI). UI: http://127.0.0.1:8765/
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

$env:RAG_OFFLINE = "1"
if (-not $env:RAG_AUTO_SEED_OFFLINE) { $env:RAG_AUTO_SEED_OFFLINE = "true" }
if (-not $env:RAG_OFFLINE_MODE) { $env:RAG_OFFLINE_MODE = "retrieve" }

$onWindows = ($IsWindows -or $env:OS -eq "Windows_NT")
if ($env:PORT) {
    $port = $env:PORT
} elseif ($onWindows) {
    $port = "18765"
} else {
    $port = "8765"
}

$reload = if ($env:UVICORN_RELOAD -eq "0") { @() } else { @("--reload") }

Write-Host "RAG_OFFLINE=1 - UI http://127.0.0.1:$port/ (Ctrl+C to stop)"
if ($port -eq "8765" -and $onWindows) {
    Write-Host "If WinError 10013, set PORT=18765 (default on Windows is 18765)."
}
& $py -m uvicorn src.main:app --host 127.0.0.1 --port $port @reload