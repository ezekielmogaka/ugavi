# Penetration Test Checklist — Ugavi 0.1.0

> Use this checklist when engaging a third-party pen-tester or performing self-assessment.

## Pre-Test Setup
- [ ] Test environment provisioned (staging, not production)
- [ ] Demo data seeded (`bench execute ugavi.fixtures.demo_data.run`)
- [ ] Test user accounts created:
  - [ ] Administrator
  - [ ] Procurement Officer (Donor A)
  - [ ] Procurement Officer (Donor B)
  - [ ] Procurement Manager (elevated DoA)
  - [ ] Logistics Officer
  - [ ] Fleet Manager
  - [ ] Supplier (portal user)
  - [ ] Auditor (read-only)
- [ ] TLS certificate installed on test environment
- [ ] Security scan tools available (Burp Suite, OWASP ZAP, Nikto)
- [ ] Test window agreed (no production impact)

## Authentication Tests
- [ ] Brute force protection: >10 login attempts → account locked (15 min)
- [ ] Session fixation: session token regenerated after login
- [ ] Session timeout: verify absolute timeout (default 6h)
- [ ] API key enumeration: cannot enumerate valid API keys
- [ ] 2FA bypass: TOTP cannot be skipped when enabled

## Authorization Tests (Donor Segregation)
- [ ] **Horizontal escalation**: Donor A procurement officer accesses Donor B's PR → blocked
- [ ] **Vertical escalation**: Procurement Officer approves PR above DoA → blocked
- [ ] **Cross-module access**: Logistics Officer accesses sealed bids → blocked
- [ ] **Supplier self-access**: Supplier sees only own bids, not competitors'
- [ ] **IDOR**: Modify bid ID in URL → access denied
- [ ] **Direct object reference**: Enumeration of bid IDs → only own bids visible
- [ ] **Stock isolation**: Donor A stock balance query does not include Donor B stock

## Sealed-Bid Crypto Tests
- [ ] **Pre-open access**: Bid data cannot be read before opening date/time
- [ ] **Single share insufficient**: 1 or 2 key shares alone cannot decrypt
- [ ] **3-of-3 decryption**: All 3 shares required for successful reconstruction
- [ ] **Key rotation**: Rotated key does not leave old plaintext key accessible
- [ ] **Memory safety**: Private key not in process memory after split (manual review)
- [ ] **Database dump**: SSS shares only in DB, no plaintext private key

## Injection Tests
- [ ] SQL injection: `' OR '1'='1` in PR title → sanitized
- [ ] XSS: `<script>alert(1)</script>` in tender title → escaped
- [ ] Template injection: `{{7*7}}` in bid description → not evaluated
- [ ] File upload: Upload .php/.exe as bid attachment → rejected
- [ ] Path traversal: `../../../etc/passwd` in file path → blocked

## Business Logic Tests
- [ ] **Bid on closed tender**: Bid submitted after deadline → rejected
- [ ] **Double bid**: Same supplier, same tender, two bids → only latest valid?
- [ ] **Negative stock**: Issue more than available → rejected
- [ ] **Cross-donor transfer**: Transfer without bilateral approval → rejected
- [ ] **DoA bypass**: PR above threshold without manager approval → blocked
- [ ] **Rate limit**: >3 bids/hr from same supplier → blocked

## Rate Limiting Tests
- [ ] Login: 10 attempts in 15 min → rate limited
- [ ] OTP: 3 wrong attempts in 5 min → rate limited
- [ ] Bid submission: 3 per supplier per tender per hour → rate limited
- [ ] Rate limit reset: After window expiry, counter resets

## Infrastructure Tests
- [ ] TLS: Minimum TLS 1.2, prefer 1.3
- [ ] Security headers: HSTS, X-Frame-Options, X-Content-Type-Options, CSP
- [ ] Cookie security: HttpOnly, Secure, SameSite flags set
- [ ] Debug mode: `bench set-config developer_mode 0` in production
- [ ] Error pages: No stack traces, no database errors visible

## Data Protection Tests
- [ ] Encrypted fields: bid_amount stored encrypted in DB
- [ ] Audit logs: hash chain intact after modifications
- [ ] Export safety: CSV export respects donor segregation
- [ ] Backup encryption: Backup files don't contain plaintext keys

## Post-Test
- [ ] All findings documented with severity (Critical/High/Medium/Low)
- [ ] Evidence screenshots/logs attached
- [ ] Remediation plan for each finding
- [ ] Re-test after fixes applied
- [ ] Final report generated

---

**Test Date:** ___________ | **Tester:** ___________ | **Signature:** ___________