param(
    [switch]$OpenBrowser,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$PidFile = Join-Path $RootDir ".localhost-pids.json"

$BackendUrl = "http://localhost:8000/health"
$FrontendUrl = "http://localhost:3000/login"

function Test-Url {
    param([string]$Url)

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500)
    }
    catch {
        return $false
    }
}

function Stop-RecordedProcesses {
    if (-not (Test-Path $PidFile)) {
        Write-Host "No recorded localhost processes found."
        return
    }

    $records = Get-Content $PidFile -Raw | ConvertFrom-Json
    foreach ($record in @($records.backend, $records.frontend)) {
        if ($null -ne $record -and $record.pid) {
            $process = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
            if ($process) {
                Stop-Process -Id $record.pid -Force
                Write-Host "Stopped process $($record.pid)."
            }
        }
    }

    Remove-Item $PidFile -Force
}

function Start-HiddenPowerShell {
    param(
        [string]$WorkingDirectory,
        [string]$Command
    )

    return Start-Process `
        -FilePath "powershell.exe" `
        -WindowStyle Hidden `
        -PassThru `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Set-Location -LiteralPath '$WorkingDirectory'; $Command"
        )
}

function Wait-ForUrl {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Url $Url) {
            Write-Host "$Name is ready: $Url"
            return $true
        }
        Start-Sleep -Seconds 2
    }

    Write-Host "$Name did not respond within $TimeoutSeconds seconds: $Url"
    return $false
}

if ($Stop) {
    Stop-RecordedProcesses
    exit 0
}

if (-not (Test-Path (Join-Path $BackendDir ".venv\Scripts\python.exe"))) {
    throw "Backend virtual environment not found at backend\.venv. Create/install backend dependencies first."
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    throw "Frontend node_modules not found. Run npm install in the frontend folder first."
}

$backendProcess = $null
$frontendProcess = $null

if (Test-Url $BackendUrl) {
    Write-Host "Backend is already running: $BackendUrl"
}
else {
    Write-Host "Starting backend on http://localhost:8000 ..."
    $backendProcess = Start-HiddenPowerShell `
        -WorkingDirectory $BackendDir `
        -Command "`$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
}

if (Test-Url $FrontendUrl) {
    Write-Host "Frontend is already running: $FrontendUrl"
}
else {
    Write-Host "Starting frontend on http://localhost:3000 ..."
    $frontendProcess = Start-HiddenPowerShell `
        -WorkingDirectory $FrontendDir `
        -Command "npm run dev"
}

$backendReady = Wait-ForUrl -Name "Backend" -Url $BackendUrl
$frontendReady = Wait-ForUrl -Name "Frontend" -Url $FrontendUrl

$records = [ordered]@{
    backend = if ($backendProcess) { @{ pid = $backendProcess.Id; started_at = (Get-Date).ToString("o") } } else { $null }
    frontend = if ($frontendProcess) { @{ pid = $frontendProcess.Id; started_at = (Get-Date).ToString("o") } } else { $null }
}
$records | ConvertTo-Json -Depth 4 | Set-Content -Path $PidFile -Encoding UTF8

Write-Host ""
if ($backendReady -and $frontendReady) {
    Write-Host "DataGov localhost is active."
    Write-Host "Frontend: $FrontendUrl"
    Write-Host "Backend:  $BackendUrl"
    Write-Host "Login with your configured DataGov account."
}
else {
    Write-Host "One or more services did not become ready. Check backend/frontend logs if the page does not load."
}

if ($OpenBrowser -and $frontendReady) {
    Start-Process $FrontendUrl
}
