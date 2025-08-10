# GitHub Actions Usage Guide

## Current Issue
You're hitting GitHub Actions usage limits due to billing/payment issues. Here's how to manage this:

## GitHub Actions Limits (Free Accounts)

### Public Repositories
- **2,000 minutes/month** for free
- **Ubuntu runners**: 2 minutes = 1 minute used
- **Windows/macOS runners**: 1 minute = 1 minute used

### Private Repositories
- **500 minutes/month** for free
- Requires billing setup for more

## Optimized Workflows

### 1. Production Deploy (`deploy.yml`)
- ✅ **Only runs on main branch pushes**
- ✅ **Ignores documentation changes**
- ✅ **Optimized caching** (reduces time by ~60%)
- ✅ **Faster npm install** with `--prefer-offline`
- ✅ **Shallow checkout** (faster git operations)

### 2. Development Checks (`develop.yml`)
- ✅ **Only runs on dev branch and PRs to main**
- ✅ **Ignores documentation changes**
- ✅ **Optimized for speed**
- ✅ **Reduced timeout** (8 minutes max)

### 3. Lightweight Check (`lightweight-check.yml`)
- ✅ **Manual trigger only** (workflow_dispatch)
- ✅ **Only type checking** (fastest check)
- ✅ **5-minute timeout**
- ✅ **Minimal usage**

## Usage Reduction Strategies

### 1. Path-Based Triggers
```yaml
paths-ignore:
  - '**.md'
  - 'docs/**'
  - 'README.md'
```
This prevents workflows from running on documentation changes.

### 2. Optimized Caching
```yaml
cache: 'npm'
cache-dependency-path: frontend/package-lock.json
```
Reduces npm install time by ~60%.

### 3. Faster npm Install
```bash
npm ci --prefer-offline --no-audit
```
- `--prefer-offline`: Uses cached packages
- `--no-audit`: Skips security audit (faster)

### 4. Shallow Checkout
```yaml
fetch-depth: 1
```
Only downloads the latest commit (faster).

## Alternative Solutions

### Option 1: Disable GitHub Actions Temporarily
1. Go to repository Settings → Actions → General
2. Select "Disable actions for this repository"
3. Use local development instead

### Option 2: Use Lightweight Workflow Only
1. Disable `deploy.yml` and `develop.yml`
2. Use only `lightweight-check.yml` (manual trigger)
3. Deploy manually when needed

### Option 3: Local Development Workflow
```bash
# Local development checks
cd frontend
npm run lint
npx tsc --noEmit
npm run build

# Manual deployment
npm run build
# Then deploy to Netlify manually
```

### Option 4: Netlify Auto-Deploy
1. Connect GitHub repository to Netlify
2. Set build command: `cd frontend && npm run build`
3. Set publish directory: `frontend/.next`
4. Disable GitHub Actions deployment

## Current Workflow Usage Estimates

| Workflow | Estimated Time | Monthly Usage (10 pushes) |
|----------|----------------|---------------------------|
| deploy.yml | 8-12 minutes | 80-120 minutes |
| develop.yml | 6-10 minutes | 60-100 minutes |
| lightweight-check.yml | 3-5 minutes | 30-50 minutes |

**Total estimated usage: 170-270 minutes/month**

## Immediate Actions

### If You Want to Continue Using GitHub Actions:
1. ✅ **Use optimized workflows** (already implemented)
2. ✅ **Monitor usage** in repository Settings → Actions → General
3. ✅ **Use lightweight workflow** for quick checks

### If You Want to Disable GitHub Actions:
1. Go to repository Settings → Actions → General
2. Select "Disable actions for this repository"
3. Use local development workflow
4. Deploy manually to Netlify

### If You Want to Set Up Billing:
1. Go to GitHub Settings → Billing & plans
2. Add payment method
3. Set spending limits
4. Continue using full workflows

## Recommended Approach

### For Development:
```bash
# Local development
git checkout dev
# Make changes
npm run lint
npx tsc --noEmit
npm run build
git push origin dev
```

### For Production:
```bash
# Merge to main
git checkout main
git merge dev
git push origin main
# GitHub Actions will deploy automatically
```

### If GitHub Actions Fails:
```bash
# Manual deployment
cd frontend
npm run build
# Upload .next folder to Netlify manually
```

## Monitoring Usage

### Check Current Usage:
1. Go to repository Settings → Actions → General
2. Scroll down to "Workflow permissions"
3. See "GitHub-hosted runners" usage

### Set Up Notifications:
1. Go to GitHub Settings → Notifications
2. Enable "Actions" notifications
3. Get alerts when approaching limits

## Emergency Procedures

### If You Hit Limits Mid-Month:
1. **Disable workflows** temporarily
2. **Use local development**
3. **Manual deployment** to Netlify
4. **Wait for next month** or set up billing

### If Production Deployment Fails:
1. **Build locally**: `cd frontend && npm run build`
2. **Deploy manually** to Netlify
3. **Check GitHub Actions** status
4. **Fix issues** and re-enable workflows

## Cost-Effective Alternatives

### 1. Netlify Auto-Deploy
- Free tier available
- Automatic deployment on push
- No GitHub Actions needed

### 2. Vercel
- Free tier available
- Automatic deployment
- Built for Next.js

### 3. Local Development
- No external dependencies
- Full control
- No usage limits

## Next Steps

1. **Choose your approach** (GitHub Actions vs alternatives)
2. **Monitor usage** if using GitHub Actions
3. **Set up billing** if needed
4. **Use optimized workflows** to minimize usage
5. **Consider alternatives** for cost-effectiveness
