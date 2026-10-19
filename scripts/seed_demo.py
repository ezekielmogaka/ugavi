"""Seed Demo Data for Ugavi.

Creates: 2 donors, ~30 suppliers, items, warehouses, users, 3 vehicles,
and sample tenders at 150K / 350K / 800K KES.
"""
import frappe
import random
from datetime import datetime, timedelta


def run():
    frappe.logger().info("Starting Ugavi seed data...")
    create_donors()
    create_suppliers()
    create_warehouses()
    create_items()
    create_users()
    create_vehicles()
    create_sample_tenders()
    create_procurement_settings()
    frappe.db.commit()
    frappe.logger().info("Ugavi seed data complete!")


def create_donors():
    donors = [
        {"name": "USAID Kenya", "donor_code": "USAID-KE", "currency": "KES",
         "grant_reference": "USAID-720615-2024",
         "grant_start": "2024-01-01", "grant_end": "2027-12-31"},
        {"name": "The Global Fund", "donor_code": "GF-KE", "currency": "KES",
         "grant_reference": "GF-KEN-2024-001",
         "grant_start": "2024-01-01", "grant_end": "2026-12-31"},
    ]
    for d in donors:
        if not frappe.db.exists("Donor Profile", d["name"]):
            frappe.get_doc({"doctype": "Donor Profile", **d}).insert(ignore_permissions=True)
            print(f"  Donor: {d['name']}")
def create_suppliers():
    categories = ["Medical Supplies", "Pharmaceuticals", "Food & Nutrition",
                  "IT Equipment", "Office Supplies", "Vehicles & Spares",
                  "Construction", "Consulting", "Transport & Logistics"]
    for i in range(1, 31):
        name = f"Supplier {i:03d} Ltd"
        if frappe.db.exists("Supplier", name):
            continue
        preq = i <= 20
        cat = random.choice(categories)
        supplier = frappe.get_doc({
            "doctype": "Supplier", "supplier_name": name,
            "supplier_group": "Local", "country": "Kenya",
            "supplier_type": "Company", "tax_id": f"P05123456{i:02d}Z",
            "custom_prequalification_status": "Prequalified" if preq else "Not Prequalified",
            "custom_prequalification_category": cat if preq else "",
        })
        supplier.insert(ignore_permissions=True)
        print(f"  Supplier: {name} (Prequalified: {preq})")


def create_warehouses():
    for code in ["USAID", "GF"]:
        for wh in ["Main Store", "Medical Store", "Field Office"]:
            wh_name = f"{code} - {wh}"
            if not frappe.db.exists("Warehouse", wh_name):
                frappe.get_doc({
                    "doctype": "Warehouse", "warehouse_name": wh_name,
                    "parent_warehouse": "Stores - U", "company": "Ugavi NGO",
                }).insert(ignore_permissions=True)
                print(f"  Warehouse: {wh_name}")


def create_items():
    items = [
        ("ITM-MED-001", "Malaria Test Kit (RDT)", "Medical Supplies", 150),
        ("ITM-MED-002", "HIV Test Kit", "Medical Supplies", 200),
        ("ITM-PHA-001", "Artemether-Lumefantrine 20/120mg", "Pharmaceuticals", 350),
        ("ITM-PHA-002", "ARV Tenofovir 300mg", "Pharmaceuticals", 500),
        ("ITM-IT-001", "Laptop - Dell Latitude", "IT Equipment", 85000),
        ("ITM-OFF-001", "A4 Paper Ream", "Office Supplies", 450),
        ("ITM-VEH-002", "Fuel - Diesel", "Vehicles & Spares", 180),
        ("ITM-VEH-003", "Oil Filter - Genuine", "Vehicles & Spares", 2500),
    ]
    for code, name, grp, rate in items:
        if not frappe.db.exists("Item", code):
            frappe.get_doc({
                "doctype": "Item", "item_code": code, "item_name": name,
                "item_group": grp, "stock_uom": "Nos",
                "valuation_rate": rate, "is_stock_item": 1,
            }).insert(ignore_permissions=True)
            print(f"  Item: {code}")


def create_users():
    role_map = {
        "requester@ugavi.local": ["Program Staff"],
        "approver1@ugavi.local": ["Approver Level 1"],
        "approver2@ugavi.local": ["Approver Level 2"],
        "procurement@ugavi.local": ["Procurement Officer"],
        "bid_officer1@ugavi.local": ["Bid Opening Officer"],
        "bid_officer2@ugavi.local": ["Bid Opening Officer"],
        "bid_officer3@ugavi.local": ["Bid Opening Officer"],
        "storekeeper@ugavi.local": ["Store Keeper"],
        "fleet@ugavi.local": ["Fleet Manager"],
        "auditor@ugavi.local": ["Auditor"],
        "supplier1@supplier.co.ke": ["Supplier Portal User"],
    }
    for email, roles in role_map.items():
        if not frappe.db.exists("User", email):
            name = email.split("@")[0].replace("_", " ").title()
            user = frappe.get_doc({
                "doctype": "User", "email": email, "first_name": name,
                "send_welcome_email": 0, "enabled": 1,
                "new_password": "Ugavi@2024!",
                "roles": [{"role": r} for r in roles],
            })
            user.insert(ignore_permissions=True)
            print(f"  User: {email}")


def create_vehicles():
    vehicles = [
        ("KBZ 001A", "Toyota Land Cruiser", "SUV", "Diesel", "2023-01-15"),
        ("KCA 234B", "Toyota Hilux", "Pickup", "Diesel", "2022-06-01"),
        ("KDD 567C", "Nissan Patrol", "SUV", "Petrol", "2021-03-10"),
    ]
    for plate, make, vtype, fuel, reg_date in vehicles:
        if not frappe.db.exists("Vehicle", plate):
            frappe.get_doc({
                "doctype": "Vehicle", "license_plate": plate,
                "make": make, "vehicle_type": vtype,
                "fuel_type": fuel, "registration_date": reg_date,
            }).insert(ignore_permissions=True)
            print(f"  Vehicle: {plate}")


def create_sample_tenders():
    tenders = [
        ("TENDER-150K", "Office Supplies - Direct", 150000, "Request for Quotation (Direct)", "USAID Kenya"),
        ("TENDER-350K", "Medical Supplies - Restricted", 350000, "Restricted Tender", "The Global Fund"),
        ("TENDER-800K", "Vehicle Purchase - Open", 800000, "Open Tender", "USAID Kenya"),
    ]
    for tid, title, val, method, donor in tenders:
        if not frappe.db.exists("Tender", tid):
            frappe.get_doc({
                "doctype": "Tender", "title": title,
                "estimated_value": val, "procurement_method": method,
                "donor": donor, "status": "Draft",
                "deadline": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
            }).insert(ignore_permissions=True)
            print(f"  Tender: {title} ({val:,} KES)")


def create_procurement_settings():
    if not frappe.db.exists("Ugavi Procurement Settings", "Ugavi Procurement Settings"):
        frappe.get_doc({
            "doctype": "Ugavi Procurement Settings",
            "direct_threshold": 200000,
            "restricted_threshold": 500000,
            "open_threshold": 500000,
            "default_currency": "KES",
        }).insert(ignore_permissions=True)
        print("  Procurement Settings created")