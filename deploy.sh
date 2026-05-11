#!/bin/bash
# SwarmBharat AI Deployment Script

echo "🚀 Starting SwarmBharat AI Deployment"
echo "======================================"

# Step 1: Check git status
echo "📋 Checking git status..."
git status --short

# Step 2: Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
git push origin main --force

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🌐 Repository URL: https://github.com/Bharadwaj9429/SwarmBharat-AI"
    echo ""
    echo "🚀 Next steps to deploy:"
    echo "1. Go to https://railway.app"
    echo "2. Click 'New Project' → 'Deploy from GitHub repo'"
    echo "3. Select 'SwarmBharat-AI'"
    echo "4. Add environment variables from .env.production"
    echo "5. Click Deploy!"
else
    echo "❌ Push failed. You may need to:"
    echo "   - Use a GitHub token with repo access"
    echo "   - Or create a new repo if secret scanning blocks it"
fi
