"""Tests for sealed-bid crypto and DoA chain validation."""
import secrets
import unittest
from unittest.mock import ANY, patch


class TestSealedBidCrypto(unittest.TestCase):
    """Test Shamir's Secret Sharing and encryption."""

    def test_split_and_reconstruct(self):
        """3-of-3 split should reconstruct the original secret."""
        from ugavi.procurement.services.sealed_bid import (
            reconstruct_secret,
            split_secret,
        )
        original = secrets.randbelow(2**256)
        shares = split_secret(original, n=3, k=3)
        self.assertEqual(len(shares), 3)
        reconstructed = reconstruct_secret(shares)
        self.assertEqual(original, reconstructed)

    def test_two_shares_cannot_reconstruct(self):
        """Any 2 shares must not reconstruct the secret."""
        from ugavi.procurement.services.sealed_bid import (
            reconstruct_secret,
            split_secret,
        )
        original = secrets.randbelow(2**256)
        shares = split_secret(original, n=3, k=3)
        with self.assertRaises(ValueError):
            reconstruct_secret(shares[:2])

    def test_different_secrets(self):
        """Two different secrets produce different shares."""
        from ugavi.procurement.services.sealed_bid import split_secret
        shares1 = split_secret(12345, n=3, k=3)
        shares2 = split_secret(54321, n=3, k=3)
        vals1 = {s[1] for s in shares1}
        vals2 = {s[1] for s in shares2}
        self.assertNotEqual(vals1, vals2)

    def test_rsa_private_key_round_trip_uses_wrapping_key(self):
        """A full RSA PEM must be wrapped, not reduced into the SSS field."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        from ugavi.procurement.services.sealed_bid import (
            generate_tender_keypair,
            reconstruct_secret,
            split_secret,
        )

        private_pem, _public_pem = generate_tender_keypair()
        wrapping_key = AESGCM.generate_key(bit_length=256)
        nonce = secrets.token_bytes(12)
        encrypted = AESGCM(wrapping_key).encrypt(nonce, private_pem, b"TND-TEST")
        shares = split_secret(int.from_bytes(wrapping_key, byteorder="big"))
        reconstructed = reconstruct_secret(shares).to_bytes(32, byteorder="big")
        restored_pem = AESGCM(reconstructed).decrypt(nonce, encrypted, b"TND-TEST")

        self.assertEqual(restored_pem, private_pem)
        serialization.load_pem_private_key(restored_pem, password=None)


class TestDelegationOfAuthority(unittest.TestCase):
    """Test the DoA chain validation."""

    def test_rejects_empty_chain(self):
        from ugavi.procurement.services.delegation_of_authority import validate_approval_chain
        self.assertFalse(validate_approval_chain([]))

    def test_rejects_duplicate_roles(self):
        from ugavi.procurement.services.delegation_of_authority import validate_approval_chain
        chain = [
            {"role": "Approver Level 1", "user": None, "min_amount": 0},
            {"role": "Approver Level 1", "user": None, "min_amount": 50000},
        ]
        self.assertFalse(validate_approval_chain(chain))

    def test_accepts_valid_chain(self):
        from ugavi.procurement.services.delegation_of_authority import validate_approval_chain
        chain = [
            {"role": "Supervisor", "user": None, "min_amount": 0},
            {"role": "Manager", "user": None, "min_amount": 200000},
            {"role": "Director", "user": None, "min_amount": 500000},
        ]
        self.assertTrue(validate_approval_chain(chain))


class TestOTP(unittest.TestCase):
    """Test OTP generation and verification (frappe context required)."""

    def test_generate_otp_returns_hash(self):
        """OTP generation returns a SHA-256 hex string."""
        from ugavi.procurement.services.sealed_bid import generate_otp
        with patch(
            "ugavi.procurement.services.sealed_bid._send_otp_email"
        ) as send_email:
            test_hash = generate_otp("test@example.com", "TEST-TENDER-001")
        self.assertEqual(len(test_hash), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in test_hash))
        send_email.assert_called_once_with(
            "test@example.com", ANY, "TEST-TENDER-001"
        )

    def _issue(self, email, tender):
        from ugavi.procurement.services.sealed_bid import generate_otp
        with patch("ugavi.procurement.services.sealed_bid._send_otp_email") as send_email:
            generate_otp(email, tender)
        return send_email.call_args.args[1]

    def tearDown(self):
        import frappe
        for key in ("TEST-002:test2@example.com", "TEST-003:test3@example.com",
                    "TEST-004:test4@example.com", "TEST-005:test5@example.com"):
            frappe.cache().delete(f"bid_otp:{key}")

    def test_verify_otp_correct(self):
        """Correct OTP verifies once and is consumed by default."""
        import frappe

        from ugavi.procurement.services.sealed_bid import verify_otp
        otp = self._issue("test2@example.com", "TEST-002")
        with patch("ugavi.procurement.services.sealed_bid._log_audit") as audit:
            self.assertTrue(verify_otp("test2@example.com", "TEST-002", otp))
        audit.assert_called_once_with(
            "TEST-002", "test2@example.com", "OTP_VERIFIED", "Success"
        )
        self.assertIsNone(frappe.cache().get("bid_otp:TEST-002:test2@example.com"))

    def test_verify_otp_wrong_code(self):
        """Wrong OTP returns False and keeps the code usable."""
        from ugavi.procurement.services.sealed_bid import verify_otp
        otp = self._issue("test3@example.com", "TEST-003")
        wrong = "000000" if otp != "000000" else "111111"
        with patch("ugavi.procurement.services.sealed_bid._log_audit") as audit:
            self.assertFalse(verify_otp("test3@example.com", "TEST-003", wrong))
            self.assertTrue(verify_otp("test3@example.com", "TEST-003", otp))
        audit.assert_any_call("TEST-003", "test3@example.com", "OTP_FAILED_1", "Failed")

    def test_otp_valid_for_configured_window_not_clock_minute(self):
        """Codes stay valid across minute boundaries until the configured expiry."""
        import time

        import frappe

        from ugavi.procurement.services.sealed_bid import _otp_expiry_seconds, verify_otp
        otp = self._issue("test4@example.com", "TEST-004")
        later = time.time() + min(240, _otp_expiry_seconds() - 30)
        with patch("ugavi.procurement.services.sealed_bid._log_audit"), \
                patch("ugavi.procurement.services.sealed_bid.time.time", return_value=later):
            self.assertTrue(verify_otp("test4@example.com", "TEST-004", otp, consume=False))
        expired = time.time() + _otp_expiry_seconds() + 1
        with patch("ugavi.procurement.services.sealed_bid._log_audit"), \
                patch("ugavi.procurement.services.sealed_bid.time.time", return_value=expired):
            with self.assertRaises(frappe.ValidationError):
                verify_otp("test4@example.com", "TEST-004", otp)

    def test_non_consuming_verification_keeps_code(self):
        """Ceremony verification must not burn codes before all officers pass."""
        from ugavi.procurement.services.sealed_bid import verify_otp
        otp = self._issue("test5@example.com", "TEST-005")
        with patch("ugavi.procurement.services.sealed_bid._log_audit"):
            self.assertTrue(verify_otp("test5@example.com", "TEST-005", otp, consume=False))
            self.assertTrue(verify_otp("test5@example.com", "TEST-005", otp, consume=False))

    def test_otp_uses_secrets_compare_digest(self):
        """confirm secrets.compare_digest is imported (constant-time comparison)."""
        import inspect

        from ugavi.procurement.services import sealed_bid as sb
        source = inspect.getsource(sb.verify_otp)
        self.assertIn("secrets.compare_digest", source)