$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

$pip = ".\.venv\Scripts\python.exe"
$pyVer = & $pip -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"

& $pip -m pip install -U pip

# Base deps (no chromadb — handled below for Windows wheel quirks)
$lines = Get-Content "requirements.txt" | Where-Object {
    $_ -notmatch '^\s*$' -and $_ -notmatch '^\s*#' -and $_ -notmatch '^chromadb'
}
$tempReq = Join-Path $env:TEMP "rag-api-demo-req.txt"
$lines | Set-Content $tempReq
& $pip -m pip install -r $tempReq
Remove-Item $tempReq

$onWindows = ($IsWindows -or $env:OS -eq "Windows_NT")

if ($onWindows -and $pyVer -eq "3.12") {
    Write-Host "Windows Python 3.12: using chroma-hnswlib 0.7.5 wheel (0.7.6 has no win wheel)."
    & $pip -m pip install "chroma-hnswlib==0.7.5"
    & $pip -m pip install "chromadb==0.5.23" --no-deps
    & $pip -m pip install -r requirements-chromadb-deps.txt
} else {
    & $pip -m pip install "chromadb==0.5.23"
}

Write-Host "OK: .venv (Python $pyVer)"
Write-Host "Start: .\scripts\dev-offline.ps1"