---
name: "security-audit"
description: "Security audit and vulnerability assessment skill. Use when reviewing code for security issues, hardening systems, or implementing security best practices."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["security", "audit", "vulnerability", "owasp", "hardening"]
trigger_patterns:
  - "security"
  - "vulnerability"
  - "secure"
  - "audit"
  - "owasp"
  - "penetration"
---

# Security Audit Skill

Comprehensive security review and vulnerability assessment guidance.

## OWASP Top 10 Checklist

### 1. Broken Access Control

```markdown
## Check for:
- [ ] Direct object references (IDOR)
- [ ] Missing function-level access control
- [ ] Privilege escalation paths
- [ ] Bypassing access control via URL manipulation

## Example vulnerability:
```python
# Bad: No authorization check
@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return db.get_user(user_id)  # Any user can access any other user!

# Good: Verify authorization
@app.get("/api/users/{user_id}")
def get_user(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(403, "Not authorized")
    return db.get_user(user_id)
```
```

### 2. Cryptographic Failures

```markdown
## Check for:
- [ ] Sensitive data transmitted in plaintext
- [ ] Weak encryption algorithms (MD5, SHA1 for passwords)
- [ ] Hardcoded secrets
- [ ] Insecure random number generation

## Secure practices:
```python
# Password hashing
from argon2 import PasswordHasher
ph = PasswordHasher()
hash = ph.hash("password")
ph.verify(hash, "password")  # Raises exception if invalid

# Secure token generation
import secrets
token = secrets.token_urlsafe(32)

# Never do this:
import hashlib
hash = hashlib.md5(password.encode()).hexdigest()  # WEAK!
```
```

### 3. Injection

```markdown
## Check for:
- [ ] SQL injection
- [ ] NoSQL injection
- [ ] Command injection
- [ ] LDAP injection
- [ ] XPath injection

## SQL Injection Prevention:
```python
# Bad: String concatenation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Good: Parameterized queries
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# Good: ORM with proper escaping
User.query.filter_by(id=user_id).first()
```

## Command Injection Prevention:
```python
# Bad
os.system(f"echo {user_input}")

# Good: Use subprocess with list arguments
subprocess.run(["echo", user_input], shell=False)

# Better: Avoid shell commands with user input entirely
```
```

### 4. Insecure Design

```markdown
## Check for:
- [ ] Missing threat modeling
- [ ] No rate limiting on sensitive operations
- [ ] Lack of defense in depth
- [ ] Missing business logic validation

## Example:
```python
# Bad: No rate limiting on login
@app.post("/login")
def login(credentials: Credentials):
    return authenticate(credentials)

# Good: Rate limited
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/login")
@limiter.limit("5/minute")
def login(credentials: Credentials):
    return authenticate(credentials)
```
```

### 5. Security Misconfiguration

```markdown
## Check for:
- [ ] Default credentials in use
- [ ] Unnecessary features enabled
- [ ] Missing security headers
- [ ] Verbose error messages in production
- [ ] Outdated software

## Security Headers:
```python
# Flask example
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```
```

### 6. Vulnerable Components

```markdown
## Check for:
- [ ] Outdated dependencies
- [ ] Known vulnerable packages
- [ ] Unmaintained libraries

## Tools:
```bash
# Python
pip-audit
safety check -r requirements.txt

# JavaScript
npm audit
yarn audit

# General
snyk test
```
```

### 7. Authentication Failures

```markdown
## Check for:
- [ ] Weak password policies
- [ ] Missing MFA option
- [ ] Session fixation
- [ ] Insecure session management

## Secure Session Management:
```python
# Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour timeout
)

# Regenerate session on login
@app.route('/login', methods=['POST'])
def login():
    if authenticate(request.form):
        session.regenerate()  # Prevent session fixation
        session['user_id'] = user.id
```
```

### 8. Data Integrity Failures

```markdown
## Check for:
- [ ] Missing integrity checks on critical data
- [ ] Insecure deserialization
- [ ] Missing code signing

## Secure Deserialization:
```python
# Bad: Pickle with untrusted data
import pickle
data = pickle.loads(untrusted_data)  # DANGEROUS!

# Good: Use safe serialization
import json
data = json.loads(untrusted_data)

# If you must use pickle, sign and verify
import hmac
def safe_pickle_loads(data, key):
    signature = data[:32]
    pickled = data[32:]
    expected = hmac.new(key, pickled, 'sha256').digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Invalid signature")
    return pickle.loads(pickled)
```
```

### 9. Logging & Monitoring Failures

```markdown
## Check for:
- [ ] Sensitive data in logs
- [ ] Missing audit logs
- [ ] No alerting for security events
- [ ] Logs not protected

## Secure Logging:
```python
import logging

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sanitize sensitive data
def sanitize_log(data):
    sensitive_keys = ['password', 'token', 'api_key', 'ssn']
    return {k: '***' if k in sensitive_keys else v for k, v in data.items()}

# Log security events
def log_security_event(event_type, details):
    logger.warning(f"SECURITY: {event_type} - {sanitize_log(details)}")
```
```

### 10. Server-Side Request Forgery (SSRF)

```markdown
## Check for:
- [ ] URL parameters used for server requests
- [ ] Unvalidated redirects
- [ ] Internal service exposure

## Prevention:
```python
from urllib.parse import urlparse
import ipaddress

ALLOWED_HOSTS = ['api.example.com', 'cdn.example.com']
BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
]

def is_safe_url(url):
    try:
        parsed = urlparse(url)

        # Check allowed hosts
        if parsed.hostname not in ALLOWED_HOSTS:
            return False

        # Check not internal IP
        ip = ipaddress.ip_address(parsed.hostname)
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return False

        return True
    except:
        return False
```
```

## Security Audit Process

### 1. Information Gathering

```markdown
- [ ] Identify all entry points (APIs, forms, file uploads)
- [ ] Map authentication and authorization flows
- [ ] Document data flows
- [ ] List third-party integrations
- [ ] Review infrastructure configuration
```

### 2. Automated Scanning

```bash
# Web application scanning
nikto -h https://target.com
nuclei -u https://target.com -t cves/

# Dependency scanning
npm audit
pip-audit

# Static analysis
bandit -r ./src  # Python
semgrep --config auto ./src  # Multi-language
```

### 3. Manual Testing

```markdown
## Input Validation
- [ ] Test with SQL injection payloads
- [ ] Test with XSS payloads
- [ ] Test with path traversal (../)
- [ ] Test file upload restrictions

## Authentication
- [ ] Test password reset flow
- [ ] Test session timeout
- [ ] Test concurrent session handling
- [ ] Test remember me functionality

## Authorization
- [ ] Test horizontal privilege escalation
- [ ] Test vertical privilege escalation
- [ ] Test API endpoint permissions
```

### 4. Report Template

```markdown
# Security Audit Report

## Executive Summary
[Brief overview of findings]

## Scope
- Systems tested:
- Testing period:
- Methodology:

## Findings

### Critical
| ID | Title | Impact | CVSS |
|----|-------|--------|------|
| C1 | SQL Injection in login | Data breach | 9.8 |

### High
[Similar table]

### Medium
[Similar table]

### Low
[Similar table]

## Detailed Findings

### C1: SQL Injection in Login Form

**Description**: The login form is vulnerable to SQL injection...

**Impact**: An attacker could bypass authentication and access any account...

**Proof of Concept**:
```
Username: ' OR '1'='1
Password: anything
```

**Recommendation**: Use parameterized queries...

**References**:
- CWE-89
- OWASP SQL Injection
```

## Quick Reference

### Input Validation

```python
import re
from html import escape

def sanitize_input(user_input: str) -> str:
    # Remove/escape HTML
    sanitized = escape(user_input)

    # Limit length
    sanitized = sanitized[:1000]

    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')

    return sanitized

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```

### Environment Configuration

```python
# Never commit secrets!
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
API_KEY = os.getenv('API_KEY')

# Verify all required env vars are set
required = ['DATABASE_URL', 'SECRET_KEY', 'API_KEY']
missing = [v for v in required if not os.getenv(v)]
if missing:
    raise RuntimeError(f"Missing environment variables: {missing}")
```
