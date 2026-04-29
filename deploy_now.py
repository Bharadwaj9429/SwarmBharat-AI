#!/usr/bin/env python3
"""
Quick Deployment Script for SwarmBharat AI
Deploy to Railway.app with local MongoDB
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run command and show result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - ERROR: {str(e)}")
        return False

def main():
    print("🚀 SwarmBharat AI - Quick Deployment")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("backend/main.py"):
        print("❌ Please run this from the SwarmBharat-AI root directory")
        sys.exit(1)
    
    # Step 1: Install Railway CLI
    if not run_command("npm list -g @railway/cli", "Check Railway CLI"):
        print("📦 Installing Railway CLI...")
        run_command("npm install -g @railway/cli", "Install Railway CLI")
    
    # Step 2: Login to Railway
    print("\n🔑 Please login to Railway...")
    run_command("railway login", "Login to Railway")
    
    # Step 3: Initialize Railway project
    print("\n📁 Initializing Railway project...")
    run_command("railway init", "Initialize Railway project")
    
    # Step 4: Deploy
    print("\n🚀 Deploying to Railway...")
    if run_command("railway up", "Deploy to Railway"):
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("\n📋 NEXT STEPS:")
        print("1. Go to your Railway dashboard")
        print("2. Set environment variables:")
        print("   MONGODB_URI=mongodb://localhost:27017/swarmbharat")
        print("   REDIS_URL=your_redis_url")
        print("   FIREBASE_PROJECT_ID=swarmbharat-ai")
        print("3. Redeploy with new variables")
        print("4. Test your live app!")
    else:
        print("\n❌ DEPLOYMENT FAILED!")
        print("Please check the error messages above")

if __name__ == "__main__":
    main()
