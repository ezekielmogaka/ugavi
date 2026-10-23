# ADR-003: Submission Path — Server-Side Encryption

**Status:** Accepted
**Date:** 2026-10-21
**Deciders:** Ugavi team (independent QA recommendation)

## Context
Bids arrive at the server via HTTP POST. Two options:
- **(a) Server-side encryption**: Plaintext bid content exists in server memory during the HTTP request handler (~milliseconds), encrypted immediately, only ciphertext stored.
- **(b) Browser-side encryption**: Supplier's browser encrypts bid using tender public key before transmission. Server never sees plaintext.

## Decision
**Use (a) server-side encryption for MVP1.** Browser-side is deferred as Phase B.

## Rationale
1. Browser-side encryption requires JavaScript crypto (Web Crypto API), which adds complexity: key distribution to browser, handling of non-JS clients, and verifying the encryption happened correctly client-side.
2. Frappe's architecture serves bid forms server-side. Adding client-side crypto requires building a separate JS crypto layer that duplicates the Python crypto.
3. Server-side plaintext exposure is ~milliseconds in memory, not written to disk. Accepted residual risk.
4. All other controls (SSS shares, OTP, hash chain) remain in effect regardless of submission path.

## Residual Risk
A compromised server process during bid submission could intercept plaintext. This is the same attack surface as any web application's request handler.

## Migration Path to (b)
- Tender DocType already has `public_key` field (Long Text, PEM format)
- Supplier portal page can call Web Crypto API `crypto.subtle.encrypt()` with the public key
- Server then receives pre-encrypted payload and stores it directly
- Transition requires: JS crypto layer, browser compatibility testing, fallback for no-JS clients

## Evidence
- [code] Bid.submit_bid() at ugavi/procurement/doctype/bid/bid.py:30-56 — encrypts in submit_bid handler
- [measured] plaintext in local variable `content` for ~milliseconds before encryption
- [verified] encrypted_key, nonce, encrypted_content stored; plaintext never in DB