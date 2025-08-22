# Security Guidelines for FairMind

## 🚨 Critical Security Rules

### 1. **NEVER Commit Secrets**
- ❌ **NEVER** commit private keys, passwords, or API keys
- ❌ **NEVER** commit `.env` files or environment variables
- ❌ **NEVER** commit database connection strings
- ❌ **NEVER** commit SSL certificates or private keys

### 2. **Use Environment Variables**
- ✅ Store secrets in environment variables
- ✅ Use `.env.example` files for documentation
- ✅ Use secure secret management services

### 3. **File Naming Conventions**
- ❌ Avoid files with names like: `secret`, `credential`, `password`, `key`
- ✅ Use descriptive names that don't hint at sensitive content

## 🔒 Security Measures Implemented

### 1. **Pre-commit Security Scan**
- Automatic scanning before every commit
- Detects private keys, passwords, API keys
- Blocks commits with security issues
- Located: `scripts/security-scan.sh`

### 2. **Comprehensive .gitignore**
- Blocks all sensitive file types
- Prevents accidental commits of secrets
- Covers certificates, keys, environment files

### 3. **GitHub Actions Security Scan**
- Runs on every push and pull request
- Uses TruffleHog and Gitleaks
- Scans entire repository history
- Located: `.github/workflows/security-scan.yml`

## 🛠️ How to Handle Secrets

### 1. **Environment Variables**
```bash
# Create .env file (NOT committed)
DATABASE_URL="postgresql://user:pass@host:port/db"
API_KEY="your-actual-api-key"
SECRET_KEY="your-actual-secret-key"

# Create .env.example (committed)
DATABASE_URL="postgresql://user:password@host:port/database"
API_KEY="your-api-key-here"
SECRET_KEY="your-secret-key-here"
```

### 2. **Supabase Configuration**
```bash
# Use environment variables
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key-here"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key-here"
```

### 3. **Database Connections**
```bash
# Use connection pooling and environment variables
DATABASE_URL="postgresql://user:password@host:port/db?sslmode=require"
```

## 🚨 Emergency Procedures

### If Secrets Are Accidentally Committed:

1. **Immediate Actions**:
   - Rotate all exposed credentials immediately
   - Revoke and regenerate private keys
   - Update any services using these credentials

2. **Remove from Git History**:
   ```bash
   # Use git filter-repo to remove files from history
   git filter-repo --path path/to/secret/file --invert-paths --force
   git push origin --force --all
   ```

3. **Notify Team**:
   - Alert all team members
   - Check for any unauthorized access
   - Review access logs

## 📋 Security Checklist

### Before Every Commit:
- [ ] Run `./scripts/security-scan.sh`
- [ ] Check for any `.env` files
- [ ] Check for private keys or certificates
- [ ] Check for hardcoded passwords or API keys
- [ ] Verify no sensitive data in comments

### Before Every Push:
- [ ] Ensure all tests pass
- [ ] Verify security scan passes
- [ ] Check GitHub Actions security scan
- [ ] Review changed files for sensitive content

### Weekly Security Review:
- [ ] Review access logs
- [ ] Check for new security vulnerabilities
- [ ] Update dependencies
- [ ] Review environment variables

## 🔧 Security Tools

### 1. **Pre-commit Hook**
- Location: `.git/hooks/pre-commit`
- Automatically runs security scan
- Blocks commits with security issues

### 2. **Security Scan Script**
- Location: `scripts/security-scan.sh`
- Scans for common secret patterns
- Checks file types and sizes

### 3. **GitHub Actions**
- Location: `.github/workflows/security-scan.yml`
- Runs TruffleHog and Gitleaks
- Scans repository history

## 📞 Security Contacts

- **Security Issues**: Create GitHub issue with `security` label
- **Emergency**: Contact team lead immediately
- **Questions**: Ask in team chat or create discussion

## 🎯 Best Practices

### 1. **Code Review**
- Always review code for secrets
- Check for hardcoded values
- Verify environment variable usage

### 2. **Documentation**
- Document all environment variables
- Keep `.env.example` updated
- Document security procedures

### 3. **Monitoring**
- Monitor for security alerts
- Review GitHub security tab
- Check dependency vulnerabilities

## 🚀 Quick Commands

```bash
# Run security scan manually
./scripts/security-scan.sh

# Check for secrets in current directory
grep -r "password\|secret\|key" . --exclude-dir=node_modules --exclude-dir=.git

# Check for sensitive files
find . -name "*.pem" -o -name "*.key" -o -name ".env*"

# Test pre-commit hook
git add . && git commit -m "test"
```

## 📚 Resources

- [GitHub Security Best Practices](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [Environment Variables Best Practices](https://12factor.net/config)
- [Git Security](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)

---

**Remember**: Security is everyone's responsibility. When in doubt, ask before committing!
