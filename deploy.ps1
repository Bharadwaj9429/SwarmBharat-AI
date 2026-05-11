# SwarmBharat AI Deployment Script for Windows
Write-Host "🚀 Starting SwarmBharat AI Deployment" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Step 1: Check git status
Write-Host "`n📋 Checking git status..." -ForegroundColor Cyan
git status --short

# Step 2: Push to GitHub
Write-Host "`n📤 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "`n🌐 Repository URL: https://github.com/Bharadwaj9429/SwarmBharat-AI" -ForegroundColor Yellow
    Write-Host "`n🚀 Next steps to deploy:" -ForegroundColor Green
    Write-Host "1. Go to https://railway.app" -ForegroundColor White
    Write-Host "2. Click 'New Project' → 'Deploy from GitHub repo'" -ForegroundColor White
    Write-Host "3. Select 'SwarmBharat-AI'" -ForegroundColor White
    Write-Host "4. Add environment variables from .env.production" -ForegroundColor White
    Write-Host "5. Click Deploy!" -ForegroundColor White
} else {
    Write-Host "`n❌ Push failed. You may need to:" -ForegroundColor Red
    Write-Host "   - Use a GitHub token with repo access" -ForegroundColor Yellow
    Write-Host "   - Or create a new repo if secret scanning blocks it" -ForegroundColor Yellow
}
