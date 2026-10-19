# Threat Model — Sealed Bid Security

## TN13: Private Key Exposure Risk

### Status: ✅ FIXED (Phase C, commit b0cb620)

### Original Vulnerability
The `Sealed Bid Key` DocType contained a `private_key_pem` field (Long Text) storing the full RSA-4096 private key in the MariaDB database as plaintext. Any administrator with DB access or an SQL injection could recover the private key and decrypt all bids for a tender — defeating the "sealed" property.

### Attack Vectors (mitigated)
| Vector | Pre-Fix | Post-Fix |
|--------|---------|----------|
| DB read (admin) | Full private key retrievable | Only SSS shares (3-of-3 required) |
| SQL injection | Single query extracts key | 3 separate shares, 3 officers required |
| Backup exfiltration | Key in plaintext | Shares distributed, no single point |
| API call | `frappe.get_doc("Sealed Bid Key", tender).private_key_pem` | Field removed; `generate_and_distribute_keys` destroys plaintext immediately |

### Fix Architecture
```
generate_tender_keypair() → RSA-4096 keypair (in memory)
  ↓
split_secret(private_key_int, n=3, k=3) → 3 SSS shares
  ↓
Sealed Bid Key doc ← {share_1_user, share_1_data, …}  (ONLY shares stored)
  ↓
private_key_pem goes out of scope → garbage collected
```

- **At generation**: Private key exists in memory for <1 second, then split
- **At storage**: Only SSS shares persisted (Mersenne prime 2^521-1)
- **At opening**: `recover_private_key_for_opening(tender_id, shares)` — reconstructs in memory, used to decrypt bids, then discarded
- **Audit trail**: `key_reconstructed`, `reconstructed_at`, `reconstructed_by` recorded

### Residual Risks
1. **Memory scraping**: During key reconstruction, the full private key exists in Python memory for the duration of bid opening (~seconds). Mitigation: use `secrets.compare_digest` and minimize key lifetime.
2. **Share collusion**: 3 officers colluding can reconstruct the key at any time. This is by design — the 3-of-3 scheme requires all officers present.
3. **Custom SSS implementation**: Not audited by a cryptographer. Uses Mersenne prime 2^521-1. Recommendation: pre-production audit by a credentialed cryptographer.

### Key Management Lifecycle
```
Publish Tender → Generate Keys → Split → Store Shares → Discard Private Key
                                                     ↓
                                          [Tender Open Period]
                                                     ↓
Bid Opening → Officers Submit Shares → Reconstruct → Decrypt Bids → Discard
                                                     ↓
                                              [Audit Trail Updated]
```

### Recommendations
1. **Audit**: Have a credentialed cryptographer review `sealed_bid.py` before production
2. **Library**: Consider using `python-shamir-mnemonic` or `slip10` for audited SSS
3. **HSM**: For production, consider Hardware Security Module for key generation
4. **Logging**: Ensure private key material is never logged (use `secrets` module, not `random`)