"""Structured JSON Logging — machine-readable audit trail.

Outputs all Ugavi events as JSON to a rotating log file,
enabling log aggregation (Fluentd, Logstash, Loki).
"""
import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional


_json_logger = None


def _get_logger():
    """Lazy-init the JSON logger."""
    global _json_logger
    if _json_logger is not None:
        return _json_logger

    _json_logger = logging.getLogger("ugavi.structured")
    _json_logger.setLevel(logging.INFO)

    # Don't add handlers if already configured
    if _json_logger.handlers:
        return _json_logger

    log_dir = os.path.join(os.path.expanduser("~"), "frappe-bench", "logs")
    os.makedirs(log_dir, exist_ok=True)

    handler = RotatingFileHandler(
        os.path.join(log_dir, "ugavi-structured.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=7,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    _json_logger.addHandler(handler)
    _json_logger.propagate = False

    return _json_logger


def log_event(event_type: str, details: Optional[Dict[str, Any]] = None,
              user: Optional[str] = None, severity: str = "INFO") -> None:
    """Emit a structured JSON log entry.

    Args:
        event_type: Category (e.g., "bid.submission", "tender.opening", "auth.login")
        details: Arbitrary key-value payload
        user: Actor (defaults to frappe.session.user)
        severity: INFO|WARNING|ERROR|CRITICAL
    """
    import frappe
    try:
        actor = user or frappe.session.user
    except Exception:
        actor = "system"

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "app": "ugavi",
        "version": frappe.get_attr("ugavi.__version__") or "0.1.0",
        "event": event_type,
        "severity": severity,
        "user": actor,
        "site": frappe.local.site if hasattr(frappe.local, "site") else "unknown",
        "details": details or {},
    }

    logger = _get_logger()
    getattr(logger, severity.lower(), logger.info)(json.dumps(entry, default=str))


# Convenience aliases for common events
def log_bid_submission(tender: str, supplier: str, bid_name: str):
    log_event("bid.submission", {"tender": tender, "supplier": supplier, "bid": bid_name})

def log_bid_opening(tender: str, opened_by: str, bid_count: int):
    log_event("bid.opening", {"tender": tender, "opened_by": opened_by, "bid_count": bid_count})

def log_auth_event(event: str, user: str, success: bool, ip: Optional[str] = None):
    log_event(f"auth.{event}", {"user": user, "success": success, "ip": ip},
              severity="WARNING" if not success else "INFO")

def log_db_write(doctype: str, docname: str, action: str):
    log_event("db.write", {"doctype": doctype, "docname": docname, "action": action})

def log_error(error_type: str, message: str, stack_trace: Optional[str] = None):
    log_event("error", {"type": error_type, "message": message, "stack": stack_trace},
              severity="ERROR")