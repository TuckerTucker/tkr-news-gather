# Security Implementation Guide

## Overview

The TKR News Gatherer has been enhanced with comprehensive security controls to address all critical vulnerabilities identified in the security analysis. This document outlines the implemented security measures and operational procedures.

## 🔒 Security Features Implemented

### 1. Authentication & Authorization

**JWT-based Authentication:**
- Secure JWT token generation with RS256 algorithm
- Token expiration (30 minutes default)
- Scope-based authorization (read, write, admin)
- Protected endpoints require valid JWT tokens

**API Key Authentication:**
- Alternative authentication for service-to-service communication
- Configurable API keys via environment variables
- Constant-time comparison to prevent timing attacks

**Usage:**
```bash
# Get JWT token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secure_password"

# Use JWT token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/news/ontario

# Use API key
curl -H "X-API-Key: <api-key>" \
  http://localhost:8000/provinces
```

### 2. Input Validation & SSRF Protection

**Comprehensive Validation:**
- Province names validated against allowlist
- Numeric limits enforced (1-50 articles)
- Host types restricted to known values
- URL validation with SSRF protection

**SSRF Protection:**
- Blocks private IP ranges (RFC 1918)
- Prevents access to localhost and metadata services
- Validates URL schemes (blocks file://, gopher://, etc.)
- Enforces maximum URL limits per request

### 3. Rate Limiting

**Multi-tier Rate Limiting:**
- Global: 100 requests/minute per IP
- Authentication: 5 requests/minute per IP
- AI Processing: 5 requests/minute per IP
- Scraping: 3 requests/minute per IP
- Pipeline: 1 request/hour per IP

### 4. Security Headers

**Implemented Headers:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'`

### 5. CORS Configuration

**Restricted Origins:**
- Configurable allowed origins (no wildcards in production)
- Specific allowed methods (GET, POST only)
- Controlled headers (Authorization, Content-Type, X-API-Key)
- Credentials support only for trusted origins

### 6. Error Handling

**Secure Error Responses:**
- Sanitized error messages in production
- No stack traces or internal details exposed
- Request IDs for troubleshooting
- Comprehensive security logging

### 7. Logging & Monitoring

**Security Event Logging:**
- Authentication attempts (success/failure)
- Rate limit violations
- Input validation failures
- SSRF attempts
- Request/response timing

## 🚀 Quick Start

### 1. Generate Security Credentials

```bash
# Generate secure credentials
make generate-credentials

# Copy output to .env file
cp .env.example .env
# Edit .env with generated credentials
```

### 2. Run Security Tests

```bash
# Full security validation
make security-full

# Individual tests
make security-scan    # Dependency and code scanning
make security-test    # API security testing
make code-audit      # Static analysis
```

### 3. Start Secure Server

```bash
# Development (with debug features)
DEBUG=true python -m uvicorn src.main_secure:app --reload

# Production (secure configuration)
python -m uvicorn src.main_secure:app --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

```bash
# Security Configuration
JWT_SECRET_KEY=<32-character-random-string>
API_KEYS=key1,key2,key3
RATE_LIMIT_PER_MINUTE=100
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ENABLE_SECURITY_HEADERS=true
TRUSTED_HOSTS=yourdomain.com,*.yourdomain.com

# Optional Security Features
DEBUG=false                    # Disable debug features in production
ENABLE_METRICS=false          # Enable metrics collection
```

### User Management

The current implementation includes a basic authentication system. For production use:

1. **Implement proper user database**
2. **Add user registration/management**
3. **Implement password policies**
4. **Add multi-factor authentication**
5. **Integrate with existing identity providers**

## 🛡️ Security Testing

### Automated Testing

```bash
# Run all security tests
./scripts/test-security.sh

# Test specific areas
curl -H "X-API-Key: invalid" http://localhost:8000/provinces  # Should return 401
curl http://localhost:8000/news/ontario                       # Should return 401
curl -H "Origin: http://malicious.com" http://localhost:8000  # Should be blocked
```

### Manual Testing Checklist

- [ ] All endpoints require authentication
- [ ] Rate limiting prevents abuse
- [ ] Input validation blocks malicious input
- [ ] SSRF protection blocks internal requests
- [ ] Security headers are present
- [ ] Error messages don't leak information
- [ ] CORS is properly configured

## 🚨 Security Incident Response

### 1. Detection

Monitor logs for:
- Repeated authentication failures
- Rate limit violations
- SSRF attempts
- Unusual request patterns

### 2. Response

```bash
# View security logs
tail -f logs/security.log

# Check rate limiting status
curl http://localhost:8000/health

# Temporary API key revocation
# Update API_KEYS environment variable
```

### 3. Recovery

1. Rotate compromised credentials
2. Update security configurations
3. Review and update access patterns
4. Document incident and lessons learned

## 📋 Security Checklist for Production

### Pre-Deployment

- [ ] All security credentials generated and stored securely
- [ ] CORS origins configured for production domains only
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] Rate limits appropriate for expected traffic
- [ ] Security headers enabled
- [ ] HTTPS enforced (configure reverse proxy)
- [ ] Database credentials secured
- [ ] API keys distributed securely

### Post-Deployment

- [ ] Security monitoring enabled
- [ ] Log aggregation configured
- [ ] Incident response procedures documented
- [ ] Regular security scanning scheduled
- [ ] Credential rotation schedule established
- [ ] Security training for team members

### Ongoing Maintenance

- [ ] Weekly dependency updates (`make deps-audit`)
- [ ] Monthly security scans (`make security-full`)
- [ ] Quarterly penetration testing
- [ ] Annual security architecture review

## 🔍 Monitoring & Alerting

### Key Metrics to Monitor

1. **Authentication Failures** - Potential brute force attacks
2. **Rate Limit Violations** - DoS attempts or abuse
3. **Input Validation Failures** - Injection attempts
4. **SSRF Attempts** - Internal network probing
5. **Error Rates** - Application health and attacks

### Recommended Alerting Thresholds

```yaml
alerts:
  - auth_failures > 10/minute
  - rate_limit_violations > 50/minute  
  - validation_errors > 20/minute
  - ssrf_attempts > 1/minute
  - error_rate > 5%
```

## 📚 Additional Resources

### Security Standards Compliance

- **OWASP Top 10 2021** - All major risks addressed
- **NIST Cybersecurity Framework** - Identify, Protect, Detect, Respond, Recover
- **CIS Controls** - Critical security controls implemented

### Related Documentation

- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Contributing Guidelines](CONTRIBUTING.md)

### Security Training Resources

- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [SANS Secure Coding Practices](https://www.sans.org/white-papers/2172/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)

---

**⚠️ Important:** This security implementation provides a strong foundation, but security is an ongoing process. Regular updates, monitoring, and security assessments are essential for maintaining a secure application.

For security questions or to report vulnerabilities, please contact: security@tkr-team.com