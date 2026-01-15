# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.9.x   | :white_check_mark: |
| < 0.9   | :x:                |

## Reporting a Vulnerability

We take the security of Agent Zero seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them by:

1. **GitHub Security Advisories**: Use GitHub's private vulnerability reporting feature by going to the Security tab and clicking "Report a vulnerability"

2. **Email**: If you prefer, you can email the maintainers directly

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
- Full path(s) of the affected source file(s)
- Location of the affected code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability

### Response Timeline

- **Initial Response**: We aim to acknowledge receipt within 48 hours
- **Status Update**: We will provide an update within 7 days
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### After Resolution

Once a vulnerability has been resolved, we will:

1. Release a patched version
2. Publish a security advisory (with credit to the reporter, if desired)
3. Update this document if necessary

## Security Best Practices for Users

When using Agent Zero:

1. **Run in isolation**: Always run Agent Zero in a Docker container or isolated environment
2. **API Keys**: Never commit API keys or secrets to your repository
3. **Environment Variables**: Use environment variables for sensitive configuration
4. **Network Access**: Be cautious about granting network access to agents
5. **Regular Updates**: Keep Agent Zero and its dependencies up to date

## Security Scanning

This repository uses automated security scanning:

- **Semgrep**: Static analysis for security vulnerabilities
- **CodeQL**: GitHub's semantic code analysis
- **Dependabot**: Automated dependency updates for known vulnerabilities
