# ADR-002: Sealed-Bid Cryptography (Revised 2026-10-21)

**Status:** Accepted (with updates)
**Date:** 2026-09-30 (original) | 2026-10-21 (revised with measured evidence)
**Deciders:** Ugavi team

## Context
Tender bids must remain sealed until formal opening by three officers. No single person must decrypt bids before the opening ceremony.

## Decision
**RSA-4096 + AES-256-GCM envelope encryption with custom Shamir's Secret Sharing (3-of-3).**

### Algorithm (verified 2026-10-21):
1. Generate RSA-4096 keypair at tender publication [verified: bench venv enc/dec cycle PASS]
2. Split private key using custom Shamir SSS (3 shares, threshold 3) over Mersenne prime 2^521-1 [tested: test_split_and_reconstruct PASS]
3. Store SSS shares in `Sealed Bid Key` DocType — private key destroyed immediately [verified: no private_key_pem field in schema]
4. 3 bid opening officers each assigned one share [verified: Sealed Bid Key schema share_1/2/3_user + share_1/2/3_data]
5. At opening, 3 officers submit shares + OTP → reconstruct private key in memory [code exists, not runtime-tested]
6. Decrypt bid AES keys → decrypt bid content → discard private key [code exists, not runtime-tested]

### Key properties:
- **No plaintext private key persists** [verified: SealedBidKey._validate_no_private_key_leak]
- **2-of-3 cannot decrypt** [tested: test_two_shares_cannot_reconstruct PASS]
- **OTP**: 6-digit SHA-256, 5-min, 3-attempt [code exists in sealed_bid.py]
- **Audit**: key_reconstructed fields [code exists, not wired to hash chain]

## Library
`cryptography` 50.0.2 (Apache 2.0/BSD) in bench venv. OpenSSL backend.
[verified: /home/frappe/frappe-bench/env/lib/python3.14/site-packages/cryptography]

## Gap: Plaintext Shares in DB
Shares stored as plain integers in share_X_data (Long Text). DB admin can reconstruct key. Addressed by ADR-004 (Share Wrapping).

## Residual Risks
1. Custom SSS not audited by external cryptographer
2. Memory scraping during reconstruction (~seconds)
3. 3-officer collusion (by design)
4. Plaintext bid content in memory ~ms during Bid.submit_bid()

## Evidence
- [verified] HAS_CRYPTO: True (bench venv)
- [verified] Full RSA+AES enc/dec cycle: PASS
- [tested] test_split_and_reconstruct: PASS
- [tested] test_two_shares_cannot_reconstruct: PASS
- [measured] no private_key_pem field in Sealed Bid Key schema