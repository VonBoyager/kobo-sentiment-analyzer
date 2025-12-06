# Kobo Sentiment Analyzer - Local Development Startup Script
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   Kobo Sentiment Analyzer - Local Development Setup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Step 1: Start PostgreSQL
Write-Host "`n[1/4] Starting PostgreSQL..." -ForegroundColor Yellow
& "$PSScriptRoot\start_postgres.ps1"

# Step 2: Activate virtual environment
Write-Host "`n[2/4] Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path "$PSScriptRoot\venv\Scripts\Activate.ps1") {
    & "$PSScriptRoot\venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv venv
    & "$PSScriptRoot\venv\Scripts\Activate.ps1"
    pip install -r requirements.txt
}

# Step 3: Run migrations and auto-load dataset
Write-Host "`n[3/4] Running migrations and loading data..." -ForegroundColor Yellow
Set-Location -Path "$PSScriptRoot\sentiment_analyzer"
python manage.py migrate

# Check if data exists, if not, auto-load dataset
$dataCount = python -c "import django; django.setup(); from ml_analysis.models import TrainingData; print(TrainingData.objects.count())" 2>$null
if ($dataCount -eq "0" -or -not $dataCount) {
    Write-Host "No data found. Auto-loading dataset..." -ForegroundColor Yellow
    python manage.py auto_load_dataset
}

# Step 4: Start Django server
Write-Host "`n[4/4] Starting Django development server..." -ForegroundColor Yellow
Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "   Server starting at http://localhost:8000" -ForegroundColor Green
Write-Host "   Admin panel at http://localhost:8000/admin" -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop the server" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green

python manage.py runserver

