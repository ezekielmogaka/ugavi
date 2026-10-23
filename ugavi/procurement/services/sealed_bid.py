"""Sealed-Bid Encryption — Core Crypto.

Shamir's Secret Sharing (3-of-3) + RSA envelope encryption + AES-256-GCM.
Share wrapping at rest (PBKDF2-HMAC-SHA256 + AES-256-GCM per share).
Opening ceremony: 3-officer OTP → reconstruct key → decrypt all bids.

Threat model: no single user can decrypt bids alone.
Database-level defense-in-depth via per-share wrapping keys.
"""
import base64
import binascii
import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timedelta

import frappe
from frappe import _

# We use cryptography library for production-grade crypto
try:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ---- Shamir's Secret Sharing (3-of-3) ----
PRIME = 2**521 - 1  # Mersenne prime for field arithmetic


def _eval_poly(coeffs: list[int], x: int, prime: int) -> int:
    result = 0
    for coeff in reversed(coeffs):
        result = (result * x + coeff) % prime
    return result


def split_secret(secret: int, n: int = 3, k: int = 3) -> list[tuple[int, int]]:
    coeffs = [secret] + [secrets.randbelow(PRIME) for _ in range(k - 1)]
    return [(i + 1, _eval_poly(coeffs, i + 1, PRIME)) for i in range(n)]


def reconstruct_secret(shares: list[tuple[int, int]]) -> int:
    if len(shares) < 3:
        raise ValueError("Need exactly 3 shares for reconstruction")
    secret = 0
    for i, (xi, yi) in enumerate(shares):
        num, den = 1, 1
        for j, (xj, _share_value) in enumerate(shares):
            if i != j:
                num = (num * (-xj)) % PRIME
                den = (den * (xi - xj)) % PRIME
        inv_den = pow(den, PRIME - 2, PRIME)
        secret = (secret + yi * num * inv_den) % PRIME
    return secret


# ---- Key Generation & Encryption ----

def generate_tender_keypair():
    """Generate RSA-4096 key pair for tender encryption."""
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required for sealed bids")
    private_key = rsa.generate_private_key(65537, 4096, default_backend())
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def encrypt_bid_content(plaintext: str, public_key_pem: bytes) -> dict[str, str]:
    """Envelope encryption: AES-256-GCM for content, RSA for AES key."""
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required")
    aes_key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(aes_key)
    nonce = secrets.token_bytes(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
    encrypted_key = public_key.encrypt(aes_key, padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(), label=None))
    return {
        "encrypted_key": base64.b64encode(encrypted_key).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }


def decrypt_bid_content(encrypted_data: dict[str, str], private_key_pem: bytes) -> str:
    """Decrypt bid content using private key."""
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required")
    encrypted_key = base64.b64decode(encrypted_data["encrypted_key"])
    nonce = base64.b64decode(encrypted_data["nonce"])
    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())
    aes_key = private_key.decrypt(encrypted_key, padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(), label=None))
    aesgcm = AESGCM(aes_key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


# ---- Share Wrapping (Defense-in-Depth) ----

WRAPPING_ITERATIONS = 100_000
WRAPPING_KEY_LENGTH = 32  # AES-256


def _get_wrapping_secret() -> bytes:
    """Retrieve the site-level wrapping secret from env or site config.

    Falls back to a hash of the site database password so that
    developers do not need an extra env var set on local machines.
    """
    secret = os.environ.get("SEALED_BID_WRAPPING_SECRET")
    if secret:
        return secret.encode("utf-8")
    from frappe.utils.password import get_encryption_key

    site_key = get_encryption_key()
    if not site_key:
        frappe.throw(
            _("SEALED_BID_WRAPPING_SECRET or the site encryption key must be configured")
        )
    return hashlib.sha256(site_key.encode()).digest()


def _derive_wrapping_key(salt: bytes) -> bytes:
    """Derive an AES-256 key from the site secret + per-share salt."""
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required for share wrapping")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=WRAPPING_KEY_LENGTH,
        salt=salt,
        iterations=WRAPPING_ITERATIONS,
        backend=default_backend(),
    )
    return kdf.derive(_get_wrapping_secret())


def _wrap_share(share_value: str) -> str:
    """Encrypt a share with AES-256-GCM before DB storage.

    Returns a string ``salt:nonce:ciphertext`` (all base64).
    """
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required")
    salt = secrets.token_bytes(32)
    wrapping_key = _derive_wrapping_key(salt)
    aesgcm = AESGCM(wrapping_key)
    nonce = secrets.token_bytes(12)
    ciphertext = aesgcm.encrypt(nonce, share_value.encode("utf-8"), None)
    return f"{base64.b64encode(salt).decode()}:{base64.b64encode(nonce).decode()}:{base64.b64encode(ciphertext).decode()}"


def _unwrap_share(wrapped_blob: str) -> str:
    """Decrypt a share that was stored as 'salt:nonce:ciphertext'."""
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required")
    parts = wrapped_blob.split(":")
    if len(parts) != 3:
        raise ValueError("Invalid wrapped share format - expected salt:nonce:ciphertext")
    salt = base64.b64decode(parts[0])
    nonce = base64.b64decode(parts[1])
    ciphertext = base64.b64decode(parts[2])
    wrapping_key = _derive_wrapping_key(salt)
    aesgcm = AESGCM(wrapping_key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def construct_private_key(tender: str) -> bytes:
    """Reconstruct the 256-bit wrapping key and decrypt the RSA private key in memory."""
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required")
    key_doc = frappe.get_doc("Sealed Bid Key", {"tender": tender})
    if not key_doc:
        frappe.throw(_("No sealed-bid key found for tender {0}").format(tender))
    shares: list[tuple[int, int]] = []
    for i in range(1, 4):
        data_field = f"share_{i}_data"
        wrapped = key_doc.get(data_field)
        if not wrapped:
            frappe.throw(_("Share {0} missing").format(i))
        try:
            plain_y = int(_unwrap_share(wrapped))
        except (ValueError, TypeError, binascii.Error, InvalidTag) as e:
            frappe.throw(_("Failed to unwrap share {0}: {1}").format(i, str(e)))
        shares.append((i, plain_y))
    wrapping_key_int = reconstruct_secret(shares)
    wrapping_key = wrapping_key_int.to_bytes(32, byteorder="big")
    try:
        nonce = base64.b64decode(key_doc.private_key_nonce)
        encrypted_private_key = base64.b64decode(key_doc.encrypted_private_key)
        private_key_pem = AESGCM(wrapping_key).decrypt(
            nonce, encrypted_private_key, tender.encode("utf-8")
        )
    except (ValueError, TypeError, binascii.Error, InvalidTag) as exc:
        frappe.throw(_("Failed to reconstruct sealed-bid key: {0}").format(exc))
    key_doc.key_reconstructed = 1
    key_doc.reconstructed_at = datetime.now()
    key_doc.reconstructed_by = frappe.session.user
    key_doc.save(ignore_permissions=True)
    return private_key_pem


# ---- Opening Ceremony ----


split_and_distribute_private_key = None  # removed — use generate_and_distribute_keys

def generate_and_distribute_keys(tender: str, officers: list) -> dict:
    """Generate RSA keypair, immediately split private key via SSS, wrap each share.

    The private key is never written to disk or database — only AES-256-GCM wrapped
    SSS shares are persisted (one per officer). Reconstruction requires all 3 officers
    plus the site-level wrapping secret.

    Returns: dict with {"public_key_pem": str}
    """
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required for sealed bids")
    if len(officers) < 3 or len(set(officers)) < 3:
        frappe.throw("Exactly 3 distinct officers are required for key generation")

    from frappe.utils import now_datetime

    private_pem, public_pem = generate_tender_keypair()

    # Encrypt the large PEM with a random 256-bit key, then split only that key.
    # The SSS field is 521 bits, so splitting the PEM integer directly would
    # reduce it modulo PRIME and irreversibly corrupt the key.
    wrapping_key = AESGCM.generate_key(bit_length=256)
    private_key_nonce = secrets.token_bytes(12)
    encrypted_private_key = AESGCM(wrapping_key).encrypt(
        private_key_nonce, private_pem, tender.encode("utf-8")
    )
    shares = split_secret(int.from_bytes(wrapping_key, byteorder="big"), n=3, k=3)

    # Wrap each share with AES-256-GCM before DB storage
    # Each share stores as "salt:nonce:ciphertext" (base64)
    wrapped_shares = []
    for i, (share_x, share_y) in enumerate(shares):
        wrapped_blob = _wrap_share(str(share_y))
        wrapped_shares.append({
            "officer": officers[i],
            "share_x": share_x,
            "wrapped_blob": wrapped_blob,
        })

    # Persist wrapped shares (NO plaintext private key)
    key_doc = frappe.get_doc({
        "doctype": "Sealed Bid Key",
        "tender": tender,
        "generated_at": now_datetime(),
        "public_key_pem": public_pem.decode("utf-8"),
        "encrypted_private_key": base64.b64encode(encrypted_private_key).decode(),
        "private_key_nonce": base64.b64encode(private_key_nonce).decode(),
        "share_1_user": officers[0],
        "share_1_data": wrapped_shares[0]["wrapped_blob"],
        "share_2_user": officers[1],
        "share_2_data": wrapped_shares[1]["wrapped_blob"],
        "share_3_user": officers[2],
        "share_3_data": wrapped_shares[2]["wrapped_blob"],
        "shares_distributed": 1,
    })
    key_doc.insert(ignore_permissions=True)
    del private_pem
    del wrapping_key
    return {"public_key_pem": public_pem.decode("utf-8")}


@frappe.whitelist()
def open_bids(tender: str,
              officer_1_otp: str | None = None,
              officer_2_otp: str | None = None,
              officer_3_otp: str | None = None) -> dict:
    """Full bid-opening ceremony: verify OTPs → reconstruct key → decrypt all bids.

    1. Verify OTPs from all 3 officers
    2. Unwrap shares + reconstruct RSA private key via SSS
    3. Decrypt every Submitted bid's content
    4. Populate Bid Opening Record; mark bids Opened; advance tender to Under Evaluation
    5. Return summary with opening_record, count, decrypted_bids

    OTPs must be requested first via ``init_opening_ceremony()``.
    """
    tender_doc = frappe.get_doc("Tender", tender)
    if tender_doc.status not in ("Published", "Bids Received"):
        frappe.throw(_("Tender is not awaiting bid opening"))
    if not tender_doc.submission_deadline or frappe.utils.now_datetime() <= tender_doc.submission_deadline:
        frappe.throw(_("Bids can only be opened after the submission deadline"))
    if "Bid Opening Officer" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
        frappe.throw(_("Only a Bid Opening Officer can conduct the ceremony"))
    officers = [
        tender_doc.opening_officer_1,
        tender_doc.opening_officer_2,
        tender_doc.opening_officer_3,
    ]
    if any(not officer for officer in officers) or len(set(officers)) != 3:
        frappe.throw(_("Three distinct opening officers must be assigned"))
    otps = [officer_1_otp, officer_2_otp, officer_3_otp]
    verification_logs = []

    # Step 1: OTP verification
    for officer, otp in zip(officers, otps):
        if not otp:
            frappe.throw(_("Missing OTP for officer {0}").format(officer))
        stored = frappe.cache().get(f"bid_otp:{tender}:{officer}")
        if not stored:
            frappe.throw(_("OTP not requested or expired for officer {0}").format(officer))
        data = json.loads(stored)
        if not verify_otp(officer, tender, otp, data.get("hash", "")):
            frappe.throw(_("Invalid OTP for officer {0}").format(officer))
        verification_logs.append(
            _("Verified for {0} at {1}").format(
                officer, frappe.utils.now_datetime()
            )
        )

    # Step 2: Reconstruct private key (unwraps all 3 shares)
    _log_audit(tender, frappe.session.user, "OPENING_CEREMONY_START", "InProgress")
    try:
        private_pem = construct_private_key(tender)
    except Exception as e:
        _log_audit(tender, frappe.session.user, "KEY_RECONSTRUCTION_FAILED", str(e))
        raise

    # Step 3: Decrypt all submitted bids
    bids = frappe.get_all("Bid",
                          filters={"tender": tender, "status": "Submitted"},
                          fields=["name", "supplier", "encrypted_key", "nonce", "encrypted_content"])
    decrypted_bids = []
    for bid in bids:
        try:
            plaintext = decrypt_bid_content({
                "encrypted_key": bid.encrypted_key,
                "nonce": bid.nonce,
                "ciphertext": bid.encrypted_content,
            }, private_pem)
            content = json.loads(plaintext)
            proposal_url = None
            proposal = content.get("technical_proposal")
            if proposal:
                from frappe.utils.file_manager import save_file

                file_doc = save_file(
                    proposal["name"],
                    base64.b64decode(proposal["content"]),
                    "Bid",
                    bid.name,
                    is_private=1,
                )
                proposal_url = file_doc.file_url
            frappe.db.set_value("Bid", bid.name, "status", "Opened")
            frappe.db.set_value("Bid", bid.name, "bidder_name", content.get("bidder", ""))
            frappe.db.set_value("Bid", bid.name, "bid_amount", content.get("amount", 0))
            frappe.db.set_value("Bid", bid.name, "delivery_days", content.get("delivery", 0))
            if proposal_url:
                frappe.db.set_value("Bid", bid.name, "technical_proposal", proposal_url)
            decrypted_bids.append({
                "bid": bid.name, "supplier": bid.supplier,
                "amount": content.get("amount", 0),
                "delivery_days": content.get("delivery", 0),
            })
        except (ValueError, TypeError, binascii.Error, InvalidTag) as exc:
            _log_audit(tender, frappe.session.user, "BID_DECRYPTION_FAILED", bid.name)
            frappe.throw(_("Could not decrypt bid {0}: {1}").format(bid.name, exc))

    # Step 4: Create Bid Opening Record
    bor = frappe.get_doc({
        "doctype": "Bid Opening Record",
        "tender": tender,
        "opening_date": datetime.now(),
        "officer_1": officers[0], "officer_2": officers[1], "officer_3": officers[2],
        "outcome": "Success" if decrypted_bids else "Partial",
        "otp_log_1": verification_logs[0],
        "otp_log_2": verification_logs[1],
        "otp_log_3": verification_logs[2],
    })
    bor.flags.opening_verified = True
    for db in decrypted_bids:
        bor.append("bids_opened", {
            "bid": db["bid"], "supplier": db["supplier"],
        })
    bor.insert(ignore_permissions=True)
    for officer in officers:
        frappe.cache().delete(f"bid_otp:{tender}:{officer}")

    # Advance tender
    tender_doc.status = "Under Evaluation"
    tender_doc.save(ignore_permissions=True)

    _log_audit(tender, frappe.session.user, "OPENING_CEREMONY_COMPLETE",
               f"Success: {len(decrypted_bids)} bids opened")
    del private_pem
    return {
        "opening_record": bor.name,
        "bids_opened": len(decrypted_bids),
        "decrypted_bids": decrypted_bids,
    }


@frappe.whitelist()
def init_opening_ceremony(tender: str) -> dict:
    """Generate OTPs for all 3 officers and send emails.

    Returns dict with {"officers": [...], "otp_hashes": {email: hash}} used
    by the caller to pass officer-provided OTPs to ``open_bids()``.
    """
    tender_doc = frappe.get_doc("Tender", tender)
    if not tender_doc.submission_deadline or frappe.utils.now_datetime() <= tender_doc.submission_deadline:
        frappe.throw(_("Opening codes can only be requested after the submission deadline"))
    if "Bid Opening Officer" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
        frappe.throw(_("Only a Bid Opening Officer can request opening codes"))
    officers = [
        tender_doc.opening_officer_1,
        tender_doc.opening_officer_2,
        tender_doc.opening_officer_3,
    ]
    if len(set(officers)) != 3:
        frappe.throw(_("Three distinct opening officers must be assigned"))
    for officer in officers:
        if not officer:
            frappe.throw(_("All 3 opening officers must be assigned"))
        generate_otp(officer, tender)
    _log_audit(tender, frappe.session.user, "CEREMONY_OTPS_SENT", "Success")
    return {"officers": officers}
# ---- Settings Helper ----

def _get_settings():
    """Return cached Ugavi Procurement Settings singleton."""
    return frappe.get_single("Ugavi Procurement Settings")


def _otp_expiry_seconds() -> int:
    """OTP expiry in seconds from settings (default 300)."""
    return int(_get_settings().otp_expiry_minutes or 5) * 60


def _max_otp_attempts() -> int:
    """Max OTP attempts from settings (default 3)."""
    return int(_get_settings().max_otp_attempts or 3)


def _sealed_bid_enabled() -> bool:
    """Whether sealed bids are globally enabled."""
    return bool(_get_settings().sealed_bid_enabled)


# ---- OTP Management ----

def generate_otp(officer_email: str, tender_id: str) -> str:
    """Generate 6-digit OTP with configurable expiry and attempt limit."""
    otp = str(secrets.randbelow(1000000)).zfill(6)
    otp_hash = hashlib.sha256(
        f"{officer_email}:{tender_id}:{otp}:{int(time.time()/60)}".encode()
    ).hexdigest()
    expiry_secs = _otp_expiry_seconds()
    max_attempts_val = _max_otp_attempts()
    frappe.cache().setex(
        f"bid_otp:{tender_id}:{officer_email}", expiry_secs,
        json.dumps({
            "hash": otp_hash,
            "attempts": 0,
            "max_attempts": max_attempts_val,
            "expires_at": (datetime.now() + timedelta(seconds=expiry_secs)).isoformat(),
        })
    )
    _send_otp_email(officer_email, otp, tender_id)
    return otp_hash


def verify_otp(officer_email: str, tender_id: str, otp_input: str, stored_hash: str) -> bool:
    """Verify OTP with rate limiting and constant-time comparison."""
    cache_key = f"bid_otp:{tender_id}:{officer_email}"
    cached = frappe.cache().get(cache_key)
    if not cached:
        frappe.throw(_("OTP expired. Please request a new code."))
    data = json.loads(cached)
    max_attempts_val = data.get("max_attempts", _max_otp_attempts())
    if data["attempts"] >= max_attempts_val:
        frappe.cache().delete(cache_key)
        _log_audit(tender_id, officer_email, "OTP_MAX_ATTEMPTS", "Failed")
        frappe.throw(_("Max OTP attempts exceeded."))
    data["attempts"] += 1
    frappe.cache().setex(cache_key, _otp_expiry_seconds(), json.dumps(data))
    # Constant-time comparison across two time windows
    for offset in [0, -60]:
        t = int(time.time() / 60) * 60 + offset
        expected = hashlib.sha256(
            f"{officer_email}:{tender_id}:{otp_input}:{t//60}".encode()
        ).hexdigest()
        if secrets.compare_digest(expected, stored_hash):
            frappe.cache().delete(cache_key)
            _log_audit(tender_id, officer_email, "OTP_VERIFIED", "Success")
            return True
    _log_audit(tender_id, officer_email, f"OTP_FAILED_{data['attempts']}", "Failed")
    return False


# ---- Audit Logging ----

def _log_audit(tender_id: str, user: str, action: str, outcome: str):
    """Write immutable audit log entry."""
    ip = frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "N/A"
    frappe.get_doc({
        "doctype": "Audit Log",
        "tender": tender_id, "user": user,
        "action": action, "outcome": outcome,
        "ip_address": ip, "timestamp": datetime.now(),
    }).insert(ignore_permissions=True)


def _send_otp_email(email: str, otp: str, tender_id: str):
    message = f"Your OTP is {otp}. It expires shortly. Tender: {tender_id}"
    frappe.sendmail(
        recipients=[email],
        subject=f"Bid Opening OTP - {tender_id}",
        message=message,
    )
    from ugavi.integrations.sms import send_message

    send_message(email, message)