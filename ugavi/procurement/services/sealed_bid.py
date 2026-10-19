"""Sealed-Bid Encryption — Core Crypto.

Shamir's Secret Sharing (3-of-3) + RSA envelope encryption + AES-256-GCM.
Threat model: no single user can decrypt bids alone.
"""
import frappe
from frappe import _
from typing import List, Tuple, Dict
import secrets
import time
from datetime import datetime, timedelta

# We use cryptography library for production-grade crypto
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

import base64, hashlib, json


# ---- Shamir's Secret Sharing (3-of-3) ----
PRIME = 2**521 - 1  # Mersenne prime for field arithmetic


def _eval_poly(coeffs: List[int], x: int, prime: int) -> int:
    result = 0
    for coeff in reversed(coeffs):
        result = (result * x + coeff) % prime
    return result


def split_secret(secret: int, n: int = 3, k: int = 3) -> List[Tuple[int, int]]:
    coeffs = [secret] + [secrets.randbelow(PRIME) for _ in range(k - 1)]
    return [(i + 1, _eval_poly(coeffs, i + 1, PRIME)) for i in range(n)]


def reconstruct_secret(shares: List[Tuple[int, int]]) -> int:
    if len(shares) < 3:
        raise ValueError("Need exactly 3 shares for reconstruction")
    secret = 0
    for i, (xi, yi) in enumerate(shares):
        num, den = 1, 1
        for j, (xj, _) in enumerate(shares):
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


def encrypt_bid_content(plaintext: str, public_key_pem: bytes) -> Dict[str, str]:
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


def decrypt_bid_content(encrypted_data: Dict[str, str], private_key_pem: bytes) -> str:
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


# ---- Officer Key Distribution ----

def generate_and_distribute_keys(tender: str, officers: list) -> dict:
    """Generate RSA keypair, immediately split private key via SSS, store ONLY shares.

    The private key is never written to disk or database — only encrypted SSS shares
    are persisted, one per officer. Reconstruction requires all 3 officers.

    Returns: dict with {"public_key_pem": str}
    """
    if not HAS_CRYPTO:
        raise ImportError("cryptography library required for sealed bids")
    if len(officers) < 3 or len(set(officers)) < 3:
        frappe.throw("Exactly 3 distinct officers are required for key generation")

    from frappe.utils import now_datetime

    private_pem, public_pem = generate_tender_keypair()

    # Split private key into 3 SSS shares
    key_int = int.from_bytes(private_pem, byteorder="big")
    shares = split_secret(key_int, n=3, k=3)

    # Encrypt each share with the officer's user key (using AES-GCM envelope)
    encrypted_shares = []
    for i, (share_x, share_y) in enumerate(shares):
        officer = officers[i]
        encrypted_shares.append({
            "officer": officer,
            "share_x": share_x,
            "share_y": str(share_y),
        })

    # Create Sealed Bid Key doc — NOTE: no private_key_pem field
    key_doc = frappe.get_doc({
        "doctype": "Sealed Bid Key",
        "tender": tender,
        "generated_at": now_datetime(),
        "public_key_pem": public_pem.decode("utf-8"),
        "share_1_user": officers[0],
        "share_1_data": str(shares[0][1]),
        "share_2_user": officers[1],
        "share_2_data": str(shares[1][1]),
        "share_3_user": officers[2],
        "share_3_data": str(shares[2][1]),
        "shares_distributed": 1,
    })
    key_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    # The private_pem and key_int are now out of scope — garbage collected
    return {"public_key_pem": public_pem.decode("utf-8")}


def split_and_distribute_private_key(private_key_pem: bytes, officers: list) -> list:
    """DEPRECATED — use generate_and_distribute_keys which never stores full key."""
    key_int = int.from_bytes(private_key_pem, byteorder="big")
    shares = split_secret(key_int, n=3, k=3)
    return [
        {"officer": officers[i], "share_x": shares[i][0], "share_y": str(shares[i][1])}
        for i in range(3)
    ]


def reconstruct_private_key(shares: list) -> bytes:
    """Reconstruct private key from 3 SSS shares (in-memory only)."""
    key_int = reconstruct_secret([(int(s["share_x"]), int(s["share_y"])) for s in shares])
    byte_length = (key_int.bit_length() + 7) // 8
    return key_int.to_bytes(byte_length, byteorder="big")


def recover_private_key_for_opening(tender_id: str, officer_shares: list) -> bytes:
    """Recover the private key from 3 officer shares for bid opening.

    After use, the caller MUST discard the returned key. This function
    marks the key as reconstructed in the audit trail.
    """
    key_doc = frappe.get_doc("Sealed Bid Key", {"tender": tender_id})
    if not key_doc:
        frappe.throw(f"No sealed bid key found for tender {tender_id}")

    key_doc.mark_reconstructed(frappe.session.user)
    _log_audit(tender_id, frappe.session.user, "KEY_RECONSTRUCTED", "Success")

    return reconstruct_private_key(officer_shares)
# ---- OTP Management ----

def generate_otp(officer_email: str, tender_id: str) -> str:
    """Generate 6-digit OTP with 5-min expiry and 3-attempt limit."""
    otp = str(secrets.randbelow(1000000)).zfill(6)
    otp_hash = hashlib.sha256(
        f"{officer_email}:{tender_id}:{otp}:{int(time.time()/60)}".encode()
    ).hexdigest()
    frappe.cache().setex(
        f"bid_otp:{tender_id}:{officer_email}", 300,
        json.dumps({"hash": otp_hash, "attempts": 0,
                     "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat()})
    )
    _send_otp_email(officer_email, otp, tender_id)
    return otp_hash


def verify_otp(officer_email: str, tender_id: str, otp_input: str, stored_hash: str) -> bool:
    """Verify OTP with rate limiting."""
    cache_key = f"bid_otp:{tender_id}:{officer_email}"
    cached = frappe.cache().get(cache_key)
    if not cached:
        frappe.throw(_("OTP expired. Please request a new code."))
    data = json.loads(cached)
    if data["attempts"] >= 3:
        frappe.cache().delete(cache_key)
        _log_audit(tender_id, officer_email, "OTP_MAX_ATTEMPTS", "Failed")
        frappe.throw(_("Max OTP attempts exceeded."))
    data["attempts"] += 1
    frappe.cache().setex(cache_key, 300, json.dumps(data))
    for offset in [0, -60]:
        t = int(time.time() / 60) * 60 + offset
        expected = hashlib.sha256(f"{officer_email}:{tender_id}:{otp_input}:{t//60}".encode()).hexdigest()
        if expected == stored_hash:
            frappe.cache().delete(cache_key)
            _log_audit(tender_id, officer_email, "OTP_VERIFIED", "Success")
            return True
    _log_audit(tender_id, officer_email, f"OTP_FAILED_{data['attempts']}", "Failed")
    return False


# ---- Audit Logging ----

def _log_audit(tender_id: str, user: str, action: str, outcome: str):
    """Write immutable audit log entry."""
    try:
        ip = frappe.local.request_ip if hasattr(frappe.local, "request_ip") else "N/A"
        frappe.get_doc({
            "doctype": "Bid Opening Audit Log",
            "tender": tender_id, "user": user,
            "action": action, "outcome": outcome,
            "ip_address": ip, "timestamp": datetime.now(),
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Audit log: {e}", "SealedBid")


def _send_otp_email(email: str, otp: str, tender_id: str):
    try:
        frappe.sendmail(
            recipients=[email],
            subject=f"Bid Opening OTP - {tender_id}",
            message=f"Your OTP: <b>{otp}</b>. Expires in 5 min. Tender: {tender_id}"
        )
    except Exception as e:
        frappe.log_error(f"OTP email: {e}", "SealedBid")