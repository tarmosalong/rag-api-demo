# Start rag-api-demo in offline mode (no xAI). UI: http://127.0.0.1:8765/
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$py = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

$env:RAG_OFFLINE = "1"
if (-not $env:RAG_AUTO_SEED_OFFLINE) { $env:RAG_AUTO_SEED_OFFLINE = "true" }
if (-not $env:RAG_OFFLINE_MODE) { $env:RAG_OFFLINE_MODE = "retrieve" }

Write-Host "RAG_OFFLINE=1 - UI http://127.0.0.1:8765/ (Ctrl+C to stop)"
& $py -m uvicorn src.main:app --host 127.0.0.1 --port 8765 --reload