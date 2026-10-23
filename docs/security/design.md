# Sealed-Bid Design — Ugavi 0.1.0

> Status: Implementation in progress. All claims cite evidence.
> Last updated: 2026-10-21

## 1. Overview

**Goal:** Tender bids cannot be accessed by one person. Access opens only when three designated people each supply a code sent by the system.

**Two-layer security:**
1. **Cryptographic layer:** Per-tender RSA-4096 keypair. Bids encrypted to public key. Private key split via 3-of-3 SSS. Shares wrapped per-officer. Server cannot decrypt without all 3 officers.
2. **Workflow authorization layer:** Officers authenticate separately. System issues OTP per officer. OTP authorizes the unlock step — a code alone cannot decrypt anything.

## 2. Architecture

```
Tender Publication
  → generate_tender_keypair() → RSA-4096 (in memory)
  → split_secret(private_key, n=3, k=3) → 3 SSS shares
  → for each officer: wrap_share(share, scrypt(passphrase)) → encrypted share in DB
  → private key destroyed; public key stored on Tender

Bid Submission
  → supplier submits bid via portal
  → encrypt_bid_content(plaintext, tender.public_key) → encrypted_key + nonce + ciphertext
  → store in Bid.{encrypted_key, nonce, encrypted_content}
  → status = "Submitted"; plaintext only in memory ~ms

Bid Opening Ceremony
  → authorized user clicks "Request Opening"
  → system issues 3 OTPs (email, 5-min expiry, 3-attempt limit)
  → each officer: enters OTP → system verifies → officer provides passphrase
  → unwrap_share(encrypted_share, scrypt(passphrase)) → plaintext share
  → reconstruct_secret(share1, share2, share3) → private key (in memory)
  → for each bid: decrypt_bid_content(bid, private_key) → plaintext
  → populate Bid.{bidder_name, bid_amount, delivery_days}
  → generate Bid Opening Record PDF with hash
  → discard private key
  → audit log every step via hash chain
```

## 3. DocType Map

| DocType | Module | Purpose | Status |
|---------|--------|---------|--------|
| Tender | Tendering | Tender lifecycle, public_key, officers | ✅ Schema exists |
| Bid | Procurement | Encrypted bid from supplier | ✅ Schema exists |
| Sealed Bid Key | Procurement | SSS shares (wrapped), key metadata | ✅ Schema exists |
| Bid Opening Record | Procurement | Opening ceremony record, PDF, hash | ✅ Schema exists |
| Bid Opening Detail | Procurement | Child table: per-bid results | ✅ Schema exists |
| Ugavi Procurement Settings | Procurement | Config: thresholds, OTP params, sealed_bid_enabled | ✅ Schema exists |
| Audit Log | Governance | Hash-chained audit events | ⚠️ Schema exists, not wired |
| Officer Key | Procurement | Officer passphrase enrolment | ❌ Not created |

## 4. Crypto Stack

| Layer | Algorithm | Params | Standard |
|-------|-----------|--------|----------|
| Asymmetric | RSA-4096 | e=65537 | [standard: PKCS#1 v2.2] |
| Symmetric | AES-256-GCM | key=256, nonce=96 | [standard: NIST SP 800-38D] |
| RSA padding | OAEP | SHA-256 MGF1 | [standard: PKCS#1 v2.2 §7.1] |
| SSS field | Mersenne prime | 2^521-1 | [custom] Needs audit |
| KDF (share wrap) | scrypt | N=2^14, r=8, p=1 | [standard: RFC 7914] |
| OTP hash | SHA-256 | 6-digit, time-window | [custom] |
| CSPRNG | secrets module | System entropy | [standard: Python stdlib] |

## 5. Key Lifecycle

1. **Enrolment:** Officer sets passphrase → scrypt → key stored via Officer Key DocType
2. **Generation:** Tender.publish() → generate_and_distribute_keys()
3. **Storage:** Only wrapped SSS shares in DB. No plaintext private key.
4. **Reconstruction:** 3 officers + OTP + passphrase → key in memory ~seconds
5. **Destruction:** Key discarded after all bids decrypted. Python GC.

## 6. OTP Design

- 6 digits, CSPRNG (secrets.randbelow)
- SHA-256 hashed before storage: `hash = SHA256(email:tender_id:otp:time_window)`
- Stored in frappe.cache (Valkey), TTL configurable (default 300s)
- 2-window tolerance (±60s) for clock skew
- 3-attempt limit then lockout
- Constant-time comparison [fix pending: use secrets.compare_digest]

## 7. Audit Trail

- Append-only Audit Log DocType
- SHA-256 hash chain per doctype/docname
- Events: TENDER_PUBLISHED, BID_SUBMITTED, OPENING_REQUESTED, OTP_ISSUED, OTP_VERIFIED, OTP_FAILED, KEY_RECONSTRUCTED, BIDS_DECRYPTED, OPENING_COMPLETED
- Scheduled integrity check: verify hash chain daily
- Not editable from UI or API; track_changes=0 on Audit Log

## 8. Known Gaps

| Gap | Severity | Status |
|-----|----------|--------|
| Share wrapping not implemented | HIGH | ADR-004 accepted, pending impl |
| Opening ceremony endpoint not built | HIGH | Pending |
| Audit hash chain not wired | MEDIUM | Pending |
| Attachment encryption | MEDIUM | Pending |
| OTP constant-time compare | LOW | Pending |
| Officer enrolment DocType | LOW | Pending |
| 3-of-N alternates for key loss | LOW | Deferred to Phase B |
| SMS adapter for OTP | LOW | Deferred to Phase B |
| Browser-side encryption | LOW | Deferred to Phase B |
| Containerised signing for PDF | LOW | Deferred to Phase B |