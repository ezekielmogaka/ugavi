"""Asset Register Report — comprehensive asset listing with value summary."""
import frappe
from frappe.model.document import Document
from frappe.utils.data import now_datetime


class AssetRegisterReport(Document):
    """Full listing of assets with current book value, location, custodian."""

    @property
    def columns(self):
        return [
            {"label": "Asset Code", "fieldname": "asset_code", "fieldtype": "Data", "width": 120},
            {"label": "Asset Name", "fieldname": "asset_name", "fieldtype": "Data", "width": 200},
            {"label": "Category", "fieldname": "asset_category", "fieldtype": "Data", "width": 130},
            {"label": "Purchase Value (KES)", "fieldname": "purchase_value", "fieldtype": "Currency", "width": 150},
            {"label": "Current Book Value", "fieldname": "current_book_value", "fieldtype": "Currency", "width": 150},
            {"label": "Accum. Depreciation", "fieldname": "accumulated_depreciation", "fieldtype": "Currency", "width": 150},
            {"label": "Acquisition Date", "fieldname": "acquisition_date", "fieldtype": "Date", "width": 130},
            {"label": "Useful Life (Years)", "fieldname": "useful_life_years", "fieldtype": "Int", "width": 130},
            {"label": "Location", "fieldname": "current_location", "fieldtype": "Data", "width": 150},
            {"label": "Department", "fieldname": "custodian_department", "fieldtype": "Link", "options": "Department", "width": 150},
            {"label": "Custodian", "fieldname": "custodian", "fieldtype": "Link", "options": "Employee", "width": 150},
            {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        ]

    def get_report_data(self):
        filters = {}
        if self.asset_category:
            filters["asset_category"] = self.asset_category
        if self.status:
            filters["status"] = self.status

        assets = frappe.get_all("Asset Register",
            filters=filters,
            fields=["name", "asset_name", "asset_category", "purchase_price",
                    "purchase_date", "location", "custodian",
                    "useful_life_years", "salvage_value", "status"])

        from datetime import date
        today = date.today()
        data = []
        for a in assets:
            years_owned = 0
            if a.purchase_date:
                delta = today - getattr(a, "purchase_date", today)
                years_owned = delta.days / 365.25 if hasattr(delta, 'days') else 0

            useful_life = a.useful_life_years or 5
            depreciable = max((a.purchase_price or 0) - (a.salvage_value or 0), 0)
            yearly_dep = depreciable / useful_life if useful_life > 0 else 0
            accum_dep = min(yearly_dep * years_owned, depreciable)
            book_value = (a.purchase_price or 0) - accum_dep

            data.append({
                "asset_code": a.name,
                "asset_name": a.asset_name,
                "asset_category": a.asset_category,
                "purchase_value": a.purchase_price or 0,
                "current_book_value": round(max(book_value, 0), 2),
                "accumulated_depreciation": round(accum_dep, 2),
                "acquisition_date": str(a.purchase_date) if a.purchase_date else "",
                "useful_life_years": useful_life,
                "current_location": a.location,
                "custodian_department": "",
                "custodian": a.custodian,
                "status": a.status or "Active",
            })

        return data

    @property
    def summary(self):
        data = self.get_report_data()
        total_purchase = sum(d["purchase_value"] for d in data)
        total_book = sum(d["current_book_value"] for d in data)
        total_dep = sum(d["accumulated_depreciation"] for d in data)
        return {
            "asset_count": len(data),
            "total_purchase_value": total_purchase,
            "total_book_value": round(total_book, 2),
            "total_accumulated_depreciation": round(total_dep, 2),
        }

    def generate(self):
        self.generated_at = now_datetime()
        self.report_data = frappe.as_json(self.get_report_data())
        self.save()