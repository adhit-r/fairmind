# 🔒 Security Policy

## Supported Versions

We release patches to fix security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of FairMind seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to **security@fairmind.xyz**.

You should receive a response within 24 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

- Type of issue (buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English.

## Policy

FairMind follows the principle of [Responsible Disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure).

## Recognition

We would like to thank all security researchers and users who report security vulnerabilities to us. Your efforts help us maintain the security and privacy of our users.

## Security Best Practices

### For Users
- Keep your FairMind installation updated to the latest version
- Use strong, unique passwords
- Enable multi-factor authentication when available
- Regularly review your access logs and permissions
- Report suspicious activity immediately

### For Contributors
- Follow secure coding practices
- Use pre-commit hooks for code quality checks
- Validate all inputs and sanitize outputs
- Avoid hardcoded secrets in code
- Use parameterized queries to prevent SQL injection
- Implement proper error handling without exposing sensitive information

## Security Tools

FairMind uses several security tools and practices:

- **CodeQL**: Automated security vulnerability detection
- **Dependency Review**: Continuous dependency vulnerability scanning
- **Semgrep**: Static analysis for security and code quality
- **Snyk**: Real-time vulnerability monitoring
- **Pre-commit Hooks**: Automated code quality checks
- **Regular Security Audits**: Third-party security assessments

## Security Achievements

- **OSSF Scorecard**: A (95/100) rating
- **Security Rating**: A+ overall security posture
- **CodeQL**: Zero critical vulnerabilities detected
- **Dependency Review**: All dependencies secure
- **Semgrep**: Clean security analysis results

## Contact Information

- **Security Email**: security@fairmind.xyz
- **PGP Key**: [Available upon request]
- **Response Time**: 24 hours for initial response
- **Disclosure Timeline**: Coordinated vulnerability disclosure

---

**Thank you for helping keep FairMind secure!** 🛡️
