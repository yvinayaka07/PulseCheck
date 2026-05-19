# =============================================================================
# PulseCheck – Local CI/CD Pipeline Simulator (PowerShell)
# Usage: .\run-pipeline.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Green
Write-Host " 🩺 PulseCheck Local CI/CD Pipeline Simulator" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host ""

# ── Step 1: Unit & Endpoint Tests ───────────────────────────────────────────
Write-Host "[1/3] Running automated unit and integration tests..." -ForegroundColor Cyan
if (Test-Path .venv\Scripts\python.exe) {
    & .venv\Scripts\python.exe -m pytest tests/ --cov=app --cov-report=term-missing
} else {
    python -m pytest tests/ --cov=app --cov-report=term-missing
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests failed! Aborting pipeline." -ForegroundColor Red
    Exit 1
}
Write-Host "✅ All tests passed successfully!" -ForegroundColor Green
Write-Host ""

# ── Docker Check ─────────────────────────────────────────────────────────────
Write-Host "Checking local containerization environment..." -ForegroundColor Gray

$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerInstalled) {
    Write-Host "⚠️  Docker is not installed or not in system PATH." -ForegroundColor Yellow
    Write-Host "Skipping containerization steps. Install Docker to test multi-stage builds locally." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host " 🎉 Local Pipeline Passed (Tests Only - Docker Skipped)" -ForegroundColor Green
    Write-Host "====================================================" -ForegroundColor Green
    Exit 0
}

# Check if daemon is running
& docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Docker daemon is not running." -ForegroundColor Yellow
    Write-Host "Skipping containerization steps. Start Docker Desktop to test multi-stage builds locally." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host " 🎉 Local Pipeline Passed (Tests Only - Daemon Skipped)" -ForegroundColor Green
    Write-Host "====================================================" -ForegroundColor Green
    Exit 0
}

Write-Host "✅ Docker environment is available and healthy." -ForegroundColor Green
Write-Host ""

# ── Step 2: Build Container Image ────────────────────────────────────────────
Write-Host "[2/3] Building Docker container image (multi-stage)..." -ForegroundColor Cyan
docker build -t pulsecheck:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed! Aborting pipeline." -ForegroundColor Red
    Exit 1
}
Write-Host "✅ Docker image built successfully: pulsecheck:latest" -ForegroundColor Green
Write-Host ""

# ── Step 3: Containerized Smoke Test Deployment ──────────────────────────────
Write-Host "[3/3] Simulating smoke-test deployment..." -ForegroundColor Cyan

# Stop and remove existing container if it exists
Write-Host "Cleaning up any old smoke-test containers..." -ForegroundColor Gray
docker stop pulsecheck_smoke_test 2>$null | Out-Null
docker rm pulsecheck_smoke_test 2>$null | Out-Null

# Run new container
Write-Host "Launching containerized service in background..." -ForegroundColor Gray
docker run -d --name pulsecheck_smoke_test -p 8000:8000 -e APP_ENV=production pulsecheck:latest | Out-Null

# Wait for application startup
Write-Host "Waiting for service to boot (8 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Query application status
try {
    Write-Host "Sending HTTP probe to container health-check endpoint..." -ForegroundColor Gray
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    
    if ($response.status -eq "healthy") {
        Write-Host "✅ Smoke test passed successfully! Container responds correctly." -ForegroundColor Green
        Write-Host ""
        Write-Host "====================================================" -ForegroundColor Green
        Write-Host " 🎉 Local Pipeline Execution Completed Successfully!" -ForegroundColor Green
        Write-Host "====================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Response Payload:" -ForegroundColor Gray
        Write-Host (ConvertTo-Json $response -Depth 4) -ForegroundColor White
    } else {
        throw "Container status returned: $($response.status)"
    }
} catch {
    Write-Host "❌ Smoke test failed! Could not reach container or check failed." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Retrieving container logs for debugging:" -ForegroundColor Yellow
    docker logs pulsecheck_smoke_test
    docker stop pulsecheck_smoke_test | Out-Null
    docker rm pulsecheck_smoke_test | Out-Null
    Exit 1
}

# Clean up container
Write-Host ""
Write-Host "Cleaning up smoke-test container..." -ForegroundColor Gray
docker stop pulsecheck_smoke_test | Out-Null
docker rm pulsecheck_smoke_test | Out-Null
Write-Host "Cleanup complete. Project is healthy. 🚀" -ForegroundColor Green
