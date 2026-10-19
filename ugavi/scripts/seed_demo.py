"""Seed demo data for Ugavi - uses only standard ERPNext DocTypes."""
import frappe
from frappe.utils import nowdate


def run():
    frappe.logger().info("Seeding Ugavi demo data...")
    create_suppliers()
    create_warehouses()
    create_items()
    create_demo_users()
    create_sample_pos()
    frappe.db.commit()
    frappe.logger().info("Ugavi seed data complete!")


def create_suppliers():
    names = [
        "Kenya Medical Supplies", "East Africa Logistics", "Tech Solutions Kenya",
        "Office Equip Africa", "Nairobi Builders Ltd", "Safari Pharmaceuticals",
        "Highland Printers Ltd", "Coast Engineering Works", "Great Rift Transporters",
        "Lake Basin IT Services", "Mount Kenya Foods", "Solar Solutions EA",
        "Green Energy Africa", "Aqua Pure Kenya", "Secure Guard Services",
        "Fast Track Couriers", "Digital Print Hub", "MediEquip Africa",
        "Civil Works Contractors", "Data Networks Ltd", "Premier Consulting Group",
        "Urban Architects Ltd", "Lab Supplies Kenya", "Farm Fresh Produce",
        "Safety First Equipment", "Clean Energy Solutions", "Top Notch Catering",
        "Auto Parts Express", "Water-Tech Engineering", "Edu Supplies Ltd",
    ]
    for name in names:
        if not frappe.db.exists("Supplier", {"supplier_name": name}):
            frappe.get_doc({
                "doctype": "Supplier", "supplier_name": name,
                "supplier_group": "Services", "supplier_type": "Company",
                "country": "Kenya",
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  Created {len(names)} suppliers")


def create_warehouses():
    wh_list = [
        "USAID Main Store - Nairobi",
        "USAID Field Store - Kisumu",
        "Global Fund Warehouse - Mombasa",
        "Global Fund Store - Eldoret",
        "Main Transit Warehouse - Nairobi",
        "Cold Chain Storage - Nairobi",
    ]
    company = frappe.defaults.get_default("company")
    for wh_name in wh_list:
        if not frappe.db.exists("Warehouse", {"warehouse_name": wh_name}):
            frappe.get_doc({
                "doctype": "Warehouse", "warehouse_name": wh_name,
                "warehouse_type": "Transit", "company": company,
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  Created {len(wh_list)} warehouses")


def create_items():
    items = [
        ("ANTIMALARIAL-ALU", "Antimalarial Tablets (ALU)", "Drugs"),
        ("HIV-RAPID-TEST", "HIV Rapid Test Kit", "Drugs"),
        ("LLIN-NET", "Mosquito Net - LLIN", "Consumable"),
        ("FIRST-AID-KIT", "First Aid Kit", "Consumable"),
        ("STATIONERY-PACK", "Office Stationery Pack", "Consumable"),
        ("LAPTOP-DELL", "Laptop - Dell Latitude", "Products"),
        ("GENERATOR-50KVA", "Generator - 50kVA", "Products"),
        ("FUEL-DIESEL", "Fuel - Diesel", "Consumable"),
    ]
    for code, name, grp in items:
        if not frappe.db.exists("Item", code):
            frappe.get_doc({
                "doctype": "Item", "item_code": code, "item_name": name,
                "item_group": grp, "stock_uom": "Nos",
                "valuation_rate": 0, "is_stock_item": 1,
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  Created {len(items)} items")
def create_demo_users():
    users = [
        ("jane.procurement@ugavi.local", "Jane", "Wanjiku", "Procurement Officer"),
        ("tom.logistics@ugavi.local", "Tom", "Odhiambo", "Store Keeper"),
        ("mary.audit@ugavi.local", "Mary", "Wambui", "Auditor"),
        ("peter.fleet@ugavi.local", "Peter", "Mwangi", "Fleet Manager"),
    ]
    for email, first, last, role in users:
        if not frappe.db.exists("User", email):
            frappe.get_doc({
                "doctype": "User", "email": email, "first_name": first,
                "last_name": last, "send_welcome_email": 0, "enabled": 1,
                "roles": [{"role": role}],
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  Created {len(users)} demo users")


def create_sample_pos():
    suppliers = frappe.get_all("Supplier", limit=1)
    items = frappe.get_all("Item", limit=3)
    if not suppliers or not items:
        return
    for i in range(2):
        po_name = f"PO-DEMO-{i+1:04d}"
        if not frappe.db.exists("Purchase Order", po_name):
            frappe.get_doc({
                "doctype": "Purchase Order",
                "supplier": suppliers[0].name,
                "schedule_date": nowdate(),
                "items": [{
                    "item_code": items[i].name,
                    "qty": 100.0,
                    "rate": 500.0,
                    "schedule_date": nowdate(),
                }],
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("  Created sample purchase orders")