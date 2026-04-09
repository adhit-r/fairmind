# Security Policy

## Supported Versions

FairMind is in active pre-1.0 development. Security fixes are applied to the
`main` branch and any active release branches. We recommend running the latest
commit on `main` until a tagged release line exists.

| Version       | Supported          |
| ------------- | ------------------ |
| `main` (HEAD) | Yes                |
| Older commits | No                 |

## Reporting a Vulnerability

We take the security of FairMind seriously. **Please do not report security
vulnerabilities through public GitHub issues, discussions, or pull requests.**

Instead, report vulnerabilities privately via one of the following channels:

1. **Email**: send a report to **security@fairmind.xyz**.
2. **GitHub Security Advisories**: open a private advisory at
   <https://github.com/adhit-r/fairmind/security/advisories/new>.

### What to include in the report

- The type of vulnerability (e.g. XSS, SQLi, RCE, auth bypass, IDOR)
- The full path(s) to the affected source file(s)
- The branch, tag, or commit SHA where you observed the issue
- Any configuration required to reproduce the issue
- Step-by-step instructions to reproduce
- A proof-of-concept or exploit code (if available)
- The impact: what an attacker could do, and under which conditions

### What to expect

- We will acknowledge receipt within **3 business days**.
- We will provide an initial assessment within **7 business days**.
- We will keep you informed of progress as we investigate and remediate.
- Once a fix is released, we will credit you in the advisory unless you ask
  to remain anonymous.

### Disclosure policy

We follow coordinated disclosure. Please give us a reasonable window to
remediate before disclosing publicly. We aim to ship fixes within 90 days of
the initial report, sooner for critical issues. We will notify you when the
vulnerability is fixed and when it is safe to disclose.

## Out of scope

The following are generally not considered vulnerabilities for the purposes of
this policy:

- Issues in third-party dependencies that already have a public CVE and an
  available upstream fix (please open a regular dependency-update issue
  instead)
- Self-XSS that requires the victim to paste attacker-controlled content into
  their own browser console
- Missing security headers without a demonstrated attack
- Rate-limiting or brute-force concerns on endpoints that already enforce
  authentication and account lockout
