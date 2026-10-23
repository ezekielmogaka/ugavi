"""Rate Limiter — protecting API endpoints from abuse.

Applied to:
- Bid submission (max 3 attempts per supplier per tender)
- OTP verification (max 3 wrong attempts, then lockout)
- Login attempts
"""
import frappe
from frappe import _


class RateLimiter:
    """Simple sliding-window rate limiter using Valkey/frappe cache."""

    def __init__(self, key_prefix: str = "rate_limit"):
        self.key_prefix = key_prefix

    def check(self, action: str, identifier: str, max_attempts: int = 5,
              window_seconds: int = 300) -> bool:
        """Check if action is allowed. Returns True if allowed, raises if blocked."""
        cache_key = f"{self.key_prefix}:{action}:{identifier}"
        attempts = frappe.cache().get_value(cache_key) or 0

        if attempts >= max_attempts:
            frappe.throw(
                _("Rate limit exceeded for {0}. Try again in {1} seconds.").format(
                    action, window_seconds
                )
            )
            return False

        frappe.cache().set_value(cache_key, attempts + 1, expires_in_sec=window_seconds)
        return True

    def reset(self, action: str, identifier: str):
        """Reset rate limit counter."""
        cache_key = f"{self.key_prefix}:{action}:{identifier}"
        frappe.cache().delete_value(cache_key)


def check_bid_submission_rate(supplier: str, tender: str) -> bool:
    """Allow max 3 bid submissions per supplier per tender per hour."""
    limiter = RateLimiter("bid_submit")
    return limiter.check(f"bid:{tender}", supplier, max_attempts=3, window_seconds=3600)


def check_otp_rate(user: str) -> bool:
    """Allow max 3 OTP verification attempts per user per 5 minutes."""
    limiter = RateLimiter("otp_verify")
    return limiter.check(f"otp:{user}", user, max_attempts=3, window_seconds=300)


def check_login_rate(identifier: str) -> bool:
    """Allow max 10 login attempts per identifier per 15 minutes."""
    limiter = RateLimiter("login_attempt")
    return limiter.check("login", identifier, max_attempts=10, window_seconds=900)