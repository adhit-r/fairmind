# Branch Strategy

## Overview
This repository uses a simplified two-branch strategy for development and production.

## Branches

### `main` - Production Branch
- **Purpose**: Production-ready code
- **Deployment**: Automatically deploys to production
- **Protection**: Requires pull request from `dev`
- **Workflow**: `deploy.yml` - Builds and deploys to Netlify

### `dev` - Development Branch
- **Purpose**: Active development and feature work
- **Deployment**: Development/staging environment
- **Protection**: Requires pull request for major changes
- **Workflow**: `develop.yml` - Runs tests, linting, and type checking

## Development Workflow

### 1. Starting New Work
```bash
# Always start from dev branch
git checkout dev
git pull origin dev

# Create feature branch (optional)
git checkout -b feature/new-feature
```

### 2. Making Changes
```bash
# Make your changes
git add .
git commit -m "feat: add new feature"

# Push to dev
git push origin dev
```

### 3. Deploying to Production
```bash
# Merge dev into main
git checkout main
git merge dev
git push origin main

# This triggers automatic deployment
```

## Branch Protection Rules

### Main Branch
- ✅ Requires pull request reviews
- ✅ Requires status checks to pass
- ✅ Requires up-to-date branches
- ✅ Restricts pushes to main

### Dev Branch
- ✅ Requires pull request for major changes
- ✅ Runs development checks
- ✅ Allows direct pushes for minor changes

## CI/CD Pipeline

### Development Pipeline (`develop.yml`)
- Runs on: `dev` branch pushes and PRs
- Actions:
  - Install dependencies
  - Run linting
  - Type checking
  - Build verification

### Production Pipeline (`deploy.yml`)
- Runs on: `main` branch pushes
- Actions:
  - Install dependencies
  - Build application
  - Deploy to Netlify

## Best Practices

### 1. Always Work on Dev
- Never make direct changes to `main`
- All development happens on `dev`
- Use feature branches for complex changes

### 2. Regular Merges
- Merge `dev` to `main` when features are complete
- Keep `main` stable and production-ready
- Test thoroughly before merging

### 3. Commit Messages
- Use conventional commit format
- Be descriptive and clear
- Reference issues when applicable

### 4. Code Review
- Always review code before merging to `main`
- Use pull requests for significant changes
- Ensure all tests pass

## Migration from Old Structure

### What Changed
- ❌ Removed `gh-pages` branch (was for GitHub Pages)
- ✅ Created `dev` branch for development
- ✅ Set up proper CI/CD pipelines
- ✅ Established branch protection rules

### Benefits
- 🚀 Simplified workflow
- 🔒 Better code protection
- 🧪 Automated testing
- 📦 Automated deployment

## Emergency Procedures

### Hotfix Process
```bash
# For critical production fixes
git checkout main
git checkout -b hotfix/critical-fix
# Make minimal changes
git commit -m "fix: critical production issue"
git push origin hotfix/critical-fix
# Create PR to main
# After merge, update dev
git checkout dev
git merge main
git push origin dev
```

### Rollback Process
```bash
# If deployment fails
git checkout main
git revert <commit-hash>
git push origin main
# This will trigger a new deployment
```
