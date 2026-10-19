"""Bootstrap ERPNext foundation + seed Ugavi demo data."""
import frappe
from frappe.utils import nowdate


def run():
    """Complete ERPNext setup, then seed demo data."""
    setup_company()
    create_supplier_groups()
    create_item_groups()
    create_suppliers()
    create_warehouses()
    create_items()
    create_demo_users()
    create_donor_profiles()
    setup_procurement_settings()
    frappe.db.commit()
    print("Ugavi seed data complete!")


def setup_company():
    if frappe.db.exists("Company", "Ugavi NGO"):
        print("  Company already exists")
        return
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
    setup_complete({
        "company_name": "Ugavi NGO",
        "company_abbr": "UG",
        "country": "Kenya",
        "currency": "KES",
        "timezone": "Africa/Nairobi",
        "chart_of_accounts": "Standard",
        "fy_start_date": "2024-01-01",
        "fy_end_date": "2024-12-31",
        "domains": ["Distribution"],
        "language": "English",
    })
    print("  Company + Chart of Accounts created")


def create_supplier_groups():
    groups = ["Local", "International", "Services", "Raw Material"]
    for g in groups:
        if not frappe.db.exists("Supplier Group", g):
            frappe.get_doc({
                "doctype": "Supplier Group",
                "supplier_group_name": g,
            }).insert(ignore_permissions=True)
    print(f"  Supplier Groups: {groups}")


def create_item_groups():
    groups = ["Medical Supplies", "Pharmaceuticals", "Consumable",
              "IT Equipment", "Office Supplies", "Vehicles & Spares",
              "Drugs", "Products"]
    for g in groups:
        if not frappe.db.exists("Item Group", g):
            frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": g,
            }).insert(ignore_permissions=True)
    print(f"  Item Groups: {groups}")
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
                "supplier_group": "Local", "supplier_type": "Company",
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
    company = frappe.defaults.get_defaults().get("company") or "Ugavi NGO"
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
        ("ANTIMALARIAL-ALU", "Antimalarial Tablets (ALU)", "Pharmaceuticals"),
        ("HIV-RAPID-TEST", "HIV Rapid Test Kit", "Medical Supplies"),
        ("LLIN-NET", "Mosquito Net - LLIN", "Consumable"),
        ("FIRST-AID-KIT", "First Aid Kit", "Medical Supplies"),
        ("STATIONERY-PACK", "Office Stationery Pack", "Office Supplies"),
        ("LAPTOP-DELL", "Laptop - Dell Latitude", "IT Equipment"),
        ("GENERATOR-50KVA", "Generator - 50kVA", "Vehicles & Spares"),
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
        ("jane.procurement@ugavi.local", "Jane", "Wanjiku"),
        ("tom.logistics@ugavi.local", "Tom", "Odhiambo"),
        ("mary.audit@ugavi.local", "Mary", "Wambui"),
        ("peter.fleet@ugavi.local", "Peter", "Mwangi"),
    ]
    for email, first, last in users:
        if not frappe.db.exists("User", email):
            frappe.get_doc({
                "doctype": "User", "email": email, "first_name": first,
                "last_name": last, "send_welcome_email": 0, "enabled": 1,
def create_donor_profiles():
    """Create donor profiles for procurement tracking."""
    donors = [
        {"donor_name": "USAID Kenya", "donor_code": "USAID-KE",
         "currency": "KES", "require_segregated_stock": 1},
        {"donor_name": "The Global Fund", "donor_code": "GFATM",
         "currency": "KES", "require_segregated_stock": 1},
        {"donor_name": "DFID / FCDO", "donor_code": "FCDO",
         "currency": "KES", "require_segregated_stock": 1},
    ]
    for d in donors:
        if not frappe.db.exists("Donor Profile", {"donor_code": d["donor_code"]}):
            frappe.get_doc({"doctype": "Donor Profile", **d}).insert(ignore_permissions=True)
    print(f"  Created {len(donors)} donor profiles")


def setup_procurement_settings():
    """Seed Ugavi Procurement Settings with default thresholds."""
    if frappe.db.exists("Ugavi Procurement Settings", "Ugavi Procurement Settings"):
        print("  Procurement settings already exist")
        return
    settings = frappe.get_doc({
        "doctype": "Ugavi Procurement Settings",
        "direct_threshold": 200000,
        "restricted_threshold": 500000,
        "open_threshold": 500000,
        "enforce_donor_rules": 1,
        "require_waiver_for_override": 1,
        "sealed_bid_enabled": 1,
        "otp_expiry_minutes": 5,
        "max_otp_attempts": 3,
        "default_currency": "KES",
    })
    settings.insert(ignore_permissions=True)
    print("  Procurement settings seeded")
            }).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  Created {len(users)} demo users")