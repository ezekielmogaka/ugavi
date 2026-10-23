import csv
import io
import json
from pathlib import Path

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file


IMPORT_RULES = {
    "Supplier": {
        "required": {"supplier_name", "supplier_type"},
        "identity": "supplier_name",
        "links": {"country": "Country"},
    },
    "Item": {
        "required": {"item_code", "item_name", "item_group", "stock_uom"},
        "identity": "item_code",
        "links": {"item_group": "Item Group", "stock_uom": "UOM"},
    },
    "Asset Register": {
        "required": {"asset_name", "asset_category", "donor"},
        "identity": "asset_tag",
        "links": {"donor": "Donor Profile", "custodian": "User", "location": "Warehouse"},
    },
    "Vehicle": {
        "required": {"license_plate", "make", "model"},
        "identity": "license_plate",
        "links": {},
    },
    "User": {
        "required": {"email", "first_name"},
        "identity": "email",
        "links": {},
    },
}


class ImportValidationRun(Document):
    @frappe.whitelist()
    def run_validation(self):
        file_doc = frappe.db.get_value(
            "File",
            {"file_url": self.source_file},
            ["name", "is_private", "file_name"],
            as_dict=True,
        )
        if not file_doc or not file_doc.is_private:
            frappe.throw(_("Import source must be an uploaded private file."))

        rows = _read_rows(file_doc.name, file_doc.file_name)
        errors = _validate_rows(self.target_doctype, rows)
        self.total_rows = len(rows)
        self.error_count = len(errors)
        self.status = "Failed" if errors else "Validated"
        self.validation_report = json.dumps(errors, indent=2)
        self.validated_by = frappe.session.user
        self.validated_at = frappe.utils.now_datetime()
        self.save()
        return {
            "status": self.status,
            "total_rows": self.total_rows,
            "error_count": self.error_count,
            "errors": errors,
            "next_step": (
                _("Correct the reported rows and validate again.")
                if errors
                else _("Create a standard Frappe Data Import using this validated file.")
            ),
        }


def _read_rows(file_name: str, source_name: str):
    extension = Path(source_name).suffix.lower()
    file_doc = frappe.get_doc("File", file_name)
    content = file_doc.get_content()
    if extension == ".csv":
        text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
        return list(csv.DictReader(io.StringIO(text)))
    if extension in {".xlsx", ".xls"}:
        values = read_xlsx_file_from_attached_file(
            fcontent=content, read_only=True
        )
        if not values:
            return []
        headers = [str(value or "").strip() for value in values[0]]
        return [
            dict(zip(headers, row, strict=False))
            for row in values[1:]
            if any(value not in (None, "") for value in row)
        ]
    frappe.throw(_("Only CSV and XLSX import files are supported."))


def _validate_rows(target_doctype: str, rows: list[dict]):
    rules = IMPORT_RULES.get(target_doctype)
    if not rules:
        frappe.throw(_("Unsupported import target."))
    errors = []
    seen = set()
    for index, row in enumerate(rows, start=2):
        for fieldname in sorted(rules["required"]):
            if row.get(fieldname) in (None, ""):
                errors.append(
                    {"row": index, "field": fieldname, "error": "Required value missing"}
                )
        identity = str(row.get(rules["identity"]) or "").strip()
        if identity:
            if identity in seen:
                errors.append(
                    {
                        "row": index,
                        "field": rules["identity"],
                        "error": "Duplicate value in import file",
                    }
                )
            seen.add(identity)
            if frappe.db.exists(target_doctype, identity):
                errors.append(
                    {
                        "row": index,
                        "field": rules["identity"],
                        "error": "Record already exists",
                    }
                )
        for fieldname, link_doctype in rules["links"].items():
            value = row.get(fieldname)
            if value and not frappe.db.exists(link_doctype, value):
                errors.append(
                    {
                        "row": index,
                        "field": fieldname,
                        "error": f"Unknown {link_doctype}: {value}",
                    }
                )
    return errors
