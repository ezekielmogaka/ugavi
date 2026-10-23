import frappe
from frappe import _
from frappe.utils import add_years, get_datetime, now_datetime


CONTROL_DOCTYPES = {
    "Legal Hold",
    "Record Disposal Request",
    "Record Retention Policy",
}


def enforce_record_disposal(doc, method=None):
    """Enforce configured retention, legal hold, archive, and approval controls."""
    if doc.doctype in CONTROL_DOCTYPES:
        return
    if frappe.db.exists(
        "Legal Hold",
        {
            "reference_doctype": doc.doctype,
            "reference_name": doc.name,
            "status": "Active",
        },
    ):
        frappe.throw(_("This record is under legal hold and cannot be deleted."))

    policy = frappe.db.get_value(
        "Record Retention Policy",
        {"reference_doctype": doc.doctype, "enabled": 1},
        ["name", "retention_years", "archive_before_disposal"],
        as_dict=True,
    )
    if not policy:
        return
    retention_end = add_years(get_datetime(doc.creation), int(policy.retention_years))
    if retention_end > now_datetime():
        frappe.throw(
            _("Retention policy {0} prevents deletion until {1}.").format(
                policy.name, retention_end
            )
        )

    request = frappe.db.get_value(
        "Record Disposal Request",
        {
            "reference_doctype": doc.doctype,
            "reference_name": doc.name,
            "status": "Approved",
        },
        ["name", "archive_file"],
        as_dict=True,
    )
    if not request:
        frappe.throw(_("An approved record disposal request is required."))
    if policy.archive_before_disposal and not request.archive_file:
        frappe.throw(_("The approved disposal request requires a private archive file."))
