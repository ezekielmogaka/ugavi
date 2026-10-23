"""Health check — system health verification for monitoring."""
import frappe
from frappe.utils import now_datetime


@frappe.whitelist()
def health_check():
    """Return system health status as JSON.
    
    Checks:
    - Database connectivity
    - Cache connectivity (Valkey)
    - App version
    - Uptime
    """
    import frappe
    
    health = {
        "status": "healthy",
        "app": "ugavi",
        "version": frappe.get_attr("ugavi.__version__") if hasattr(frappe, "get_attr") else "0.1.0",
        "timestamp": str(now_datetime()),
        "checks": {},
    }

    # Database check
    try:
        frappe.db.sql("SELECT 1")
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {e}"
        health["status"] = "degraded"

    # Cache check (Valkey)
    try:
        frappe.cache().set_value("__health_check__", "ok", expires_in_sec=10)
        health["checks"]["cache"] = "ok"
    except Exception as e:
        health["checks"]["cache"] = f"error: {e}"
        health["status"] = "degraded"

    # Site info
    health["site"] = frappe.local.site
    health["db_name"] = frappe.conf.db_name

    return health


def get_version():
    """Return app version."""
    return "0.1.0"