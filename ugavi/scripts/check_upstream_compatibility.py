"""Fail fast on extension patterns that make ERPNext upgrades unsafe."""

import json
from pathlib import Path

import frappe
from frappe import _

FORBIDDEN_HOOKS = {
    "override_doctype_class",
    "override_whitelisted_methods",
}


def _doctype_names(app: str) -> set[str]:
    app_path = Path(frappe.get_app_path(app))
    names = set()
    for schema_path in app_path.rglob("doctype/**/*.json"):
        try:
            schema = json.loads(schema_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if (
            isinstance(schema, dict)
            and schema.get("doctype") == "DocType"
            and schema.get("name")
        ):
            names.add(schema["name"])
    return names


def _missing_controllers(app: str) -> list[str]:
    app_path = Path(frappe.get_app_path(app))
    missing = []
    for schema_path in app_path.rglob("doctype/**/*.json"):
        try:
            schema = json.loads(schema_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if (
            isinstance(schema, dict)
            and schema.get("doctype") == "DocType"
            and schema.get("name")
            and not schema.get("istable")
            and not schema_path.with_suffix(".py").exists()
        ):
            missing.append(schema["name"])
    return sorted(missing)


def get_report() -> dict:
    """Return an upgrade-safety report for the installed source trees."""
    from ugavi import hooks

    forbidden_hooks = sorted(
        hook for hook in FORBIDDEN_HOOKS if getattr(hooks, hook, None)
    )
    collisions = sorted(_doctype_names("ugavi") & _doctype_names("erpnext"))
    missing_controllers = _missing_controllers("ugavi")
    website_css = list(getattr(hooks, "web_include_css", []))
    missing_web_assets = [
        asset
        for asset in (
            "/assets/ugavi/css/ugavi-tokens.css",
            "/assets/ugavi/css/ugavi-components.css",
            "/assets/ugavi/css/ugavi-portal.css",
        )
        if asset not in website_css
    ]
    issues = []
    if forbidden_hooks:
        issues.append(f"Forbidden core override hooks: {', '.join(forbidden_hooks)}")
    if collisions:
        issues.append(f"ERPNext DocType name collisions: {', '.join(collisions)}")
    if missing_controllers:
        issues.append(
            "App DocTypes missing conventional controllers: "
            + ", ".join(missing_controllers)
        )
    if missing_web_assets:
        issues.append(f"Missing supplier portal assets: {', '.join(missing_web_assets)}")
    return {
        "compatible": not issues,
        "issues": issues,
        "missing_controllers": missing_controllers,
        "ugavi_doctypes": len(_doctype_names("ugavi")),
        "erpnext_doctypes": len(_doctype_names("erpnext")),
    }


def run() -> dict:
    """Bench entry point used by CI and upgrade rehearsals."""
    report = get_report()
    if not report["compatible"]:
        frappe.throw(
            _("ERPNext upstream compatibility checks failed: {0}").format(
                "; ".join(report["issues"])
            )
        )
    print(json.dumps(report, indent=2))
    return report
