# ADR-004: Share Wrapping — Per-Officer Encryption of SSS Shares

**Status:** Accepted
**Date:** 2026-10-21
**Deciders:** Ugavi team (independent QA recommendation)

## Problem
`generate_and_distribute_keys` stores SSS share_y values as plain integer strings in `Sealed Bid Key.share_X_data` (Long Text fields). A database administrator with SQL access can read all 3 share_X_data fields and reconstruct the private key — defeating the "no single person can access" requirement.

```python
# Current code (sealed_bid.py:153-156)
"share_1_data": str(shares[0][1]),  # PLAINTEXT in DB
"share_2_data": str(shares[1][1]),
"share_3_data": str(shares[2][1]),
```

## Decision
**Encrypt each SSS share with a per-officer AES-256-GCM key derived from the officer's passphrase using scrypt.**

### Algorithm
1. At officer enrolment, officer sets a passphrase.
2. `derive_officer_key(passphrase, salt)` → scrypt(N=2^14, r=8, p=1) → 32-byte AES key.
3. At tender key generation: for each officer, encrypt `share_y` with `encrypt_share_for_officer(share_y, officer_key)` → base64(ciphertext+nonce).
4. Store the wrapped share in share_X_data. The plaintext share_y never touches disk.
5. At bid opening: officer provides passphrase → derive key → decrypt share → submit to SSS reconstruction.

## Alternatives Considered
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **scrypt passphrase** | No extra hardware, officer remembers passphrase | Passphrase must be strong; recovery needs passphrase reset | ✅ CHOSEN |
| PKCS#12 / X.509 client cert | Standards-based, no password | Certificate management infrastructure; not suitable for MVP | Deferred |
| HSM-backed key | Highest security | Infrastructure complexity | Deferred to production |
| No wrapping (current) | Simple | Plaintext shares in DB — SV-02 vulnerability | ❌ REJECTED |

## Residual Risk
- Officer forgets passphrase → share unrecoverable → bids cannot be opened. Mitigation: 3-of-N alternates (ADR-006, deferred).
- Weak passphrase → brute-forceable wrapping. Mitigation: scrypt with high work factor; passphrase policy enforcement.

## Evidence
- [verified] Sealed Bid Key.schema has share_X_data as Long Text (currently plaintext)
- [measured] cryptography.hazmat.primitives.kdf.scrypt available in cryptography 50.0.2
- [assumption] scrypt(N=2^14, r=8, p=1) takes ~100ms on modern CPU per KDF eval