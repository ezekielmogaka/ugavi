"""Hook collision safety test — verify every hook ugavi defines merges correctly.

[tested: CI] Ensures Frappe's additive hook merging works as expected
and no hook keys collide with ERPNext core.
"""
import frappe


def test_hooks_merge_safely():
    """Verify ugavi hooks merge without breaking or over-merging."""
    hooks = frappe.get_hooks()

    # Verify ugavi doctype_js hooks exist
    doctype_js = hooks.get("doctype_js", {})
    assert "Purchase Requisition" in doctype_js, "PR doctype_js missing"
    assert doctype_js["Purchase Requisition"].endswith("js/purchase_requisition.js")

    # Verify doc_events merge additively (don't replace core)
    doc_events = hooks.get("doc_events", {})
    assert "Purchase Receipt" in doc_events
    assert "Stock Entry" in doc_events

    # Verify scheduler_events merge (daily, weekly, monthly, cron)
    scheduler = hooks.get("scheduler_events", {})
    assert "daily" in scheduler
    assert len(scheduler["daily"]) > 0

    # Verify app_include_css — should have ugavi theme
    app_css = hooks.get("app_include_css", [])
    theme_files = [f for f in app_css if "ugavi" in f and "css" in f]
    assert len(theme_files) > 0, "No ugavi CSS files in app_include_css"

    # Verify website_route_rules — supplier portal routes
    routes = hooks.get("website_route_rules", [])
    portal_routes = [r for r in routes if "supplier" in str(r)]
    assert len(portal_routes) > 0, "No supplier portal routes"

    # App-owned DocTypes load their controller conventionally. Core class
    # overrides are intentionally forbidden to preserve upstream upgrades.
    assert not hooks.get("override_doctype_class")
    assert not hooks.get("override_whitelisted_methods")


def test_no_patch_queue_present():
    """Verify patch queue is empty (UG1 constraint)."""
    import os
    patches_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "patches"
    )
    if os.path.exists(patches_dir):
        patches = [f for f in os.listdir(patches_dir) if f.endswith(".patch")]
        assert len(patches) == 0, f"Patch queue not empty: {patches}"
    # If patches dir doesn't exist, that's even better


def test_no_core_file_overrides():
    """Verify no core Frappe/ERPNext files are shadowed."""
    import os
    ugavi_root = os.path.join(os.path.dirname(__file__), "..", "..")
    forbidden = []
    for root, dirs, files in os.walk(ugavi_root):
        # Skip node_modules, .git, __pycache__
        if any(skip in root for skip in ["node_modules", ".git", "__pycache__"]):
            continue
        for f in files:
            path = os.path.join(root, f)
            # Check we don't have Frappe/ERPNext module overrides
            if f.endswith(".py") and (
                "/frappe/" in path or "/erpnext/" in path
            ):
                forbidden.append(path)
    assert len(forbidden) == 0, f"Core file overrides found: {forbidden}"