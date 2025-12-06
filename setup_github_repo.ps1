# Script to set up GitHub repository for kobo-sentiment-analyzer
# Make sure you've created the repository on GitHub first at: https://github.com/VonBoyager/kobo-sentiment-analyzer

$repoName = "kobo-sentiment-analyzer"
$username = "VonBoyager"
$repoUrl = "https://github.com/$username/$repoName.git"

Write-Host "Setting up GitHub repository..." -ForegroundColor Green

# Check if remote already exists
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "Remote 'origin' already exists: $existingRemote" -ForegroundColor Yellow
    $response = Read-Host "Do you want to update it? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        git remote set-url origin $repoUrl
        Write-Host "Remote updated to: $repoUrl" -ForegroundColor Green
    } else {
        Write-Host "Keeping existing remote." -ForegroundColor Yellow
    }
} else {
    # Add remote origin
    git remote add origin $repoUrl
    Write-Host "Added remote origin: $repoUrl" -ForegroundColor Green
}

# Set main branch (if not already)
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    git branch -M main
    Write-Host "Renamed branch to 'main'" -ForegroundColor Green
} else {
    Write-Host "Already on 'main' branch" -ForegroundColor Green
}

# Push to GitHub
Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
Write-Host "You may be prompted for your GitHub credentials." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nRepository setup complete!" -ForegroundColor Green
    Write-Host "Your repository is now available at: https://github.com/$username/$repoName" -ForegroundColor Cyan
} else {
    Write-Host "`nPush failed. Please check:" -ForegroundColor Red
    Write-Host "1. The repository exists on GitHub" -ForegroundColor Yellow
    Write-Host "2. You have the correct permissions" -ForegroundColor Yellow
    Write-Host "3. Your GitHub credentials are correct" -ForegroundColor Yellow
}

