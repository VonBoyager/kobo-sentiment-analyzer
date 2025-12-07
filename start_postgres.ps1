# Start PostgreSQL using Docker
Write-Host "Starting PostgreSQL database..." -ForegroundColor Cyan

# Check if Docker is running
$dockerRunning = docker info 2>$null
if (-not $dockerRunning) {
    Write-Host "Docker is not running. Starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "Waiting for Docker to start (30 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

# Navigate to the sentiment_analyzer directory where docker-compose.yml is located
Set-Location -Path "$PSScriptRoot\sentiment_analyzer"

# Start the PostgreSQL container
Write-Host "Starting PostgreSQL container..." -ForegroundColor Cyan
docker-compose up -d db

if ($LASTEXITCODE -eq 0) {
    Write-Host "PostgreSQL started successfully!" -ForegroundColor Green
    Write-Host "Database is available at localhost:5432" -ForegroundColor Green
} else {
    Write-Host "Failed to start PostgreSQL. Please check Docker." -ForegroundColor Red
}

# Return to the original directory
Set-Location -Path $PSScriptRoot

