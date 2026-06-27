# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in HECTOR, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email: [INSERT SECURITY EMAIL]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for resolution.

## Security Measures

### Authentication
- API key authentication for all endpoints
- JWT token-based authentication with configurable expiry
- Rate limiting per API key (sliding window)

### Input Validation
- All inputs are sanitized against XSS and injection attacks
- Query length limits enforced
- File upload type and size restrictions

### Data Protection
- No sensitive data logged (API keys, tokens redacted)
- Environment variables for all secrets
- `.env` excluded from version control

### Infrastructure
- Docker containers run as non-root user
- CORS restricted to configured origins
- Security headers on all responses

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |
| < Latest | No       |

Always run the latest version for security patches.
