$root = Split-Path -Parent $PSScriptRoot

$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  Write-Error "Backend virtual environment not found. Run the backend setup from README.md first."
  exit 1
}

Start-Process -FilePath $python -ArgumentList "-m","uvicorn","app.main:app","--reload","--port","8000" -WorkingDirectory $backend -WindowStyle Hidden
Start-Process -FilePath "npm.cmd" -ArgumentList "run","dev","--","--port","3000" -WorkingDirectory $frontend -WindowStyle Hidden

Write-Host "Started DataGov backend on http://localhost:8000"
Write-Host "Started DataGov frontend on http://localhost:3000"

