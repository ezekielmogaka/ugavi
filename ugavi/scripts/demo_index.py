"""Print the LOKADO tour worksheet: evidence anchors resolved to real record IDs.

Read-only. Run with ``make demo-index`` after ``make seed-lokado``.
"""

import frappe
from frappe.utils import slug

ANCHORS = (
    ("Restricted PR", "Purchase Requisition", {"title": "Water Tanks - WASH Programme (IOM)"}),
    ("Open PR", "Purchase Requisition",
     {"title": "Construction of IOM-Supported Warehouse - Kakuma"}),
    ("Live-opening tender (solar)", "Tender", {"title": "Solar Water Pumps EU Resilience"}),
    ("Live standstill tender (livestock)", "Tender", {"title": "Livestock Galla Goats USAID"}),
    ("Complaint-window tender (motorcycles)", "Tender",
     {"title": "Field Motorcycles Peace Building USAID"}),
    ("Livestock recommendation", "Bid Evaluation Summary",
     {"tender": ("tender", "Livestock Galla Goats USAID"), "status": "Approved"}),
    ("Livestock minutes", "Evaluation Minutes",
     {"tender": ("tender", "Livestock Galla Goats USAID"), "status": "Approved"}),
    ("Motorcycles standstill", "Standstill Period",
     {"tender": ("tender", "Field Motorcycles Peace Building USAID")}),
    ("Motorcycles opening record", "Bid Opening Record",
     {"tender": ("tender", "Field Motorcycles Peace Building USAID")}),
    ("Tank payable", "Purchase Invoice", {"bill_no": "LOK-INV-LGS-1190"}),
    ("Construction payable", "Purchase Invoice", {"bill_no": "LOK-INV-TCL-0412"}),
    ("Livestock payable", "Purchase Invoice", {"bill_no": "LOK-INV-NWG-0088"}),
    ("Asset", "Asset Register", {"asset_tag": "LOK-IT-001"}),
    ("Disposed asset", "Asset Register", {"asset_tag": "LOK-OLD-001"}),
    ("Fleet source receipt", "Purchase Receipt",
     {"supplier_delivery_note": "LOKADO-DEMO-FLEET-IOM", "docstatus": 1}),
    ("Vehicle", "Vehicle", {"license_plate": "KDM 271I"}),
)


def _resolve_filters(filters: dict) -> dict:
    resolved = {}
    for field, value in filters.items():
        if isinstance(value, tuple) and value[0] == "tender":
            value = frappe.db.get_value("Tender", {"title": value[1]}, "name") or "__missing__"
        resolved[field] = value
    return resolved


def get_index() -> list[dict]:
    rows = []
    for label, doctype, filters in ANCHORS:
        meta = frappe.get_meta(doctype)
        usable = {k: v for k, v in filters.items() if k == "docstatus" or meta.has_field(k)}
        name = frappe.db.get_value(
            doctype, _resolve_filters(usable), "name", order_by="creation desc"
        )
        rows.append({
            "anchor": label,
            "doctype": doctype,
            "name": name,
            "path": f"/app/{slug(doctype)}/{name}" if name else None,
        })
    return rows


def run(base_url: str = "http://localhost:8080") -> list[dict]:
    rows = get_index()
    width = max(len(row["anchor"]) for row in rows)
    for row in rows:
        target = f"{row['name']}  {base_url}{row['path']}" if row["name"] else "NOT AVAILABLE"
        print(f"{row['anchor']:<{width}}  {target}")
    return rows
