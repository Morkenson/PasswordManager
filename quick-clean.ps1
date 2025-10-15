# Quick Clean Script for Password Manager
# This removes all git history and creates a fresh, clean repository

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Password Manager - Quick Clean Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Confirm
Write-Host "WARNING: This will remove all git history!" -ForegroundColor Yellow
Write-Host "Make sure you have:" -ForegroundColor Yellow
Write-Host "  1. Changed your database password" -ForegroundColor Yellow
Write-Host "  2. Regenerated your Duo API keys" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Continue? (type 'YES' to proceed)"
if ($confirm -ne "YES") {
    Write-Host "Aborted." -ForegroundColor Red
    exit
}

# Step 2: Make backup
Write-Host ""
Write-Host "Creating backup..." -ForegroundColor Green
cd ..
Copy-Item -Recurse PasswordManager PasswordManager-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')
cd PasswordManager

# Step 3: Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Create your .env file first with NEW credentials." -ForegroundColor Red
    Write-Host "Copy env.example to .env and fill in your NEW credentials." -ForegroundColor Red
    exit
}

# Step 4: Remove git history
Write-Host ""
Write-Host "Removing old git history..." -ForegroundColor Green
Remove-Item -Recurse -Force .git

# Step 5: Initialize new repository
Write-Host "Initializing fresh repository..." -ForegroundColor Green
git init
git add .
git commit -m "Security: Clean repository with environment variables

- Removed all hardcoded credentials
- Implemented environment variable configuration  
- Added comprehensive security documentation
- Updated .gitignore to prevent sensitive data commits"

# Step 6: Connect to GitHub
Write-Host ""
Write-Host "Connecting to GitHub..." -ForegroundColor Green
git remote add origin https://github.com/Morkenson/PasswordManager.git
git branch -M main

# Step 7: Show what will be pushed
Write-Host ""
Write-Host "Files to be pushed:" -ForegroundColor Cyan
git ls-files

# Step 8: Confirm push
Write-Host ""
Write-Host "Ready to force push to GitHub!" -ForegroundColor Yellow
Write-Host "This will replace everything on GitHub with the clean version." -ForegroundColor Yellow
$pushConfirm = Read-Host "Push now? (type 'YES' to proceed)"
if ($pushConfirm -ne "YES") {
    Write-Host "Stopped before push. Run 'git push -f origin main' when ready." -ForegroundColor Yellow
    exit
}

# Step 9: Force push
Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Green
git push -f origin main

# Step 10: Done
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "SUCCESS! Repository cleaned and pushed!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Visit https://github.com/Morkenson/PasswordManager" -ForegroundColor White
Write-Host "2. Verify old credentials are gone" -ForegroundColor White
Write-Host "3. Test your application with new credentials" -ForegroundColor White
Write-Host ""
Write-Host "Remember: Your backup is in PasswordManager-backup-* folder" -ForegroundColor Yellow

