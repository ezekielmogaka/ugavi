"""Tests for sealed-bid crypto and DoA chain validation."""
import unittest
import secrets


class TestSealedBidCrypto(unittest.TestCase):
    """Test Shamir's Secret Sharing and encryption."""

    def test_split_and_reconstruct(self):
        """3-of-3 split should reconstruct the original secret."""
        from ugavi.procurement.services.sealed_bid import (
            split_secret, reconstruct_secret,
        )
        original = secrets.randbelow(2**256)
        shares = split_secret(original, n=3, k=3)
        self.assertEqual(len(shares), 3)
        reconstructed = reconstruct_secret(shares)
        self.assertEqual(original, reconstructed)

    def test_two_shares_cannot_reconstruct(self):
        """Any 2 shares must not reconstruct the secret."""
        from ugavi.procurement.services.sealed_bid import (
            split_secret, reconstruct_secret,
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
        vals1 = set(s[1] for s in shares1)
        vals2 = set(s[1] for s in shares2)
        self.assertNotEqual(vals1, vals2)


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