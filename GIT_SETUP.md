# Git Setup Instructions

## 1. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `voice-assistant`
3. Description: "Simple voice chatbot using Pipecat - responds with 'Hello!' to greetings"
4. **Keep it Public** (or Private if you prefer)
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

## 2. Initialize Git and Push (Run in PowerShell)

```powershell
# Navigate to your project
cd E:\voiceassistent

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Voice assistant with Pipecat"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/voice-assistant.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 3. What's Included

✅ README.md - Complete documentation
✅ .gitignore - Excludes sensitive files (.env, venv, etc.)
✅ pipecat-quickstart/ - All bot files
✅ Old experiment files (simple_chatbot.py, etc.)

## 4. What's Excluded (by .gitignore)

❌ .env files (API keys)
❌ Virtual environments (.venv/)
❌ Python cache (__pycache__/)
❌ IDE files (.vscode/, .idea/)

## 5. After Pushing

Your repository will be at:
`https://github.com/YOUR_USERNAME/voice-assistant`

Share it with:
```
git clone https://github.com/YOUR_USERNAME/voice-assistant.git
```

## Important: Protect Your API Keys

⚠️ **NEVER commit .env files**
- The .gitignore prevents this
- Use .env.example as a template
- Each user should create their own .env
