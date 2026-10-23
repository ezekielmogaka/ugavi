"""Schema-driven, idempotent demo seed for Ugavi.

Validates every field key against DocType meta at runtime.
Refuses to run on production sites (developer_mode=0).
Run twice -- no duplicates, no errors.

Usage:
    make seed                         # from Makefile
    bench execute ugavi.scripts.seed_demo.run
"""

import frappe
from frappe.utils import today, add_days
from frappe import _

_STRICT_FIELDS = True  # set False in tests to skip meta queries


def _check_production():
    """Refuse to run on production / non-developer sites."""
    site_conf = frappe.get_site_config()
    dev_mode = frappe.local.conf.get("developer_mode", site_conf.get("developer_mode", 0))
    if not dev_mode:
        frappe.throw(
            _("Seed data cannot run on production sites. "
              "Enable developer_mode in site_config.json."),
            title=_("Production Guard"),
        )


def _validate_doc(dt, data):
    """Check keys in data exist on DocType dt. Returns unrecognized keys."""
    if not _STRICT_FIELDS:
        return []
    try:
        meta = frappe.get_meta(dt)
    except Exception:
        return []
    valid = {f.fieldname for f in meta.fields} | {"doctype"}
    bad = [k for k in data if k not in valid and not k.startswith("__")]
    if bad:
        print(f"  W {dt}: unrecognized field(s) {bad}")
    return bad


def _ensure(dt, lk, lv, defaults, **extra):
    """Insert doc if not exists; return (created_bool, docname)."""
    if isinstance(lk, dict):
        exists = frappe.db.exists(dt, lk)
    else:
        exists = frappe.db.exists(dt, {lk: lv})
    if exists:
        return False, exists
    data = {"doctype": dt, **defaults, **extra}
    if isinstance(lk, str):
        data[lk] = lv
    _validate_doc(dt, data)
    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)
    return True, doc.name


def run():
    """Main entry point."""
    _check_production()
    _seed_foundation()
    _seed_roles_and_users()
    _seed_donors()
    _seed_suppliers()
    _seed_items_and_warehouses()
    _seed_procurement_settings()
    _seed_logistics()
    _seed_submitted_fleet_journeys()
    _seed_assets()
    _seed_governance()
    _seed_procurement_workflow()
    frappe.db.commit()
    print("\n=== Ugavi demo seed complete ===")
# ─────────────────────────────────────────────────
# 1. FOUNDATION
# ─────────────────────────────────────────────────

def _seed_foundation():
    if frappe.db.exists("Company", "Ugavi NGO"):
        print("  Company already exists")
        return
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
    setup_complete({
        "company_name": "Ugavi NGO", "company_abbr": "UG",
        "country": "Kenya", "currency": "KES",
        "timezone": "Africa/Nairobi",
        "chart_of_accounts": "Standard",
        "fy_start_date": "2024-01-01", "fy_end_date": "2024-12-31",
        "domains": ["Distribution"], "language": "English",
    })
    print("  Company + Chart of Accounts created")


# ─────────────────────────────────────────────────
# 2. ROLES & USERS
# ─────────────────────────────────────────────────

ROLES = [
    "Procurement Officer", "Approver Level 1", "Approver Level 2",
    "Bid Opening Officer", "Evaluation Committee", "Fleet Manager",
    "Asset Manager", "Logistics Officer", "Finance Officer",
    "Auditor", "Store Keeper",
]

DEMO_USERS = [
    ("procurement@ugavi.demo",  "Jimmy",  "Kamau",    "Procurement Officer"),
    ("approver1@ugavi.demo",    "Alice",  "Wanjiku",  "Approver Level 1"),
    ("approver2@ugavi.demo",    "Bob",    "Otieno",   "Approver Level 2"),
    ("opening1@ugavi.demo",     "Carol",  "Muthoni",  "Bid Opening Officer"),
    ("opening2@ugavi.demo",     "Dan",    "Omondi",   "Bid Opening Officer"),
    ("opening3@ugavi.demo",     "Emma",   "Chebet",   "Bid Opening Officer"),
    ("logistics@ugavi.demo",    "Frank",  "Kiprono",  "Logistics Officer"),
    ("fleet@ugavi.demo",        "Grace",  "Achieng",  "Fleet Manager"),
    ("assets@ugavi.demo",       "Henry",  "Maina",    "Asset Manager"),
    ("finance@ugavi.demo",      "Irene",  "Njeri",    "Finance Officer"),
    ("auditor@ugavi.demo",      "Jack",   "Mwangi",   "Auditor"),
    ("storekeeper@ugavi.demo",  "Kate",   "Akinyi",   "Store Keeper"),
    ("supplier1@ugavi.demo",    "MedSuppy", "Portal", None),
    ("supplier2@ugavi.demo",    "DiagAfri", "Portal", None),
    ("supplier3@ugavi.demo",    "TechSolKE", "Portal", None),
]


def _seed_roles_and_users():
    for role in ROLES:
        created, _ = _ensure("Role", "role_name", role, {})
        if created:
            print(f"  Role: {role}")
    for email, first, last, role in DEMO_USERS:
        if frappe.db.exists("User", email):
            continue
        user = frappe.get_doc({
            "doctype": "User", "email": email,
            "first_name": first, "last_name": last,
            "send_welcome_email": 0, "enabled": 1,
        })
        if role:
            user.append("roles", {"role": role})
        user.insert(ignore_permissions=True)
        print(f"  User: {email} ({role or 'portal'})")
    frappe.db.commit()
# ─────────────────────────────────────────────────
# 3. DONORS
# ─────────────────────────────────────────────────

DONORS = [
    ("USAID", "USAID", "usaid@demo.org"),
    ("Global Fund", "Global Fund", "globalfund@demo.org"),
    ("UNICEF", "UNICEF", "unicef@demo.org"),
    ("World Bank", "World Bank", "wb@demo.org"),
    ("DFID", "DFID", "dfid@demo.org"),
]


def _seed_donors():
    for code, name, email in DONORS:
        created, docname = _ensure(
            "Donor Profile", "donor_code", code,
            {"donor_name": name, "contact_email": email,
             "currency": "KES", "require_segregated_stock": 1, "enabled": 1},
        )
        if created:
            print(f"  Donor: {code}")
    frappe.db.commit()


# ─────────────────────────────────────────────────
# 4. SUPPLIERS (~30, varied prequal status)
# ─────────────────────────────────────────────────

SUPPLIER_GROUPS = ["Local", "International", "Services", "Raw Material"]


def _seed_suppliers():
    td = today()
    for g in SUPPLIER_GROUPS:
        _ensure("Supplier Group", "supplier_group_name", g, {})

    suppliers = [
        ("MedSupply Kenya Ltd", "Local", "Prequalified"),
        ("Diagnostics Africa Ltd", "Local", "Prequalified"),
        ("Tech Solutions Kenya", "Local", "Prequalified"),
        ("Office Equip East Africa", "Local", "Prequalified"),
        ("Nairobi Builders Ltd", "International", "Prequalified"),
        ("Safari Pharmaceuticals", "International", "Prequalified"),
        ("Highland Printers Ltd", "Services", "Prequalified"),
        ("Coast Engineering Works", "Local", "Prequalified"),
        ("Great Rift Transporters", "Local", "Prequalified"),
        ("Lake Basin IT Services", "Services", "Expired"),
        ("Mount Kenya Foods", "Local", "Expired"),
        ("Solar Solutions East Africa", "Local", "Suspended"),
        ("Green Energy Africa", "International", "Expired"),
        ("Aqua Pure Kenya", "Local", "Prequalified"),
        ("Secure Guard Services", "Services", "Prequalified"),
        ("Fast Track Couriers", "Services", "Prequalified"),
        ("Digital Print Hub", "Services", "Prequalified"),
        ("MediEquip Africa", "International", "Prequalified"),
        ("Civil Works Contractors Ltd", "International", "Expired"),
        ("Data Networks Ltd", "Services", "Prequalified"),
        ("Premier Consulting Group", "Services", "Prequalified"),
        ("Urban Architects Ltd", "International", "Prequalified"),
        ("Lab Supplies Kenya", "Local", "Prequalified"),
        ("Farm Fresh Produce", "Local", "Suspended"),
        ("Safety First Equipment Ltd", "Local", "Prequalified"),
        ("Clean Energy Solutions", "International", "Prequalified"),
        ("Top Notch Catering", "Services", "Expired"),
        ("Auto Parts Express", "Local", "Prequalified"),
        ("Water-Tech Engineering", "International", "Prequalified"),
        ("Edu Supplies Ltd", "Services", "Prequalified"),
    ]

    for name, group, pq_status in suppliers:
        created, _ = _ensure(
            "Supplier", "supplier_name", name,
            {"supplier_group": group, "supplier_type": "Company", "country": "Kenya"},
        )
        if pq_status == "Prequalified":
            if not frappe.db.exists("Supplier Prequalification", {"supplier": name}):
                frappe.get_doc({
                    "doctype": "Supplier Prequalification", "supplier": name,
                    "category": "Medical Supplies", "status": "Prequalified",
                    "expiry_date": add_days(td, 730),
                    "prequalification_date": add_days(td, -180),
                }).insert(ignore_permissions=True)
        elif pq_status == "Expired":
            if not frappe.db.exists("Supplier Prequalification", {"supplier": name}):
                frappe.get_doc({
                    "doctype": "Supplier Prequalification", "supplier": name,
                    "category": "Services", "status": "Expired",
                    "expiry_date": add_days(td, -30),
                    "prequalification_date": add_days(td, -395),
                }).insert(ignore_permissions=True)
        elif pq_status == "Suspended":
            if not frappe.db.exists("Supplier Prequalification", {"supplier": name}):
                frappe.get_doc({
                    "doctype": "Supplier Prequalification", "supplier": name,
                    "category": "Consumable", "status": "Suspended",
                    "suspension_reason": "Non-performance", "suspension_date": td,
                    "expiry_date": add_days(td, 365),
                }).insert(ignore_permissions=True)
        if created:
            print(f"  Supplier: {name}")
    frappe.db.commit()
    print("  30 suppliers verified")
# ─────────────────────────────────────────────────
# 5. ITEMS & WAREHOUSES
# ─────────────────────────────────────────────────

def _seed_items_and_warehouses():
    for g in ["Medical Supplies", "Pharmaceuticals", "Consumable",
              "IT Equipment", "Office Supplies", "Vehicles & Spares",
              "Drugs", "Products"]:
        _ensure("Item Group", "item_group_name", g, {})

    for code, name, grp, uom in [
        ("ANTIMALARIAL-ALU", "Antimalarial Tablets (ALU)", "Pharmaceuticals", "Nos"),
        ("HIV-RAPID-TEST", "HIV Rapid Test Kit", "Medical Supplies", "Nos"),
        ("LLIN-NET", "Mosquito Net - LLIN", "Consumable", "Nos"),
        ("FIRST-AID-KIT", "First Aid Kit", "Medical Supplies", "Nos"),
        ("STATIONERY-PACK", "Office Stationery Pack", "Office Supplies", "Nos"),
        ("LAPTOP-DELL", "Laptop - Dell Latitude", "IT Equipment", "Nos"),
        ("GENERATOR-50KVA", "Generator - 50kVA", "Vehicles & Spares", "Nos"),
        ("FUEL-DIESEL", "Fuel - Diesel", "Consumable", "Litres"),
        ("VEHICLE-SPARE-OIL", "Engine Oil 5W-30", "Vehicles & Spares", "Nos"),
        ("SYRINGE-5ML", "Syringe 5ml", "Medical Supplies", "Nos"),
        ("GLOVES-EXAM", "Examination Gloves Box", "Medical Supplies", "Nos"),
        ("MATERNITY-KIT", "Maternity Delivery Kit", "Medical Supplies", "Nos"),
        ("ORS-SACHET", "Oral Rehydration Salts Sachet", "Pharmaceuticals", "Nos"),
        ("COLD-BOX", "Vaccine Cold Box", "Consumable", "Nos"),
    ]:
        created, _ = _ensure(
            "Item", "item_code", code,
            {"item_name": name, "item_group": grp, "stock_uom": uom,
             "valuation_rate": 0, "is_stock_item": 1},
        )
        if created:
            print(f"  Item: {code}")

    company = frappe.defaults.get_defaults().get("company") or "Ugavi NGO"
    for wh_name in [
        "USAID Main Store - Nairobi", "USAID Field Store - Kisumu",
        "Global Fund Warehouse - Mombasa", "GF Store - Eldoret",
        "Main Transit Warehouse - Nairobi", "Cold Chain Storage - Nairobi",
    ]:
        _ensure("Warehouse", "warehouse_name", wh_name,
                {"warehouse_type": "Transit", "company": company},
                name=wh_name)
    frappe.db.commit()
    print("  14 items, 6 warehouses created")


# ─────────────────────────────────────────────────
# 6. PROCUREMENT SETTINGS
# ─────────────────────────────────────────────────

def _seed_procurement_settings():
    if frappe.db.exists("Ugavi Procurement Settings", "Ugavi Procurement Settings"):
        print("  Procurement settings already exist")
        return
    frappe.get_doc({
        "doctype": "Ugavi Procurement Settings",
        "direct_threshold": 200000, "restricted_threshold": 500000,
        "open_threshold": 500000, "enforce_donor_rules": 1,
        "require_waiver_for_override": 1, "sealed_bid_enabled": 1,
        "otp_expiry_minutes": 5, "max_otp_attempts": 3,
        "default_currency": "KES",
    }).insert(ignore_permissions=True)
    print("  Procurement settings seeded")
# ─────────────────────────────────────────────────
# 7. FLEET (5 vehicles, allocations, fuel, trips)
# ─────────────────────────────────────────────────

def _seed_fleet():
    td = today()
    dm = {d[0]: frappe.db.get_value("Donor Profile", {"donor_code": d[0]}, "name") for d in DONORS}

    vehicles = [
        ("KAZ-001K", "Toyota", "Land Cruiser Prado", 2022, "KAZ 001K", 5500000, "USAID"),
        ("KBH-234L", "Toyota", "Hilux Double Cab", 2023, "KBH 234L", 3800000, "Global Fund"),
        ("KCA-567M", "Nissan", "Patrol", 2021, "KCA 567M", 4200000, "UNICEF"),
        ("KDA-890N", "Isuzu", "D-Max", 2024, "KDA 890N", 3100000, "World Bank"),
        ("KEA-112P", "Toyota", "Land Cruiser 76", 2023, "KEA 112P", 4800000, "DFID"),
    ]
    for vname, make, model, year, plate, price, dcode in vehicles:
        created, _ = _ensure(
            "Vehicle", "license_plate", vname,
            {"license_plate": vname, "make": make, "model": model,
             "company": frappe.defaults.get_user_default("company") or "Ugavi NGO",
             "fuel_type": "Diesel", "uom": "Litre",
             "acquisition_date": str(add_days(td, -365 * (2026 - year))),
             "vehicle_value": price, "ugavi_donor": dm.get(dcode, dcode),
             "last_odometer": (2026 - year) * 15000, "ugavi_status": "Active"},
        )
        if created:
            print(f"  Vehicle: {vname} [{dcode}]")

    for vehicle, user, start, end, status in [
        ("KAZ-001K", "procurement@ugavi.demo", str(add_days(td, -180)),
         str(add_days(td, 180)), "Active"),
        ("KBH-234L", "logistics@ugavi.demo", str(add_days(td, -90)),
         str(add_days(td, 90)), "Active"),
        ("KCA-567M", "fleet@ugavi.demo", str(add_days(td, -120)),
         str(add_days(td, 60)), "Active"),
        ("KDA-890N", "assets@ugavi.demo", str(add_days(td, -60)),
         str(add_days(td, 120)), "Returned"),
    ]:
        aname = f"{vehicle}-{start}"
        if not frappe.db.exists("Vehicle Allocation", aname):
            frappe.get_doc({
                "doctype": "Vehicle Allocation", "vehicle": vehicle,
                "allocated_to": user, "start_date": start, "end_date": end,
                "status": status,
                "actual_return_date": str(td) if status == "Returned" else None,
            }).insert(ignore_permissions=True)
            print(f"  Allocation: {vehicle} -> {user}")

    for vehicle, fdate, litres, cp, odo, dcode in [
        ("KAZ-001K", str(add_days(td, -60)), 45, 210, 52500, "USAID"),
        ("KAZ-001K", str(add_days(td, -45)), 50, 210, 56000, "USAID"),
        ("KBH-234L", str(add_days(td, -50)), 40, 210, 52500, "Global Fund"),
        ("KCA-567M", str(add_days(td, -30)), 55, 210, 56000, "UNICEF"),
        ("KDA-890N", str(add_days(td, -20)), 35, 210, 52500, "World Bank"),
        ("KAZ-001K", str(add_days(td, -10)), 48, 215, 56000, "USAID"),
    ]:
        fname = f"FL-{vehicle}-{fdate}"
        if not frappe.db.exists("Fuel Log", fname):
            frappe.get_doc({
                "doctype": "Fuel Log", "vehicle": vehicle, "date": fdate,
                "fuel_type": "Diesel", "litres": litres,
                "cost_per_litre": cp, "total_cost": round(litres * cp, 2),
                "odometer": odo, "station": "Shell - Westlands",
                "donor": dm.get(dcode, dcode),
            }).insert(ignore_permissions=True)
            print(f"  Fuel: {vehicle} {fdate}")

    for vehicle, start, end, so, eo, purpose, dcode in [
        ("KAZ-001K", str(add_days(td, -55)), str(add_days(td, -55)),
         1200, 1350, "Field visit Kisumu", "USAID"),
        ("KBH-234L", str(add_days(td, -40)), str(add_days(td, -40)),
         800, 920, "Delivery Mombasa", "Global Fund"),
        ("KCA-567M", str(add_days(td, -25)), str(add_days(td, -25)),
         500, 680, "Supplies pickup", "UNICEF"),
    ]:
        tname = f"TRIP-{vehicle}-{start}"
        if not frappe.db.exists("Trip Log", tname):
            frappe.get_doc({
                "doctype": "Trip Log", "vehicle": vehicle,
                "start_date": start, "end_date": end,
                "start_odometer": so, "end_odometer": eo,
                "distance": eo - so, "purpose": purpose,
                "donor": dm.get(dcode, dcode), "status": "Completed",
            }).insert(ignore_permissions=True)
            print(f"  Trip: {vehicle} {purpose}")
    frappe.db.commit()
    print("  Fleet: 5 vehicles, 4 allocations, 6 fuel logs, 3 trips")


def _seed_submitted_fleet_journeys():
    """Seed procurement-backed fleet evidence instead of draft-only fixtures."""
    from ugavi.scripts.seed_fleet_journey import seed_fleet_journey

    company = frappe.defaults.get_defaults().get("company") or "Ugavi NGO"
    seed_fleet_journey(
        company=company,
        fleet_user="fleet@ugavi.demo",
        supplier="Auto Parts Express",
        scenarios=[
            {
                "donor_code": "USAID",
                "warehouse_name": "USAID Main Store - Nairobi",
                "license_plate": "KUG 410A",
                "make": "Toyota",
                "model": "Land Cruiser 76",
                "marker": "UGAVI-DEMO-FLEET-USAID",
            },
            {
                "donor_code": "Global Fund",
                "warehouse_name": "Global Fund Warehouse - Mombasa",
                "license_plate": "KUG 271G",
                "make": "Toyota",
                "model": "Hilux Double Cab",
                "marker": "UGAVI-DEMO-FLEET-GF",
            },
        ],
    )
    print("  Fleet: submitted donor purchase, fuel, spare, trip and report journeys")
# ─────────────────────────────────────────────────
# 8. ASSETS (5 assets, 2 movements, 1 disposal)
# ─────────────────────────────────────────────────

def _seed_assets():
    td = today()
    dm = {d[0]: frappe.db.get_value("Donor Profile", {"donor_code": d[0]}, "name") for d in DONORS}

    assets = [
        ("AST-LAPTOP-001", "IT Equipment", 120000, "USAID",
         "assets@ugavi.demo", "USAID Main Store - Nairobi"),
        ("AST-GEN-001", "Vehicles & Spares", 850000, "Global Fund",
         "logistics@ugavi.demo", "GF Store - Eldoret"),
        ("AST-COLDCHAIN-001", "Consumable", 320000, "UNICEF",
         "storekeeper@ugavi.demo", "Cold Chain Storage - Nairobi"),
        ("AST-FURN-001", "Office Supplies", 45000, "World Bank",
         "finance@ugavi.demo", "Main Transit Warehouse - Nairobi"),
        ("AST-VEHICLE-TOOL-001", "Vehicles & Spares", 18000, "DFID",
         "fleet@ugavi.demo", "USAID Field Store - Kisumu"),
    ]
    for aname, cat, price, dcode, custodian, loc in assets:
        created, _ = _ensure(
            "Asset Register", "asset_name", aname,
            {"asset_category": cat, "purchase_date": str(add_days(td, -180)),
             "purchase_price": price, "current_value": price,
             "donor": dm.get(dcode, dcode), "custodian": custodian,
             "location": loc, "condition": "Good", "status": "Active"},
        )
        if created:
            print(f"  Asset: {aname} [{cat}] donor={dcode}")

    for asset, fm, to, mv_date in [
        ("AST-LAPTOP-001", "USAID Main Store - Nairobi", "USAID Field Store - Kisumu",
         str(add_days(td, -30))),
        ("AST-GEN-001", "GF Store - Eldoret", "Main Transit Warehouse - Nairobi",
         str(add_days(td, -15))),
    ]:
        mvname = f"MV-{asset}-{mv_date}"
        if not frappe.db.exists("Ugavi Asset Movement", mvname):
            frappe.get_doc({
                "doctype": "Ugavi Asset Movement", "from_location": fm,
                "to_location": to, "status": "Confirmed",
            }).insert(ignore_permissions=True)
            print(f"  AssetMove: {asset} {fm} -> {to}")

    if not frappe.db.exists("Asset Disposal", "DISP-AST-FURN-001"):
        frappe.get_doc({
            "doctype": "Asset Disposal",
            "disposal_value": 5000, "status": "Approved",
        }).insert(ignore_permissions=True)
        print("  AssetDisposal: AST-FURN-001")
    frappe.db.commit()
    print("  Assets: 5 assets, 2 movements, 1 disposal")
# ─────────────────────────────────────────────────
# 9. GOVERNANCE (DoA, Waiver, SoD, Audit)
# ─────────────────────────────────────────────────

def _seed_governance():
    td = today()

    for dept, donor_code, min_amt, max_amt, level, role in [
        ("All Departments", None, 0, 200000, 1, "Approver Level 1"),
        ("All Departments", None, 200001, 500000, 1, "Approver Level 1"),
        ("All Departments", None, 500001, 2000000, 2, "Approver Level 2"),
        ("All Departments", "USAID", 0, 100000, 1, "Approver Level 1"),
        ("All Departments", "World Bank", 0, 5000000, 1, "Approver Level 1"),
    ]:
        doa_name = f"DoA-{dept}-{donor_code or 'X'}-{min_amt}"
        if not frappe.db.exists("Delegation of Authority", doa_name):
            dname = None
            if donor_code:
                dname = frappe.db.get_value("Donor Profile", {"donor_code": donor_code}, "name")
            frappe.get_doc({
                "doctype": "Delegation of Authority", "department": dept,
                "donor": dname, "min_amount": min_amt, "max_amount": max_amt,
                "approval_level": level, "approver_role": role, "enabled": 1,
                "effective_from": str(add_days(td, -365)),
            }).insert(ignore_permissions=True)
            print(f"  DoA: {dept} {donor_code or 'ALL'} [{min_amt}-{max_amt}] L{level}")

    if not frappe.db.exists("Waiver", "WV-EMERGENCY-001"):
        frappe.get_doc({
            "doctype": "Waiver",
            "requested_by": "procurement@ugavi.demo",
            "reason": "Emergency procurement - flood response supplies needed urgently.",
            "rule_to_override": "THRESHOLD_200K",
            "status": "Approved",
            "approved_by": "approver1@ugavi.demo",
            "approval_date": str(add_days(td, -10)),
            "approval_remarks": "Approved - genuine emergency. Flood response priority.",
        }).insert(ignore_permissions=True)
        print("  Waiver: Emergency procurement approved")

    for r1, r2, ctype, enf, desc in [
        ("Procurement Officer", "Approver Level 1", "Create + Approve Same Doc",
         "Block", "Requester cannot approve own PRs"),
        ("Procurement Officer", "Bid Opening Officer", "Approver + Auditor",
         "Block", "PO cannot open bids"),
        ("Bid Opening Officer", "Evaluation Committee", "Create + Approve Same Doc",
         "Warning Only", "Bid opener should not evaluate"),
    ]:
        sod_name = f"{r1}-{r2}-{ctype}"
        if not frappe.db.exists("Segregation of Duties", sod_name):
            frappe.get_doc({
                "doctype": "Segregation of Duties", "role_1": r1,
                "role_2": r2, "conflict_type": ctype,
                "enforcement": enf, "description": desc,
            }).insert(ignore_permissions=True)
            print(f"  SoD: {r1} x {r2}")

    if not frappe.db.exists("Audit Log", "AUDIT-001"):
        frappe.get_doc({
            "doctype": "Audit Log",
            "user": "auditor@ugavi.demo",
            "timestamp": str(add_days(td, -5)),
            "action": "Procurement method override attempt blocked",
            "outcome": "Failed",
            "ip_address": "192.168.1.100",
            "record_hash": "sha256:dummy_hash",
        }).insert(ignore_permissions=True)
        print("  Audit: SoD violation blocked")
    frappe.db.commit()
    print("  Governance: 5 DoA, 1 waiver, 3 SoD, 1 audit")
# ─────────────────────────────────────────────────
# 10. PROCUREMENT WORKFLOW (PRs + Tenders)
# ─────────────────────────────────────────────────

def _seed_procurement_workflow():
    td = today()
    dm = {d[0]: frappe.db.get_value("Donor Profile", {"donor_code": d[0]}, "name") for d in DONORS}

    pr_data = [
        ("Medical supplies - Q2 restock", "USAID", 180000,
         "Request for Quotation (Direct)", "Approved"),
        ("IT equipment procurement", "Global Fund", 350000,
         "Restricted Tender", "Approved"),
        ("Vehicle maintenance supplies", "UNICEF", 499000,
         "Restricted Tender", "Approved"),
        ("Lab equipment - Lab upgrade", "World Bank", 499500,
         "Restricted Tender", "Approved"),
        ("Warehouse construction materials", "DFID", 800000,
         "Open Tender", "Approved"),
        ("Office furniture - small order", "USAID", 150000,
         "Request for Quotation (Direct)", "Rejected"),
    ]

    pr_map = {}
    for title, donor_code, value, method, status in pr_data:
        pk = title[:50].replace(" ", "-").replace(",", "")
        if frappe.db.exists("Purchase Requisition", {"title": title}):
            pr_map[pk] = frappe.db.get_value("Purchase Requisition", {"title": title}, "name")
            continue
        pr = frappe.get_doc({
            "doctype": "Purchase Requisition", "title": title,
            "requester": "procurement@ugavi.demo",
            "department": "All Departments",
            "donor": dm.get(donor_code, donor_code),
            "justification": f"Required for {donor_code} project activities",
            "status": status, "procurement_method": method,
            "estimated_value": value,
            "items": [{
                "item_code": "HIV-RAPID-TEST", "quantity": 500,
                "estimated_unit_price": value / 500, "uom": "Nos",
                "estimated_total": value,
            }],
        })
        pr.insert(ignore_permissions=True)
        pr_map[pk] = pr.name
        print(f"  PR: {title[:40]} [{donor_code}] {value:,} KES [{status}]")

    _seed_tenders_and_bids(td, dm, pr_map)
    frappe.db.commit()
    print("  Procurement: 6 PRs, 6 tenders, 3 bids, 1 contract, 2 scorecards, 2 bid securities, 1 addendum")
def _seed_tenders_and_bids(td, dm, pr_map):
    """Tenders at 150K/350K/499K/499.5K/500K/800K + 3 bids + contract + scorecards."""

    tender_data = [
        ("Medical supplies restock Q2", "USAID", 150000,
         "Request for Quotation (Direct)", "Medical-supplies---Q2-restock"),
        ("IT equipment procurement", "Global Fund", 350000,
         "Restricted Tender", "IT-equipment-procurement"),
        ("Vehicle maintenance spares", "UNICEF", 499000,
         "Restricted Tender", "Vehicle-maintenance-supplies"),
        ("Lab equipment upgrade", "World Bank", 499500,
         "Restricted Tender", "Lab-equipment---Lab-upgrade"),
        ("Construction materials WH", "DFID", 500000,
         "Open Tender", "Warehouse-construction-materials"),
        ("Office furniture small", "USAID", 800000,
         "Open Tender", "Office-furniture---small-order"),
    ]

    tender_map = {}
    for ttitle, donor_code, value, method, pk in tender_data:
        tn = f"TND-{ttitle[:30].replace(' ','-')}"
        if frappe.db.exists("Tender", {"title": ttitle}):
            tender_map[tn] = frappe.db.get_value("Tender", {"title": ttitle}, "name")
            continue
        t = frappe.get_doc({
            "doctype": "Tender", "title": ttitle,
            "donor": dm.get(donor_code, donor_code),
            "procurement_method": method, "estimated_value": value,
            "purchase_requisition": pr_map.get(pk),
            "submission_deadline": str(add_days(td, 14 if "Direct" in method else 21)),
            "publish_date": str(td), "status": "Published",
            "opening_officer_1": "opening1@ugavi.demo",
            "opening_officer_2": "opening2@ugavi.demo",
            "opening_officer_3": "opening3@ugavi.demo",
        })
        t.insert(ignore_permissions=True)
        tender_map[tn] = t.name
        print(f"  Tender: {ttitle[:40]} [{donor_code}] {value:,} KES")

    dd_tender = next((tender_map[k] for k in tender_map if "Construction" in k), None)
    if dd_tender:
        for supplier, amount, delivery in [
            ("Nairobi Builders Ltd", 780000, 60),
            ("MedSupply Kenya Ltd", 795000, 45),
            ("Civil Works Contractors Ltd", 810000, 30),
        ]:
            bn = f"BID-{supplier}-{dd_tender}"
            if not frappe.db.exists("Bid", bn):
                frappe.get_doc({
                    "doctype": "Bid", "tender": dd_tender,
                    "supplier": supplier, "status": "Submitted",
                    "bidder_name": supplier, "bid_amount": amount,
                    "delivery_days": delivery,
                }).insert(ignore_permissions=True)
                print(f"  Bid: {supplier} [{amount:,} KES, {delivery}d]")

        if not frappe.db.exists("Bid Opening Record", f"BOR-{dd_tender}"):
            frappe.get_doc({
                "doctype": "Bid Opening Record", "tender": dd_tender,
                "opening_date": str(add_days(td, 15)),
                "officer_1": "opening1@ugavi.demo",
                "officer_2": "opening2@ugavi.demo",
                "officer_3": "opening3@ugavi.demo",
                "outcome": "Success",
                "otp_log_1": "OTP sent to opening1@ugavi.demo [sms stub]",
                "otp_log_2": "OTP sent to opening2@ugavi.demo [sms stub]",
                "otp_log_3": "OTP sent to opening3@ugavi.demo [sms stub]",
                "ip_address_1": "192.168.1.10", "ip_address_2": "192.168.1.11",
                "ip_address_3": "192.168.1.12",
            }).insert(ignore_permissions=True)
            print("  BidOpening: 3-officer sealed bid")

    if dd_tender:
        if not frappe.db.exists("Ugavi Contract", "CONT-Warehouse-Construction"):
            frappe.get_doc({
                "doctype": "Ugavi Contract",
                "supplier": "Nairobi Builders Ltd", "tender": dd_tender,
                "start_date": str(add_days(td, 30)),
                "end_date": str(add_days(td, 180)),
                "contract_value": 800000, "donor": dm.get("DFID"),
                "retention_percentage": 10, "performance_bond_required": 1,
                "bond_amount": 40000, "status": "Active",
                "milestones": [
                    {"milestone_name": "Site preparation",
                     "due_date": str(add_days(td, 30)), "amount": 200000},
                    {"milestone_name": "Foundation & walls",
                     "due_date": str(add_days(td, 90)), "amount": 400000,
                     "completed": 1, "completed_date": str(add_days(td, 85))},
                    {"milestone_name": "Roofing & finishing",
                     "due_date": str(add_days(td, 180)), "amount": 200000},
                ],
                "expiry_alert_days": 30,
            }).insert(ignore_permissions=True)
            print("  Contract: CONT-Warehouse-Construction")

    # --- Bid Security Records ---
    _seed_bid_securities(td, dd_tender)

    # --- Addendum ---
    _seed_addenda(td, dd_tender)

    for supplier, edate, q, d, c, p, remarks in [
        ("MedSupply Kenya Ltd", str(add_days(td, -60)), 9, 8, 10, 8,
         "Excellent quality, on-time delivery"),
        ("Diagnostics Africa Ltd", str(add_days(td, -60)), 8, 7, 9, 9,
         "Good quality, slight delay"),
    ]:
        sn = f"SC-{supplier}-{edate}"
        if not frappe.db.exists("Ugavi Supplier Evaluation", sn):
            frappe.get_doc({
                "doctype": "Ugavi Supplier Evaluation", "supplier": supplier,
                "evaluation_date": edate, "quality_score": q,
                "delivery_score": d, "compliance_score": c,
                "price_competitiveness": p,
                "total_score": q + d + c + p,
                "cumulative_rating": (q + d + c + p) / 40 * 100,
                "remarks": remarks,
            }).insert(ignore_permissions=True)
            print(f"  Scorecard: {supplier}")

# ─────────────────────────────────────────────────
# 10a. Bid Securities + Addenda helpers
# ─────────────────────────────────────────────────

def _seed_bid_securities(td, dd_tender):
    """Seed bid security records for the construction tender bids."""
    securities = [
        ("Nairobi Builders Ltd", "Bid Bond", 80000, "2026-06-15", "NBO-2026-BS-001", "Kenya Commercial Bank"),
        ("MedSupply Kenya Ltd", "Bank Guarantee", 80000, "2026-07-01", "MS-2026-BG-042", "Equity Bank"),
    ]
    for supplier, sec_type, amount, valid_until, ref, bank in securities:
        bs_name = f"BS-{supplier[:20]}-{dd_tender}"
        if not frappe.db.exists("Bid Security", bs_name):
            frappe.get_doc({
                "doctype": "Bid Security",
                "tender": dd_tender,
                "supplier": supplier,
                "security_type": sec_type,
                "security_amount": amount,
                "received_date": str(add_days(td, 3)),
                "valid_until": valid_until,
                "reference_number": ref,
                "issuing_bank": bank,
                "status": "Held",
            }).insert(ignore_permissions=True)
            print(f"  BidSecurity: {supplier} [{sec_type}: {amount:,} KES]")


def _seed_addenda(td, dd_tender):
    """Seed an addendum to the construction tender."""
    if not frappe.db.exists("Tender", {"title": "Construction materials WH"}):
        return
    tender_name = frappe.db.get_value("Tender", {"title": "Construction materials WH"}, "name")
    tender = frappe.get_doc("Tender", tender_name)
    if not tender.addenda or len(tender.addenda) == 0:
        tender.issue_addendum(
            title="Specification update - structural steel grade",
            description="Changed structural steel grade from S275 to S355 per structural engineer's recommendation. All bidders must price per revised specs.",
            extends_deadline=True,
            new_deadline=str(add_days(td, 28)),
        )
        print("  Addendum: Specification update issued, deadline extended +7d")


# ─────────────────────────────────────────────────
# 11. LOGISTICS (Donor Warehouses, Stock Reports, Transfers)
# ─────────────────────────────────────────────────

def _seed_logistics():
    td = today()
    dm = {d[0]: frappe.db.get_value("Donor Profile", {"donor_code": d[0]}, "name") for d in DONORS}

    for dcode, wh in [
        ("USAID", "USAID Main Store - Nairobi"),
        ("USAID", "USAID Field Store - Kisumu"),
        ("Global Fund", "Global Fund Warehouse - Mombasa"),
        ("Global Fund", "GF Store - Eldoret"),
        ("UNICEF", "Cold Chain Storage - Nairobi"),
        ("World Bank", "Main Transit Warehouse - Nairobi"),
    ]:
        dwname = f"{dcode}-{wh}"
        if not frappe.db.exists("Donor Warehouse", dwname):
            frappe.get_doc({
                "doctype": "Donor Warehouse", "warehouse": wh,
                "donor": dm.get(dcode, dcode), "restricted_items": 0,
            }).insert(ignore_permissions=True)
            print(f"  DonorWH: {dcode} <-> {wh}")

    for dcode in ["USAID", "Global Fund"]:
        for mo in [60, 30]:
            msr_name = f"MSR-{dcode}-{add_days(td, -mo)}"
            if not frappe.db.exists("Monthly Stock Report", msr_name):
                dname = dm.get(dcode, dcode)
                msr = frappe.get_doc({
                    "doctype": "Monthly Stock Report",
                    "donor": dname,
                    "month": str(add_days(td, -mo)),
                    "total_value": 250000 if dcode == "USAID" else 180000,
                })
                msr.append("stock_items", {
                    "item_code": "HIV-RAPID-TEST", "opening_qty": 1000,
                    "closing_qty": 850, "total_value": 42500, "donor": dname,
                })
                msr.append("stock_items", {
                    "item_code": "LLIN-NET", "opening_qty": 500,
                    "closing_qty": 450, "total_value": 22500, "donor": dname,
                })
                msr.insert(ignore_permissions=True)
                print(f"  StockReport: {dcode} [{add_days(td, -mo)}]")

    if not frappe.db.exists("Inter Donor Transfer", "IDT-USAID-UNICEF-001"):
        idt = frappe.get_doc({
            "doctype": "Inter Donor Transfer",
            "from_warehouse": "USAID Main Store - Nairobi",
            "to_warehouse": "Cold Chain Storage - Nairobi",
            "from_donor": dm.get("USAID"),
            "to_donor": dm.get("UNICEF"),
            "status": "Approved",
            "transfer_date": str(add_days(td, -20)),
            "reason": "Reallocation for emergency UNICEF response in flood areas",
            "approved_by": "approver1@ugavi.demo",
        })
        idt.append("items", {"item_code": "HIV-RAPID-TEST", "qty": 200, "uom": "Nos"})
        idt.append("items", {"item_code": "FIRST-AID-KIT", "qty": 50, "uom": "Nos"})
        idt.insert(ignore_permissions=True)
        print("  InterDonorTransfer: USAID -> UNICEF | 250 items approved")

    frappe.db.commit()
    print("  Logistics: 6 donor-warehouse links, 4 stock reports, 1 transfer")
# test2\n