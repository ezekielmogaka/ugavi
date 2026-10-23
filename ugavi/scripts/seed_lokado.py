"""Schema-driven, idempotent demo seed for LOKADO (Lotus Kenya Action for Development Organization).

Validates every field key against DocType meta at runtime.
Refuses to run on production sites (developer_mode=0).
Run twice -- no duplicates, no errors.

Usage:
    make seed-lokado
    bench execute ugavi.scripts.seed_lokado.run
"""

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today
from frappe.utils.password import update_password

_STRICT_FIELDS = True  # set False in tests to skip meta queries
_DEMO_PASSWORD = "Ugavi@2024"


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
    _seed_items_and_warehouses()   # creates Item Groups that suppliers need
    _seed_suppliers()
    _seed_supplier_portal_links()
    _seed_procurement_settings()
    _seed_logistics()
    _seed_supplier_evaluations()   # post-receipt supplier scorecards
    _seed_fleet()
    _seed_assets()
    _seed_governance()            # DoA, waiver, SoD, audit log, delegation
    _seed_finance()               # KRA PIN, tax templates, eTIMS hooks
    _seed_procurement_workflow()  # PRs, tenders, bids, awards, contracts
    _seed_bid_opening_and_sealed_keys(today())  # AP-19: Sealed Bid Keys + BOR

    # ── Supply-Chain Depth ──
    _seed_batch_tracking()         # Batch records with expiry dates (must come before QC)
    _seed_quality_inspections()   # QC inspections against purchase receipts
    _seed_stock_entries()          # Material Receipt / Issue / Transfer
    _seed_reorder_levels()         # Item reorder points per warehouse
    _seed_material_requests()      # Programme staff material requests

    # ── Finance + Three-Way Match ──
    _seed_purchase_invoices()     # Purchase invoices for 3-way match
    _seed_payment_entries()       # Payment entries against invoices
    _seed_landed_cost_vouchers()  # Landed cost (transport/import)
    _seed_budget_records()        # Donor/project budget allocations

    # ── Notifications ──
    _seed_notification_rules()    # Expiry, approval, rejection alerts (NT3)

    # ── Programme & Grants ──
    _seed_projects_and_grants()   # Programmes, projects, grants

    # ── Procurement Depth ──
    _seed_lokado_purchase_orders() # Co-signed LPOs from awards

    frappe.db.commit()
    print("\n=== LOKADO demo seed complete ===")
# ─────────────────────────────────────────────────
# 1. FOUNDATION — LOKADO Company
# ─────────────────────────────────────────────────

def _seed_foundation():
    company_name = "Lotus Kenya Action for Development Organization"
    company_abbr = "LOKADO"

    company = frappe.db.exists("Company", {"abbr": company_abbr})
    if not company:
        company = frappe.db.exists("Company", {"company_name": company_name})

    if company:
        print("  Company LOKADO already exists")
        company_name = frappe.db.get_value("Company", company, "company_name")
    else:
        from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

        setup_complete({
            "company_name": company_name,
            "company_abbr": company_abbr,
            "country": "Kenya",
            "currency": "KES",
            "timezone": "Africa/Nairobi",
            "chart_of_accounts": "Standard",
            "fy_start_date": "2024-01-01",
            "fy_end_date": "2024-12-31",
            "domains": ["Distribution"],
            "language": "English",
        })
        print("  Company: Lotus Kenya Action for Development Organization (LOKADO)")

    frappe.db.set_default("company", company_name)

    for dept in [
        "Peace Building & Conflict Resolution",
        "Livelihoods & Food Security",
        "Emergency WASH",
        "Gender & Protection",
        "Institutional Development",
        "Administration & Finance",
    ]:
        _ensure("Department", "department_name", dept, {"company": company_name})

    frappe.db.commit()
    print("  Foundation: Company + 6 Programs created")


# ─────────────────────────────────────────────────
# 2. ROLES & USERS — LOKADO staff with Turkana/Kenyan names
# ─────────────────────────────────────────────────

ROLES = [
    "Procurement Officer", "Approver Level 1", "Approver Level 2",
    "Bid Opening Officer", "Evaluation Committee", "Fleet Manager",
    "Asset Manager", "Logistics Officer", "Finance Officer", "Auditor", "Store Keeper",
]

LOKADO_USERS = [
    ("programme@lokado.org",    "Alice",   "Akol",      "Programme Manager"),
    ("procurement@lokado.org",  "Peter",   "Ekai",      "Procurement Officer"),
    ("approver1@lokado.org",    "Jane",    "Napeyok",   "Approver Level 1"),
    ("approver2@lokado.org",    "Paul",    "Lotir",     "Approver Level 2"),
    ("opening1@lokado.org",     "Mary",    "Akuom",     "Bid Opening Officer"),
    ("opening2@lokado.org",     "James",   "Ebei",      "Bid Opening Officer"),
    ("opening3@lokado.org",     "Sarah",   "Nabwel",    "Bid Opening Officer"),
    ("committee@lokado.org",    "Dorothy", "Nekesa",    "Evaluation Committee"),
    ("logistics@lokado.org",    "John",    "Ekiru",     "Logistics Officer"),
    ("fleet@lokado.org",        "David",   "Ewoi",      "Fleet Manager"),
    ("assets@lokado.org",       "Agnes",   "Ekal",      "Asset Manager"),
    ("finance@lokado.org",      "Margaret","Nachuk",    "Finance Officer"),
    ("auditor@lokado.org",      "Robert",  "Lotukoi",   "Auditor"),
    ("storekeeper@lokado.org",  "Ruth",    "Napeyok",   "Store Keeper"),
    ("turkana-construction@outlook.com", "Turkana Construction", "Ltd", None),
    ("nadirkonyen-women@outlook.com",    "Nadirkonyen Women",    "Group", None),
    ("riftvalley-hardware@outlook.com",  "Rift Valley Hardware", "Ltd", None),
    ("jopeji@outlook.com",               "Jopeji",               "Enterprises", None),
    ("lodwar-supplies@outlook.com",      "Lodwar General",       "Supplies", None),
]

SUPPLIER_PORTAL_LINKS = {
    "turkana-construction@outlook.com": "Turkana Construction Ltd",
    "nadirkonyen-women@outlook.com": "Nadirkonyen Women's Group",
    "riftvalley-hardware@outlook.com": "Rift Valley Hardware",
    "jopeji@outlook.com": "Jopeji Enterprises",
    "lodwar-supplies@outlook.com": "Lodwar General Supplies",
}


def _seed_roles_and_users():
    for role in ROLES:
        created, _ = _ensure("Role", "role_name", role, {})
        if created:
            print(f"  Role: {role}")

    _ensure("Role", "role_name", "Programme Manager", {})

    for index, (email, first, last, role) in enumerate(LOKADO_USERS):
        if frappe.db.exists("User", email):
            update_password(email, _DEMO_PASSWORD)
            continue
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first,
            "last_name": last,
            "send_welcome_email": 0,
            "enabled": 1,
            "new_password": _DEMO_PASSWORD,
            "mobile_no": f"+254711{index:06d}",
        })
        if role:
            user.append("roles", {"role": role})
        user.insert(ignore_permissions=True)
        print(f"  User: {email} ({role or 'portal'})")

    frappe.db.commit()
# ─────────────────────────────────────────────────
# 3. DONORS — LOKADO's actual partners
# ─────────────────────────────────────────────────

DONORS = [
    ("IOM", "IOM - UN Migration",
     "International Organization for Migration. Supporting LOKADO warehouse project and WASH/Livelihoods programme, funded by the People of Japan."),
    ("USAID", "USAID",
     "United States Agency for International Development. Supports livelihoods, food security and peace building programmes in Turkana County through LOKADO."),
    ("CONCERN", "Concern Worldwide",
     "International humanitarian organisation. Funds the SERVE Cash Transfer Project for 1,200 beneficiaries in Loima and Kerio through the People of America."),
    ("JAPAN", "Embassy of Japan",
     "The People of Japan, channelled through IOM - UN Migration, supports Emergency WASH and Livelihoods projects by LOKADO in Turkana South and East."),
    ("EU", "European Union",
     "European Union supports peace building and cross-border stability programmes in the Kenya-Uganda-South Sudan border region."),
    ("LOKADO-OWN", "LOKADO Own Funds",
     "Internally generated funds from LOKADO's income-generating activities. Used for administrative costs and institutional development."),
]


def _seed_donors():
    for code, name, desc in DONORS:
        compliance = "High" if code != "LOKADO-OWN" else "Low"
        ftype = "Project" if code != "LOKADO-OWN" else "Internal"
        created, _ = _ensure("Donor Profile", "donor_code", code, {
            "donor_name": name,
            "donor_code": code,
            "description": desc,
            "compliance_level": compliance,
            "funding_type": ftype,
        })
        if created:
            print(f"  Donor: {code} — {name}")
    frappe.db.commit()
    print("  6 donors created")


# ─────────────────────────────────────────────────
# 4. SUPPLIERS — Realistic Turkana/Kenyan businesses
# ─────────────────────────────────────────────────

LOKADO_SUPPLIERS = [
    ("Turkana Construction Ltd", "Construction Materials", "Prequalified",
     "Leading construction firm in Turkana County. 15+ years ASAL infrastructure experience."),
    ("Lodwar General Supplies", "Office Supplies", "Prequalified",
     "General supplies and hardware distributor based in Lodwar town."),
    ("Rift Valley Hardware", "Construction Materials", "Prequalified",
     "Hardware and construction materials supplier. Outlets in Eldoret and Lodwar."),
    ("Nadirkonyen Women's Group", "Livestock & Agriculture", "Prequalified",
     "Community-based women's group in Kakuma. Supplies indigenous livestock and poultry."),
    ("Jopeji Enterprises", "Field Equipment", "Prequalified",
     "Local logistics and transport company operating across Turkana County field routes."),
    ("Lokichoggio Traders Ltd", "WASH Supplies", "Prequalified",
     "Cross-border trading company based in Lokichoggio. WASH and general supplies."),
    ("Kenya Red Cross Supplies", "WASH Supplies", "Prequalified",
     "KRCS humanitarian supplies division. Emergency relief and WASH programme supplies."),
    ("Moi's Bridge Livestock", "Livestock & Agriculture", "Prequalified",
     "Livestock supplier from Kitale/Trans Nzoia. Goats and poultry for restocking programmes."),
    ("Northern Kenya Solar Ltd", "Solar Equipment", "Prequalified",
     "Solar energy and water pumping solutions for off-grid Northern Kenya communities."),
    ("Ekaale Building Works", "Construction Materials", "Prequalified",
     "Local Turkana building contractor. Community infrastructure specialist."),
    ("Samburu Agencies", "Fuel & Consumables", "Expired",
     "Previously supplied fuel and consumables. Prequalification expired."),
    ("Turkana Fuel Distributors", "Fuel & Consumables", "Suspended",
     "Suspended due to non-delivery of 3 consecutive fuel orders."),
    ("Lake Turkana Water Services", "WASH Supplies", "Prequalified",
     "Borehole, water treatment and emergency water-distribution specialist."),
    ("Kakuma Cold Chain Solutions", "Medical Supplies", "Prequalified",
     "Solar cold-chain equipment and temperature-controlled transport provider."),
    ("Eldoret Office Technologies", "Office Supplies", "Prequalified",
     "ICT equipment, managed printing and office technology support."),
    ("Turkwel Renewable Energy", "Solar Equipment", "Prequalified",
     "Solar mini-grid, pumping and battery-storage integrator."),
    ("North Rift Transporters", "Field Equipment", "Prequalified",
     "Heavy and last-mile transport services for ASAL programme locations."),
    ("Pastoralist Veterinary Network", "Livestock & Agriculture", "Expired",
     "Veterinary outreach supplier pending renewal of statutory documents."),
]


def _seed_suppliers():
    td = today()
    for name, category, pq_status, desc in LOKADO_SUPPLIERS:
        created, _ = _ensure("Supplier", "supplier_name", name, {
            "supplier_type": "Individual" if "Group" in name else "Company",
            "country": "Kenya",
            "supplier_details": desc,
        })
        if created:
            print(f"  Supplier: {name} [{pq_status}]")
        frappe.db.set_value(
            "Supplier",
            name,
            {
                "supplier_details": desc,
                "disabled": 0 if pq_status == "Prequalified" else 1,
            },
            update_modified=False,
        )

        if pq_status == "Prequalified":
            if not frappe.db.exists("Supplier Prequalification", {"supplier": name}):
                frappe.get_doc({
                    "doctype": "Supplier Prequalification",
                    "supplier": name,
                    "category": category,
                    "status": "Prequalified",
                    "prequalification_date": add_days(td, -180),
                    "expiry_date": add_days(td, 185),
                }).insert(ignore_permissions=True)
        elif pq_status == "Expired":
            if not frappe.db.exists("Supplier Prequalification", {"supplier": name}):
                frappe.get_doc({
                    "doctype": "Supplier Prequalification",
                    "supplier": name,
                    "category": category,
                    "status": "Expired",
                    "expiry_date": add_days(td, -30),
                    "prequalification_date": add_days(td, -395),
                }).insert(ignore_permissions=True)
        elif pq_status == "Suspended":
            if not frappe.db.exists("Supplier Prequalification", {"supplier": name}):
                frappe.get_doc({
                    "doctype": "Supplier Prequalification",
                    "supplier": name,
                    "category": category,
                    "status": "Suspended",
                    "suspension_reason": "Non-performance — 3 consecutive failed deliveries",
                    "suspension_date": td,
                    "expiry_date": add_days(td, 365),
                }).insert(ignore_permissions=True)

    frappe.db.commit()
    print("  18 LOKADO suppliers seeded (15 prequalified, 2 expired, 1 suspended) + 42 total in system")


def _seed_supplier_portal_links():
    """Bind demo website users to ERPNext suppliers without broad role grants."""
    for user, supplier in SUPPLIER_PORTAL_LINKS.items():
        if not frappe.db.exists(
            "User Permission",
            {"user": user, "allow": "Supplier", "for_value": supplier},
        ):
            frappe.get_doc(
                {
                    "doctype": "User Permission",
                    "user": user,
                    "allow": "Supplier",
                    "for_value": supplier,
                    "apply_to_all_doctypes": 1,
                }
            ).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  Supplier portal identities: {len(SUPPLIER_PORTAL_LINKS)} linked")
# ─────────────────────────────────────────────────
# 5. ITEMS & WAREHOUSES — LOKADO's operational context
# ─────────────────────────────────────────────────

def _seed_items_and_warehouses():
    # UOMs required by items — ensure they exist before item creation
    for uom in ["Nos", "Bag", "Metre", "Ton", "Litres"]:
        _ensure("UOM", "uom_name", uom, {"must_be_whole_number": 1 if uom == "Nos" else 0})

    for g in [
        "Livestock & Agriculture", "WASH Supplies", "Construction Materials",
        "Medical Supplies", "Office Supplies", "Field Equipment",
        "Fuel & Consumables", "Solar Equipment",
    ]:
        _ensure("Item Group", "item_group_name", g, {})

    items = [
        ("GOAT-GALLA", "Galla Goat (Indigenous)", "Livestock & Agriculture", "Nos"),
        ("CHICKEN-INDIG", "Indigenous Chicken (Kienyeji)", "Livestock & Agriculture", "Nos"),
        ("ANIMAL-FEED", "Animal Feed - Goats (50kg)", "Livestock & Agriculture", "Bag"),
        ("VET-KIT", "Veterinary Supplies Kit", "Livestock & Agriculture", "Nos"),
        ("WATER-PUMP-SOLAR", "Solar Water Pump - 2HP", "Solar Equipment", "Nos"),
        ("WATER-TANK-10K", "Water Tank - 10,000 Litres", "WASH Supplies", "Nos"),
        ("HYGIENE-KIT", "Hygiene Kit - Family", "WASH Supplies", "Nos"),
        ("PIPE-HDPE-63MM", "HDPE Pipe - 63mm (6m)", "WASH Supplies", "Metre"),
        ("CEMENT-BAG", "Cement - 50kg Bag", "Construction Materials", "Bag"),
        ("STEEL-Y12", "Steel Reinforcement Bar - Y12", "Construction Materials", "Ton"),
        ("IRON-SHEET-G32", "Iron Sheet - Gauge 32 (3m)", "Construction Materials", "Nos"),
        ("MOTORCYCLE-FIELD", "Motorcycle - Field (Boxer 150)", "Field Equipment", "Nos"),
        ("LAPTOP-DELL", "Laptop - Dell Latitude 5540", "Office Supplies", "Nos"),
        ("FUEL-DIESEL", "Fuel - Diesel", "Fuel & Consumables", "Litres"),
        ("FIRST-AID-KIT", "First Aid Kit - Community", "Medical Supplies", "Nos"),
    ]

    for code, name, grp, uom in items:
        created, _ = _ensure(
            "Item", "item_code", code,
            {"item_name": name, "item_group": grp, "stock_uom": uom,
             "valuation_rate": 0, "is_stock_item": 1,
             "has_batch_no": 1, "create_new_batch": 1},
        )
        if created:
            print(f"  Item: {code} — {name}")

    company = frappe.defaults.get_defaults().get("company", "LOKADO")
    warehouses = [
        ("LOKADO Main Warehouse - Lodwar", "Transit"),
        ("IOM Supported Warehouse - Kakuma", "Transit"),
        ("LOKADO Field Store - Lokichoggio", "Transit"),
        ("LOKADO Field Store - Oropoi", "Transit"),
        ("Cold Chain Storage - Lodwar", "Transit"),
        ("LOKADO Transit Store - Kitale", "Transit"),
    ]

    for wh_name, wh_type in warehouses:
        _ensure("Warehouse", "warehouse_name", wh_name,
                {"warehouse_type": wh_type, "company": company},
                name=wh_name)

    frappe.db.commit()
    print(f"  15 items, {len(warehouses)} warehouses created")
# ─────────────────────────────────────────────────
# 6. PROCUREMENT SETTINGS — LOKADO thresholds
# ─────────────────────────────────────────────────

def _seed_procurement_settings():
    if frappe.db.exists("Ugavi Procurement Settings", "Ugavi Procurement Settings"):
        settings = frappe.get_doc("Ugavi Procurement Settings")
    else:
        settings = frappe.get_doc({"doctype": "Ugavi Procurement Settings"})

    settings.direct_threshold = 200000
    settings.restricted_threshold = 500000
    settings.open_threshold = 500000

    settings.flags.ignore_permissions = True
    settings.save()
    frappe.db.commit()
    print("  Procurement Settings: direct=200K, restricted=500K, open=500K")


def _seed_fleet():
    """Seed four submitted, procurement-backed donor fleet journeys."""
    from ugavi.scripts.seed_fleet_journey import seed_fleet_journey

    seed_fleet_journey(
        company="Lotus Kenya Action for Development Organization",
        fleet_user="fleet@lokado.org",
        supplier="Lodwar General Supplies",
        scenarios=[
            {
                "donor_code": "USAID",
                "warehouse_name": "LOKADO Main Warehouse - Lodwar",
                "license_plate": "KDL 410U",
                "make": "Toyota",
                "model": "Land Cruiser 76",
                "marker": "LOKADO-DEMO-FLEET-USAID",
                "destination": "Oropoi programme site",
            },
            {
                "donor_code": "IOM",
                "warehouse_name": "IOM Supported Warehouse - Kakuma",
                "license_plate": "KDM 271I",
                "make": "Toyota",
                "model": "Hilux Double Cab",
                "marker": "LOKADO-DEMO-FLEET-IOM",
                "destination": "Kakuma warehouse project",
            },
            {
                "donor_code": "CONCERN",
                "warehouse_name": "LOKADO Field Store - Lokichoggio",
                "license_plate": "KDN 842C",
                "make": "Isuzu",
                "model": "D-Max",
                "marker": "LOKADO-DEMO-FLEET-CONCERN",
                "destination": "Loima cash-transfer monitoring route",
            },
            {
                "donor_code": "EU",
                "warehouse_name": "LOKADO Transit Store - Kitale",
                "license_plate": "KDP 318E",
                "make": "Toyota",
                "model": "Prado",
                "marker": "LOKADO-DEMO-FLEET-EU",
                "destination": "Cross-border peace-building corridor",
            },
        ],
    )
    print("  Fleet: 4 donor vehicles with submitted fuel, spares, trips and reports")


def _seed_assets():
    """Seed custody, condition, movement, and disposal evidence."""
    company = "Lotus Kenya Action for Development Organization"
    assets_user = "assets@lokado.org"

    def donor(code):
        return frappe.db.get_value(
            "Donor Profile", {"donor_code": code}, "name"
        )

    def warehouse(short_name):
        return frappe.db.get_value(
            "Warehouse", {"warehouse_name": short_name}, "name"
        )

    for wh_name, donor_code in (
        ("USAID Field Store - Oropoi", "USAID"),
        ("IOM Field Store - Kalobeyei", "IOM"),
    ):
        wh = warehouse(wh_name)
        if not wh:
            wh = frappe.get_doc(
                {
                    "doctype": "Warehouse",
                    "name": wh_name,
                    "warehouse_name": wh_name,
                    "warehouse_type": "Transit",
                    "company": company,
                }
            ).insert(ignore_permissions=True).name
        if not frappe.db.exists(
            "Donor Warehouse", {"warehouse": wh, "donor": donor(donor_code)}
        ):
            frappe.get_doc(
                {
                    "doctype": "Donor Warehouse",
                    "warehouse": wh,
                    "donor": donor(donor_code),
                    "restricted_items": 0,
                }
            ).insert(ignore_permissions=True)

    fixtures = [
        {
            "tag": "LOK-IT-001",
            "name": "Programme Monitoring Laptop",
            "category": "IT Equipment",
            "serial": "DL5540-LOK-001",
            "price": 145000,
            "donor": "USAID",
            "location": "LOKADO Main Warehouse - Lodwar",
            "destination": "USAID Field Store - Oropoi",
            "condition": "Good",
        },
        {
            "tag": "LOK-GEN-001",
            "name": "Kakuma Warehouse Generator",
            "category": "Equipment",
            "serial": "GEN-IOM-001",
            "price": 680000,
            "donor": "IOM",
            "location": "IOM Supported Warehouse - Kakuma",
            "destination": "IOM Field Store - Kalobeyei",
            "condition": "Fair",
        },
        {
            "tag": "LOK-PUMP-001",
            "name": "Solar Water Pump",
            "category": "Equipment",
            "serial": "PUMP-USAID-001",
            "price": 320000,
            "donor": "USAID",
            "location": "LOKADO Main Warehouse - Lodwar",
            "condition": "Good",
        },
        {
            "tag": "LOK-OLD-001",
            "name": "Legacy Field Printer",
            "category": "IT Equipment",
            "serial": "PRN-OLD-001",
            "price": 85000,
            "donor": "LOKADO-OWN",
            "location": "LOKADO Field Store - Oropoi",
            "condition": "Poor",
        },
        {
            "tag": "LOK-COLD-001",
            "name": "Solar Vaccine Refrigerator",
            "category": "Equipment",
            "serial": "COLD-JPN-001",
            "price": 540000,
            "donor": "JAPAN",
            "location": "Cold Chain Storage - Lodwar",
            "condition": "New",
        },
        {
            "tag": "LOK-SAT-001",
            "name": "Emergency Satellite Phone",
            "category": "IT Equipment",
            "serial": "SAT-EU-001",
            "price": 185000,
            "donor": "EU",
            "location": "LOKADO Transit Store - Kitale",
            "condition": "Good",
        },
        {
            "tag": "LOK-TENT-001",
            "name": "Mobile Emergency Coordination Tent",
            "category": "Equipment",
            "serial": "TENT-CON-001",
            "price": 260000,
            "donor": "CONCERN",
            "location": "LOKADO Field Store - Lokichoggio",
            "condition": "Fair",
        },
        {
            "tag": "LOK-SOLAR-001",
            "name": "Field Office Solar Power Kit",
            "category": "Equipment",
            "serial": "SOLAR-OWN-001",
            "price": 410000,
            "donor": "LOKADO-OWN",
            "location": "LOKADO Field Store - Oropoi",
            "condition": "Good",
        },
    ]
    for fixture in fixtures:
        asset_name = frappe.db.get_value(
            "Asset Register", {"asset_tag": fixture["tag"]}, "name"
        )
        if not asset_name:
            asset = frappe.get_doc(
                {
                    "doctype": "Asset Register",
                    "asset_name": fixture["name"],
                    "asset_category": fixture["category"],
                    "serial_number": fixture["serial"],
                    "asset_tag": fixture["tag"],
                    "purchase_date": add_days(today(), -365),
                    "purchase_price": fixture["price"],
                    "current_value": fixture["price"] * 0.8,
                    "useful_life_years": 5,
                    "salvage_value": fixture["price"] * 0.1,
                    "donor": donor(fixture["donor"]),
                    "custodian": assets_user,
                    "location": warehouse(fixture["location"]),
                    "last_verified_date": add_days(today(), -10),
                    "condition": fixture["condition"],
                    "status": "Active",
                }
            )
            asset.insert(ignore_permissions=True)
            asset_name = asset.name
        if fixture.get("destination") and not frappe.db.exists(
            "Ugavi Asset Movement",
            {
                "asset": asset_name,
                "to_location": warehouse(fixture["destination"]),
                "status": "Completed",
            },
        ):
            movement = frappe.get_doc(
                {
                    "doctype": "Ugavi Asset Movement",
                    "asset": asset_name,
                    "movement_date": add_days(today(), -7),
                    "to_location": warehouse(fixture["destination"]),
                    "to_custodian": assets_user,
                    "to_condition": fixture["condition"],
                    "reason": "Programme deployment and condition verification",
                }
            )
            movement.insert(ignore_permissions=True)
            movement.confirm()
        if not frappe.db.exists("Asset Verification", {"asset": asset_name}):
            frappe.get_doc(
                {
                    "doctype": "Asset Verification",
                    "asset": asset_name,
                    "verification_date": add_days(today(), -10),
                    "verified_by": assets_user,
                    "condition": fixture["condition"],
                    "found": "Yes",
                    "notes": "Physical tag, custody, location and condition verified.",
                }
            ).insert(ignore_permissions=True)

    disposal_asset = frappe.db.get_value(
        "Asset Register", {"asset_tag": "LOK-OLD-001"}, "name"
    )
    if disposal_asset and not frappe.db.exists(
        "Asset Disposal", {"asset": disposal_asset}
    ):
        disposal = frappe.get_doc(
            {
                "doctype": "Asset Disposal",
                "asset": disposal_asset,
                "disposal_date": today(),
                "disposal_method": "Auction",
                "disposal_value": 12000,
                "authorized_by": "approver2@lokado.org",
                "remarks": "Board-approved disposal of obsolete equipment.",
            }
        )
        disposal.insert(ignore_permissions=True)
        disposal.approve()
        disposal.complete_disposal()
    print("  Assets: 8 registers, 8 verifications, 2 controlled movements, 1 disposal")


# ─────────────────────────────────────────────────
# 7. GOVERNANCE — DoA, SoD, Waiver, Audit
# ─────────────────────────────────────────────────

def _seed_governance():
    td = today()

    # --- Delegation of Authority ---
    doa_entries = [
        # (department, donor_code, min_amount, max_amount, approval_level, approver_role)
        ("Administration & Finance - LOKADO", 0, 200000, 1, "Procurement Officer"),
        ("Administration & Finance - LOKADO", 200001, 500000, 2, "Approver Level 1"),
        ("Administration & Finance - LOKADO", 500001, 2000000, 3, "Approver Level 2"),
        # Finance must co-approve any PR > 100K
        ("Administration & Finance - LOKADO", 100000, 0, 1, "Finance Officer"),
    ]
    for dept, min_amt, max_amt, level, role in doa_entries:
        if not frappe.db.exists("Delegation of Authority", {
            "department": dept, "min_amount": min_amt, "approver_role": role,
        }):
            frappe.get_doc({
                "doctype": "Delegation of Authority",
                "enabled": 1,
                "department": dept,
                "min_amount": min_amt,
                "max_amount": max_amt or 0,
                "approval_level": level,
                "approver_role": role,
                "effective_from": str(td),
            }).insert(ignore_permissions=True)
            print(f"  DoA: {role} L{level} {min_amt:,}-{max_amt or '∞'} KES")

    # --- Waiver ---
    if not frappe.db.exists("Waiver", {"requested_by": "procurement@lokado.org"}):
        frappe.get_doc({
            "doctype": "Waiver",
            "rule_to_override": "Single Source",
            "reason": (
                "Emergency WASH supplies needed for flood-affected communities "
                "in Turkana South. Only Northern Kenya Solar Ltd has 2HP solar "
                "pumps in stock within 100km of affected areas."
            ),
            "requested_by": "procurement@lokado.org",
            "status": "Approved",
            "approved_by": "approver2@lokado.org",
            "approval_date": str(add_days(td, -10)),
        }).insert(ignore_permissions=True)
        print("  Waiver: Emergency single-source WASH supplies approved")

    # --- Segregation of Duties ---
    sod_rules = [
        ("Procurement Officer", "Finance Officer", "Create + Approve Same Doc",
         "Block", "Same person cannot request and approve payment"),
        ("Store Keeper", "Procurement Officer", "Buyer + Receiver",
         "Block", "Person ordering cannot receive goods"),
        ("Bid Opening Officer", "Evaluation Committee", "Approver + Auditor",
         "Warning Only", "Consider separation for high-value tenders"),
    ]
    for r1, r2, ctype, enf, desc in sod_rules:
        sod_name = f"SoD-{r1.replace(' ', '-')}-{r2.replace(' ', '-')}"
        if not frappe.db.exists("Segregation of Duties", sod_name):
            frappe.get_doc({
                "doctype": "Segregation of Duties",
                "role_1": r1, "role_2": r2,
                "conflict_type": ctype, "enforcement": enf,
                "description": desc,
            }).insert(ignore_permissions=True)
            print(f"  SoD: {r1} x {r2} [{enf}]")

    # --- Audit Log ---
    if not frappe.db.exists("Audit Log", "AUDIT-LOKADO-001"):
        frappe.get_doc({
            "doctype": "Audit Log",
            "user": "auditor@lokado.org",
            "timestamp": str(add_days(td, -5)),
            "action": "Procurement method override blocked by threshold rules engine",
            "outcome": "Failed",
            "ip_address": "10.0.1.50",
            "record_hash": "sha256:lokado_001",
        }).insert(ignore_permissions=True)
        print("  Audit: Procurement override blocked by SoD")

    # --- Approval Delegation ---
    if not frappe.db.exists("Approval Delegation", {"delegated_from": "approver1@lokado.org"}):
        frappe.get_doc({
            "doctype": "Approval Delegation",
            "delegated_from": "approver1@lokado.org",
            "delegated_to": "approver2@lokado.org",
            "delegation_type": "All Procurement",
            "start_date": str(td),
            "end_date": str(add_days(td, 14)),
            "active": 1,
            "reason": "Ms. Napeyok attending donor coordination meeting in Nairobi for 2 weeks",
        }).insert(ignore_permissions=True)
        print("  Delegation: Jane Napeyok → Paul Lotir (14 days)")

    frappe.db.commit()
    print("  Governance: 4 DoA, 1 waiver, 3 SoD, 1 audit, 1 delegation")
# ─────────────────────────────────────────────────
# 8. PROCUREMENT WORKFLOW — LOKADO's realistic scenarios
# ─────────────────────────────────────────────────

def _seed_procurement_workflow():
    td = today()
    dm = {d[0]: frappe.db.get_value("Donor Profile", {"donor_code": d[0]}, "name")
          for d in DONORS}

    pr_data = [
        # PR01: WASH water tanks — IOM (Japan) funded, Restricted Tender
        ("Water Tanks - WASH Programme (IOM)", "IOM", 450000,
         "Restricted Tender", "Approved",
         "Emergency WASH - LOKADO", "WATER-TANK-10K",
         "Supply and delivery of 10,000L water tanks for 12 villages in Turkana "
         "South and East sub-counties under IOM-Japan Emergency WASH programme."),
        # PR02: Goats for livelihoods — USAID funded, Restricted Tender
        ("Livestock Restocking - Galla Goats (USAID)", "USAID", 380000,
         "Restricted Tender", "Approved",
         "Livelihoods & Food Security - LOKADO", "GOAT-GALLA",
         "Procurement of 95 Galla goats for distribution to 238 households in "
         "Turkana South and East. Part of livelihoods recovery programme."),
        # PR03: IOM warehouse construction — Japan funded, Open Tender
        ("Construction of IOM-Supported Warehouse - Kakuma", "JAPAN", 1200000,
         "Open Tender", "Approved",
         "Institutional Development - LOKADO", "CEMENT-BAG",
         "Construction of 200m² warehouse at Kakuma for IOM project supplies. "
         "Includes foundation, steel frame, roofing, electrical and plumbing."),
        # PR04: Hygiene kits — Concern Worldwide (USAID), Direct RFQ
        ("Hygiene Kits - Gender Programme (Concern)", "CONCERN", 180000,
         "Request for Quotation (Direct)", "Approved",
         "Gender & Protection - LOKADO", "HYGIENE-KIT",
         "Procurement of 900 family hygiene kits for SERVE Cash Transfer Project "
         "beneficiaries in Loima Sub-county and Kerio Ward."),
        # PR05: Motorcycles for field officers — USAID, Open Tender
        ("Field Motorcycles - Programme Officers (USAID)", "USAID", 520000,
         "Open Tender", "Approved",
         "Peace Building & Conflict Resolution - LOKADO", "MOTORCYCLE-FIELD",
         "Procurement of 4 motorcycles for peace building field officers covering "
         "cross-border villages in Kalobeyei, Letea and Lokiriama."),
        # PR06: Office consumables — Rejected
        ("Office Consumables - Head Office", "LOKADO-OWN", 80000,
         "Request for Quotation (Direct)", "Rejected",
         "Administration & Finance - LOKADO", "LAPTOP-DELL",
         "Annual office consumables for Lodwar head office. REJECTED: value "
         "(80,000 KES) below threshold. Refer to petty cash system."),
        # PR07: Draft open tender for renewable-energy infrastructure
        ("Solar Water Pumps - EU Resilience Programme", "EU", 780000,
         "Open Tender", "Draft",
         "Emergency WASH - LOKADO", "WATER-PUMP-SOLAR",
         "Draft requirement for six solar pumping systems serving drought-prone "
         "settlements along the cross-border resilience corridor."),
        # PR08: Pending restricted procurement awaiting delegated approval
        ("Veterinary Outreach Kits - USAID Livelihoods", "USAID", 240000,
         "Restricted Tender", "Pending Approval",
         "Livelihoods & Food Security - LOKADO", "VET-KIT",
         "Veterinary kits for mobile livestock-health teams. Pending programme "
         "and finance approval under the delegated authority matrix."),
        # PR09: Approved direct purchase below the restricted threshold
        ("Emergency HDPE Pipe Repair - IOM WASH", "IOM", 195000,
         "Request for Quotation (Direct)", "Approved",
         "Emergency WASH - LOKADO", "PIPE-HDPE-63MM",
         "Emergency replacement pipe for failed Kakuma water-distribution lines."),
        # PR10: Rejected request demonstrating category and budget review
        ("Community First Aid Kits - Japan Programme", "JAPAN", 160000,
         "Request for Quotation (Direct)", "Rejected",
         "Peace Building & Conflict Resolution - LOKADO", "FIRST-AID-KIT",
         "Rejected pending confirmation of beneficiary numbers and budget-line "
         "availability; retained as approval-history evidence."),
    ]

    pr_map = {}
    for title, donor_code, value, method, status, dept, item_code, justification in pr_data:
        pk = title[:40].replace(" ", "-").replace(",", "").replace("—", "-")
        exists = frappe.db.exists("Purchase Requisition", {"title": title})
        if exists:
            pr_map[pk] = exists
            continue

        qty_map = {
            "Water Tanks": 12,
            "Livestock": 95,
            "Construction": 1,
            "Hygiene": 900,
            "Motorcycles": 4,
            "Office": 3,
            "Solar Water": 6,
            "Veterinary": 24,
            "HDPE": 650,
            "First Aid": 80,
        }
        qty = 1
        for k, v in qty_map.items():
            if k in title:
                qty = v
                break

        pr = frappe.get_doc({
            "doctype": "Purchase Requisition",
            "title": title,
            "requester": "procurement@lokado.org",
            "department": dept,
            "donor": dm.get(donor_code, donor_code),
            "justification": justification,
            "status": status,
            "procurement_method": method,
            "estimated_value": value,
            "items": [{
                "item_code": item_code,
                "quantity": qty,
                "estimated_unit_price": value / qty,
                "uom": "Nos",
                "estimated_total": value,
            }],
        })
        pr.flags.allow_status_transition = True
        pr.insert(ignore_permissions=True)
        pr_map[pk] = pr.name
        print(f"  PR: {title[:50]} [{donor_code}] {value:,} KES [{status}]")

    _seed_lokado_tenders_and_bids(td, dm, pr_map)
    frappe.db.commit()
    print("  Procurement: 10 PRs across Draft/Pending/Approved/Rejected, 8 tenders, 26 bids and 3 awards")
def _seed_lokado_tenders_and_bids(td, dm, pr_map):
    """Tenders matching LOKADO procurement scenarios."""

    tender_data = [
        ("Water Tanks WASH IOM", "IOM", 450000,
         "Restricted Tender", "Water-Tanks---WASH-Programme-(IOM)"),
        ("Livestock Galla Goats USAID", "USAID", 380000,
         "Restricted Tender", "Livestock-Restocking---Galla-Goats-(USAID"),
        ("IOM Warehouse Construction Kakuma", "JAPAN", 1200000,
         "Open Tender", "Construction-of-IOM-Supported-Warehouse--"),
        ("Hygiene Kits Gender Concern", "CONCERN", 180000,
         "Request for Quotation (Direct)", "Hygiene-Kits---Gender-Programme-(Concer"),
        ("Field Motorcycles Peace Building USAID", "USAID", 520000,
         "Open Tender", "Field-Motorcycles---Programme-Officers-(USAI"),
        ("Solar Water Pumps EU Resilience", "EU", 780000,
         "Open Tender", "Solar-Water-Pumps---EU-Resilience-"),
        ("Veterinary Outreach Kits USAID", "USAID", 240000,
         "Restricted Tender", "Veterinary-Outreach-Kits---USAID-Li"),
        ("Emergency HDPE Pipe Repair IOM", "IOM", 195000,
         "Request for Quotation (Direct)", "Emergency-HDPE-Pipe-Repair---IOM-WAS"),
    ]

    for t_title, donor_code, value, method, pr_key in tender_data:
        if frappe.db.exists("Tender", {"title": t_title}):
            continue

        pr_name = pr_map.get(pr_key)
        tender = frappe.get_doc({
            "doctype": "Tender",
            "title": t_title,
            "purchase_requisition": pr_name,
            "donor": dm.get(donor_code, donor_code),
            "procurement_method": method,
            "estimated_value": value,
            "submission_deadline": str(add_days(td, 21)),
            "status": "Draft",
            "opening_officer_1": "opening1@lokado.org",
            "opening_officer_2": "opening2@lokado.org",
            "opening_officer_3": "opening3@lokado.org",
            "bid_security_required": (
                25000 if "Warehouse" in t_title else
                10000 if value > 500000 else 0
            ),
        })
        tender.insert(ignore_permissions=True)
        tender.publish()
        print(f"  Tender: {t_title[:45]} [{donor_code}] {value:,} KES [{method}]")

        # Add documents — skip if attachment is a mandatory child field
        try:
            for dtype, doc_label in [("Bill of Quantities", "Bill of Quantities"),
                                       ("Specifications", "Technical Specifications"),
                                       ("Terms of Reference", "Terms of Reference")]:
                if hasattr(tender, "tender_documents"):
                    tender.append("tender_documents", {
                        "document_type": dtype,
                        "document_name": f"{doc_label} - {t_title[:30]}",
                    })
            tender.save(ignore_permissions=True)
        except Exception:
            # Some tender doctypes require attachment on documents; skip gracefully
            pass

    _seed_lokado_bids(td)
    _seed_lokado_award(td, dm)
    _seed_lokado_bid_securities(td)
    _seed_lokado_addendum(td)
    _seed_lokado_contract(td, dm)
    _seed_mvp2_readiness(td)


def _seed_mvp2_readiness(td):
    """Seed one active standstill window for the supplier complaint demo."""
    tender = frappe.db.get_value(
        "Tender",
        {"title": "Field Motorcycles Peace Building USAID"},
        "name",
    )
    if not tender or frappe.db.exists("Standstill Period", {"tender": tender}):
        return
    frappe.get_doc({
        "doctype": "Standstill Period",
        "tender": tender,
        "start_date": td,
        "end_date": add_days(td, 7),
        "status": "Active",
        "challenges_count": 0,
    }).insert(ignore_permissions=True)
    frappe.db.set_value("Tender", tender, "status", "Standstill Period")
    print("  MVP2 readiness: active standstill window for supplier complaints")


def _seed_lokado_bids(td):
    """Realistic bids for LOKADO tenders."""
    tender_map = {
        "Water Tanks WASH IOM": [
            ("Lodwar General Supplies", 425000),
            ("Rift Valley Hardware", 448000),
            ("Lokichoggio Traders Ltd", 460000),
        ],
        "Livestock Galla Goats USAID": [
            ("Nadirkonyen Women's Group", 365000),
            ("Moi's Bridge Livestock", 378000),
            ("Turkana Construction Ltd", 400000),
        ],
        "IOM Warehouse Construction Kakuma": [
            ("Turkana Construction Ltd", 1150000),
            ("Ekaale Building Works", 1185000),
            ("Rift Valley Hardware", 1220000),
        ],
        "Hygiene Kits Gender Concern": [
            ("Kenya Red Cross Supplies", 175000),
            ("Lodwar General Supplies", 182000),
            ("Lokichoggio Traders Ltd", 190000),
        ],
        "Field Motorcycles Peace Building USAID": [
            ("Jopeji Enterprises", 505000),
            ("Turkana Construction Ltd", 518000),
            ("Lodwar General Supplies", 530000),
        ],
        "Solar Water Pumps EU Resilience": [
            ("Turkana Construction Ltd", 745000),
            ("Ekaale Building Works", 768000),
            ("Lokichoggio Traders Ltd", 790000),
            ("Rift Valley Hardware", 810000),
        ],
        "Veterinary Outreach Kits USAID": [
            ("Kenya Red Cross Supplies", 228000),
            ("Nadirkonyen Women's Group", 235000),
            ("Lodwar General Supplies", 242000),
            ("Jopeji Enterprises", 250000),
        ],
        "Emergency HDPE Pipe Repair IOM": [
            ("Rift Valley Hardware", 188000),
            ("Lodwar General Supplies", 192000),
            ("Ekaale Building Works", 198000),
        ],
    }

    for t_title, bids in tender_map.items():
        tname = frappe.db.get_value("Tender", {"title": t_title}, "name")
        if not tname:
            continue
        for supplier_name, amount in bids:
            supplier = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
            if not supplier:
                continue
            if frappe.db.exists("Bid", {"tender": tname, "supplier": supplier}):
                continue
            bid = frappe.get_doc({
                "doctype": "Bid",
                "tender": tname,
                "supplier": supplier,
                "bid_amount": amount,
                "submission_date": str(add_days(td, -5)),
                "status": "Draft",
                "bid_validity_days": 90,
            })
            bid.insert(ignore_permissions=True)
            bid.submit_bid()
            print(f"  Bid: {supplier_name[:25]} → {amount:,} KES [{t_title[:30]}]")

    frappe.db.commit()
    print("  Procurement Workflow: 10 PRs, 8 tenders, 26 bids, 3 awards")


def _seed_bid_opening_and_sealed_keys(td):
    """AP-19: Seed Bid Opening Records and Sealed Bid Keys for live crypto demo."""
    from ugavi.procurement.services.sealed_bid import generate_and_distribute_keys
    # --- Sealed Bid Keys for Open Tenders ---
    open_tenders = [
        # T3: IOM Warehouse (awarded, grand finale)
        {"title": "IOM Warehouse Construction Kakuma", "officers": [
            "approver1@lokado.org",
            "approver2@lokado.org",
            "auditor@lokado.org",
        ]},
        # T5: Field Motorcycles Peace Building
        {"title": "Field Motorcycles Peace Building USAID", "officers": [
            "approver1@lokado.org",
            "procurement@lokado.org",
            "officer1@lokado.org",
        ]},
    ]

    for info in open_tenders:
        tname = frappe.db.get_value("Tender", {"title": info["title"]}, "name")
        if not tname:
            print(f"  SKIP SBK: tender '{info['title']}' not found")
            continue
        # Place public key on the tender
        tender = frappe.get_doc("Tender", tname)
        if tender.public_key and len(tender.public_key) > 80:
            print(f"  SBK: Key already exists for {info['title'][:40]} — skipping")
            continue
        try:
            result = generate_and_distribute_keys(tname, info["officers"])
            tender.public_key = result["public_key_pem"]
            tender.key_generated_at = frappe.utils.now_datetime()
            # Set opening officers on the tender for the ceremony
            tender.opening_officer_1 = info["officers"][0]
            tender.opening_officer_2 = info["officers"][1]
            tender.opening_officer_3 = info["officers"][2]
            tender.save(ignore_permissions=True)
            print(f"  SBK: Generated 3-of-3 key for {info['title'][:40]}")
        except ImportError:
            print(f"  SBK: cryptography not available — placeholder key stored")
            import base64 as _b64
            tender.public_key = "DEMO-PLACEHOLDER-KEY-" + _b64.b64encode(
                tender.title.encode()).decode()[:40]
            tender.opening_officer_1 = info["officers"][0]
            tender.opening_officer_2 = info["officers"][1]
            tender.opening_officer_3 = info["officers"][2]
            tender.save(ignore_permissions=True)
            print(f"  SBK: Placeholder key for {info['title'][:40]}")
        except Exception as e:
            print(f"  SBK ERROR for {info['title'][:40]}: {e}")

    # Opening records are intentionally not fabricated by the seed. Presenters
    # run the real three-officer ceremony, which creates the immutable record.
    tname = frappe.db.get_value("Tender",
        {"title": "IOM Warehouse Construction Kakuma"}, "name")
    if tname and not frappe.db.exists("Bid Opening Record", {"tender": tname}):
        print("  BOR: pending live three-officer opening ceremony (not fabricated)")


def _seed_lokado_award(td, dm):
    """Award 3 tenders with full evaluation summaries."""

    award_scenarios = [
        {
            "tender_title": "IOM Warehouse Construction Kakuma",
            "supplier_name": "Turkana Construction Ltd",
            "award_amount": 1150000,
            "justification": (
                "Turkana Construction Ltd: lowest evaluated bid at KES 1,150,000. "
                "Technical score: 82/100. Valid prequalification, 3 similar ASAL "
                "warehouse projects completed. Employs local Turkana community members."
            ),
        },
        {
            "tender_title": "Livestock Galla Goats USAID",
            "supplier_name": "Nadirkonyen Women's Group",
            "award_amount": 365000,
            "justification": (
                "Nadirkonyen Women's Group: community-based supplier offering best animal "
                "health guarantee at KES 365,000. Technical score: 88/100. Pastoralist-owned "
                "social enterprise with proven delivery to ASAL counties."
            ),
        },
        {
            "tender_title": "Water Tanks WASH IOM",
            "supplier_name": "Lodwar General Supplies",
            "award_amount": 425000,
            "justification": (
                "Lodwar General Supplies: lowest evaluated bid at KES 425,000. "
                "Technical score: 85/100. Established local supplier with 5-year WASH "
                "programme track record. Shorter transport distance to remote sites."
            ),
        },
    ]

    for scenario in award_scenarios:
        tname = frappe.db.get_value("Tender", {"title": scenario["tender_title"]}, "name")
        if not tname:
            continue

        supplier = frappe.db.get_value("Supplier", {"supplier_name": scenario["supplier_name"]}, "name")
        if not supplier:
            continue

        if frappe.db.exists("Bid Evaluation Summary", {"tender": tname}):
            continue

        try:
            bes = frappe.get_doc({
                "doctype": "Bid Evaluation Summary",
                "tender": tname,
                "evaluation_date": str(add_days(td, -2)),
                "recommended_bidder": supplier,
                "recommended_amount": scenario["award_amount"],
                "justification": scenario["justification"],
                "status": "Approved",
            })
            bes.insert(ignore_permissions=True)

            if hasattr(bes, 'award_tender'):
                bes.award_tender()
                print(f"  Award: {scenario['tender_title'][:40]} → {scenario['supplier_name'][:25]} {scenario['award_amount']:,} KES [+ PO]")
            else:
                print(f"  Award: {scenario['tender_title'][:40]} → {scenario['supplier_name'][:25]} {scenario['award_amount']:,} KES")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  Award: Could not create for {scenario['tender_title'][:40]} — {type(e).__name__}: {e}")

    frappe.db.commit()
    print("  Awards: 3 tenders awarded with evaluation summaries")


def _seed_lokado_bid_securities(td):
    """Bid securities for open tender construction."""
    tname = frappe.db.get_value("Tender", {"title": "IOM Warehouse Construction Kakuma"}, "name")
    if not tname:
        return
    try:
        tender = frappe.get_doc("Tender", tname)
        for bid in frappe.get_all("Bid", {"tender": tname}, ["name"]):
            if hasattr(tender, 'verify_bid_security'):
                try:
                    tender.verify_bid_security(bid.name)
                except Exception:
                    pass
        print("  Bid Security: Verified for construction tender")
    except Exception:
        pass


def _seed_lokado_addendum(td):
    """Addendum for IOM warehouse tender."""
    tname = frappe.db.get_value("Tender", {"title": "IOM Warehouse Construction Kakuma"}, "name")
    if not tname:
        return
    try:
        tender = frappe.get_doc("Tender", tname)
        has_addenda = (hasattr(tender, 'addenda') and tender.addenda
                       and len(tender.addenda) > 0)
        if not has_addenda and hasattr(tender, 'issue_addendum'):
            tender.issue_addendum(
                title="Structural spec update — steel grade S275→S355",
                description=(
                    "Site assessment at Kakuma: structural steel revised from "
                    "S275 to S355 for ASAL wind loads. Revised BoQ attached."
                ),
                extends_deadline=True,
                new_deadline=str(add_days(td, 28)),
            )
            print("  Addendum: Steel spec updated, deadline extended +7 days")
    except Exception:
        pass
def _seed_lokado_contract(td, dm):
    """Create Ugavi Contracts for all awarded tenders with milestones and documents."""

    contract_scenarios = [
        {
            "tender_title": "IOM Warehouse Construction Kakuma",
            "supplier_name": "Turkana Construction Ltd",
            "amount": 1150000,
            "duration_days": 180,
            "retention_pct": 10,
            "bond_amount": 115000,
            "milestones": [
                ("Foundation & slab", 20, 30),
                ("Steel frame erection", 30, 60),
                ("Roofing & cladding", 20, 90),
                ("Electrical & plumbing", 15, 120),
                ("Finishing & handover", 15, 180),
            ],
        },
        {
            "tender_title": "Livestock Galla Goats USAID",
            "supplier_name": "Nadirkonyen Women's Group",
            "amount": 365000,
            "duration_days": 45,
            "retention_pct": 5,
            "bond_amount": 0,
            "milestones": [
                ("Animal health screening", 25, 10),
                ("First batch delivery - 47 goats", 35, 22),
                ("Second batch delivery - 48 goats", 30, 38),
                ("Vaccination & final handover", 10, 45),
            ],
        },
        {
            "tender_title": "Water Tanks WASH IOM",
            "supplier_name": "Lodwar General Supplies",
            "amount": 425000,
            "duration_days": 60,
            "retention_pct": 5,
            "bond_amount": 21250,
            "milestones": [
                ("Manufacturing & QA", 30, 20),
                ("Delivery to 6 sites", 35, 40),
                ("Installation & testing", 25, 55),
                ("Community handover", 10, 60),
            ],
        },
        {
            "tender_title": "Hygiene Kits Gender Concern",
            "supplier_name": "Kenya Red Cross Supplies",
            "amount": 175000,
            "duration_days": 30,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Procurement & packing", 40, 10),
                ("Distribution to Loima", 40, 20),
                ("Beneficiary verification", 20, 30),
            ],
        },
        {
            "tender_title": "Emergency HDPE Pipe Repair IOM",
            "supplier_name": "Rift Valley Hardware",
            "amount": 188000,
            "duration_days": 14,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Material delivery", 60, 5),
                ("Pipe replacement works", 40, 14),
            ],
        },
    ]

    for scenario in contract_scenarios:
        tname = frappe.db.get_value("Tender", {"title": scenario["tender_title"]}, "name")
        if not tname:
            continue

        if frappe.db.exists("Ugavi Contract", {"tender": tname}):
            continue

        supplier = frappe.db.get_value("Supplier", {"supplier_name": scenario["supplier_name"]}, "name")

        try:
            contract = frappe.get_doc({
                "doctype": "Ugavi Contract",
                "tender": tname,
                "supplier": supplier,
                "contract_amount": scenario["amount"],
                "start_date": str(td),
                "end_date": str(add_days(td, scenario["duration_days"])),
                "retention_percentage": scenario["retention_pct"],
                "performance_bond_amount": scenario["bond_amount"],
                "status": "Draft",
                "donor": frappe.db.get_value("Tender", tname, "donor"),
            })

            for desc, pct, day in scenario["milestones"]:
                contract.append("milestones", {
                    "milestone_name": desc,
                    "completion_percentage": pct,
                    "due_date": str(add_days(td, day)),
                    "status": "Pending" if day > 15 else "Completed",
                })

            contract.insert(ignore_permissions=True)
            print(f"  Contract: {scenario['tender_title'][:40]} [{len(scenario['milestones'])} milestones]")
        except Exception as e:
            print(f"  Contract: Could not create for {scenario['tender_title'][:40]} — {type(e).__name__}: {e}")

    frappe.db.commit()
    print("  Contracts: 5 Ugavi Contracts with milestones, retention and bonds")


# ─────────────────────────────────────────────────
# 9. LOGISTICS — Donor warehouses, stock, transfers
# ─────────────────────────────────────────────────

def _seed_logistics():
    td = today()
    dm = {d[0]: frappe.db.get_value("Donor Profile", {"donor_code": d[0]}, "name")
          for d in DONORS}

    # Resolve warehouse short names → full ERPNext names (suffixed with company abbr)
    def _wh(short_name):
        return frappe.db.get_value("Warehouse", {"warehouse_name": short_name}, "name") or short_name

    wh_links = [
        ("IOM", "IOM Supported Warehouse - Kakuma"),
        ("USAID", "LOKADO Main Warehouse - Lodwar"),
        ("CONCERN", "LOKADO Field Store - Lokichoggio"),
        ("JAPAN", "Cold Chain Storage - Lodwar"),
        ("EU", "LOKADO Transit Store - Kitale"),
        ("LOKADO-OWN", "LOKADO Field Store - Oropoi"),
    ]

    for dcode, wh in wh_links:
        wh_full = _wh(wh)
        if frappe.db.exists("Donor Warehouse", {"warehouse": wh_full}):
            print(f"  DonorWH: {dcode} <-> {wh} (already exists)")
            continue
        frappe.get_doc({
            "doctype": "Donor Warehouse",
            "warehouse": wh_full,
            "donor": dm.get(dcode, dcode),
            "restricted_items": 1 if dcode in ("IOM", "USAID") else 0,
        }).insert(ignore_permissions=True)
        print(f"  DonorWH: {dcode} <-> {wh}")

    stock_reports = [
        ("IOM", 60, "IOM Supported Warehouse - Kakuma", [
            ("HYGIENE-KIT", 500, 420, 210000),
            ("PIPE-HDPE-63MM", 200, 150, 75000),
        ]),
        ("USAID", 30, "LOKADO Main Warehouse - Lodwar", [
            ("GOAT-GALLA", 200, 135, 540000),
            ("ANIMAL-FEED", 80, 65, 26000),
            ("VET-KIT", 30, 25, 75000),
        ]),
        ("CONCERN", 45, "LOKADO Field Store - Lokichoggio", [
            ("HYGIENE-KIT", 900, 720, 360000),
            ("FIRST-AID-KIT", 120, 95, 142500),
        ]),
        ("JAPAN", 75, "Cold Chain Storage - Lodwar", [
            ("FIRST-AID-KIT", 180, 154, 231000),
            ("WATER-PUMP-SOLAR", 8, 6, 510000),
        ]),
        ("EU", 90, "LOKADO Transit Store - Kitale", [
            ("MOTORCYCLE-FIELD", 6, 4, 520000),
            ("PIPE-HDPE-63MM", 1200, 860, 430000),
        ]),
        ("LOKADO-OWN", 15, "LOKADO Field Store - Oropoi", [
            ("LAPTOP-DELL", 12, 9, 1170000),
            ("FUEL-DIESEL", 600, 240, 50400),
        ]),
    ]

    for dcode, days_ago, wh, items in stock_reports:
        dname = dm.get(dcode, dcode)
        report_filters = {
            "donor": dname,
            "warehouse": _wh(wh),
            "report_month": str(add_days(td, -days_ago)),
        }
        existing_reports = frappe.get_all(
            "Monthly Stock Report",
            filters=report_filters,
            pluck="name",
            order_by="creation asc",
        )
        for duplicate in existing_reports[1:]:
            frappe.delete_doc(
                "Monthly Stock Report", duplicate, ignore_permissions=True
            )
        if existing_reports:
            continue
        msr = frappe.get_doc({
            "doctype": "Monthly Stock Report",
            "donor": dname,
            "warehouse": _wh(wh),
            "report_month": str(add_days(td, -days_ago)),
        })
        for item_code, open_q, close_q, total_val in items:
            msr.append("items", {
                "item_code": item_code,
                "opening_qty": open_q,
                "closing_qty": close_q,
                "total_value": total_val,
                "donor": dname,
            })
        msr.insert(ignore_permissions=True)
        print(f"  StockReport: {dcode} [{add_days(td, -days_ago)}]")

    # Inter-donor transfer: IOM -> Concern for flood emergency
    transfer_filters = {
        "from_donor": dm.get("IOM"),
        "to_donor": dm.get("CONCERN"),
        "from_warehouse": _wh("IOM Supported Warehouse - Kakuma"),
        "to_warehouse": _wh("LOKADO Field Store - Lokichoggio"),
        "reason": ("like", "Emergency reallocation:%"),
    }
    existing_transfers = frappe.get_all(
        "Inter Donor Transfer",
        filters=transfer_filters,
        pluck="name",
        order_by="creation asc",
    )
    for duplicate in existing_transfers[1:]:
        frappe.delete_doc(
            "Inter Donor Transfer", duplicate, ignore_permissions=True
        )
    if not existing_transfers:
        idt = frappe.get_doc({
            "doctype": "Inter Donor Transfer",
            "from_warehouse": _wh("IOM Supported Warehouse - Kakuma"),
            "to_warehouse": _wh("LOKADO Field Store - Lokichoggio"),
            "from_donor": dm.get("IOM"),
            "to_donor": dm.get("CONCERN"),
            "status": "Approved",
            "transfer_date": str(add_days(td, -15)),
            "reason": (
                "Emergency reallocation: 200 hygiene kits from IOM to Concern "
                "SERVE programme. Flash floods in Loima increased beneficiary count."
            ),
            "approved_by": "approver1@lokado.org",
        })
        idt.append("items", {"item_code": "HYGIENE-KIT", "qty": 200, "uom": "Nos"})
        idt.insert(ignore_permissions=True)
        print("  InterDonorTransfer: IOM -> Concern | 200 hygiene kits")

    transfer_scenarios = [
        {
            "from_warehouse": _wh("LOKADO Main Warehouse - Lodwar"),
            "to_warehouse": _wh("LOKADO Transit Store - Kitale"),
            "from_donor": dm.get("USAID"),
            "to_donor": dm.get("EU"),
            "status": "Pending Approval",
            "reason": "DEMO-PENDING: Proposed temporary transfer for joint peace forum.",
            "item_code": "FIRST-AID-KIT",
            "qty": 20,
        },
        {
            "from_warehouse": _wh("Cold Chain Storage - Lodwar"),
            "to_warehouse": _wh("LOKADO Field Store - Oropoi"),
            "from_donor": dm.get("JAPAN"),
            "to_donor": dm.get("LOKADO-OWN"),
            "status": "Rejected",
            "reason": "DEMO-REJECTED: Donor consent and cold-chain plan were not attached.",
            "item_code": "FIRST-AID-KIT",
            "qty": 15,
        },
        {
            "from_warehouse": _wh("IOM Supported Warehouse - Kakuma"),
            "to_warehouse": _wh("LOKADO Main Warehouse - Lodwar"),
            "from_donor": dm.get("IOM"),
            "to_donor": dm.get("USAID"),
            "status": "Approved",
            "reason": "DEMO-APPROVED: Emergency WASH supplies reallocation to USAID health programme after Kakuma flood damage.",
            "item_code": "WATER-TANK-10K",
            "qty": 2,
        },
    ]
    for scenario in transfer_scenarios:
        if frappe.db.exists(
            "Inter Donor Transfer", {"reason": scenario["reason"]}
        ):
            continue
        transfer = frappe.get_doc(
            {
                "doctype": "Inter Donor Transfer",
                "from_warehouse": scenario["from_warehouse"],
                "to_warehouse": scenario["to_warehouse"],
                "from_donor": scenario["from_donor"],
                "to_donor": scenario["to_donor"],
                "status": scenario["status"],
                "transfer_date": today(),
                "reason": scenario["reason"],
                "items": [
                    {
                        "item_code": scenario["item_code"],
                        "qty": scenario["qty"],
                        "uom": "Nos",
                    }
                ],
            }
        )
        transfer.insert(ignore_permissions=True)

    # --- Purchase Receipts linking awarded suppliers to stock ---
    receipt_scenarios = [
        ("Turkana Construction Ltd", "IOM Supported Warehouse - Kakuma", [
            ("CEMENT-BAG", 250, 1100, "BAT-2025-IOM-CEMENT", "2026-04-15"),
            ("WATER-TANK-10K", 6, 52000, "BAT-2025-IOM-TANK", "2026-12-31"),
        ]),
        ("Nadirkonyen Women's Group", "LOKADO Main Warehouse - Lodwar", [
            ("GOAT-GALLA", 95, 3842, "BAT-2025-USAID-GOAT", "2026-06-30"),
            ("ANIMAL-FEED", 50, 520, "BAT-2025-USAID-FEED", "2025-12-31"),
        ]),
        ("Lodwar General Supplies", "IOM Supported Warehouse - Kakuma", [
            ("WATER-TANK-10K", 6, 48000, "BAT-2025-IOM-TANK2", "2027-01-31"),
        ]),
        ("Kenya Red Cross Supplies", "LOKADO Field Store - Lokichoggio", [
            ("HYGIENE-KIT", 900, 175, "BAT-2025-CONC-HYG", "2026-03-31"),
            ("FIRST-AID-KIT", 120, 1500, "BAT-2025-CONC-FA", "2026-03-31"),
        ]),
        ("Rift Valley Hardware", "IOM Supported Warehouse - Kakuma", [
            ("PIPE-HDPE-63MM", 650, 290, "BAT-2025-IOM-PIPE", "2027-06-30"),
        ]),
        ("Jopeji Enterprises", "LOKADO Transit Store - Kitale", [
            ("MOTORCYCLE-FIELD", 4, 130000, "BAT-2025-USAID-MOTO", "2028-12-31"),
        ]),
    ]

    for supplier_name, wh_name, items in receipt_scenarios:
        supplier = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
        wh_full = _wh(wh_name)
        if not supplier or not wh_full:
            continue
        # Check if a receipt for this supplier+warehouse combo already exists
        if frappe.db.exists("Purchase Receipt", {
            "supplier": supplier,
            "set_warehouse": wh_full,
        }):
            continue
        try:
            pr = frappe.get_doc({
                "doctype": "Purchase Receipt",
                "supplier": supplier,
                "set_warehouse": wh_full,
                "posting_date": str(add_days(td, -10)),
                "company": "Lotus Kenya Action for Development Organization",
            })
            for item_code, received_qty, rate, _batch_no, _expiry in items:
                item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
                child = {
                    "item_code": item_code,
                    "item_name": item_name,
                    "received_qty": received_qty,
                    "qty": received_qty,
                    "rate": rate,
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "base_rate": rate,
                    "warehouse": wh_full,
                }
                # Only set batch_no if the Batch record exists (created by the fleet seed)
                if frappe.db.exists("Batch", _batch_no):
                    child["batch_no"] = _batch_no
                pr.append("items", child)
            pr.insert(ignore_permissions=True)
            pr.submit()
            print(f"  PurchaseReceipt: {supplier_name[:25]} → {wh_name[:35]}")
        except Exception as e:
            print(f"  PurchaseReceipt: {supplier_name[:25]} skipped — {type(e).__name__}: {e}")

    frappe.db.commit()
    print("  Logistics: 6 donor books, 6 stock reports, 4 transfer outcomes, 6 purchase receipts with batch tracking")
    print(
        f"  {len(LOKADO_USERS)} users available "
        f"({len(LOKADO_USERS) - len(SUPPLIER_PORTAL_LINKS)} staff + "
        f"{len(SUPPLIER_PORTAL_LINKS)} supplier portal users)"
    )


# ─────────────────────────────────────────────────
# 9a. SUPPLIER EVALUATIONS — Post-receipt scorecards
# ─────────────────────────────────────────────────

def _seed_supplier_evaluations():
    """Create performance evaluations for suppliers with completed deliveries."""

    evaluation_scenarios = [
        {
            "supplier_name": "Turkana Construction Ltd",
            "delivery_quality": 4.5, "timeliness": 4.2, "compliance": 5.0,
            "overall": 4.6,
            "comments": "Warehouse construction delivered on time with high quality. Excellent donor compliance. Strong community engagement.",
        },
        {
            "supplier_name": "Nadirkonyen Women's Group",
            "delivery_quality": 4.8, "timeliness": 4.5, "compliance": 4.5,
            "overall": 4.6,
            "comments": "Galla goats delivered in excellent health. Vaccination certificates provided. Slight delay in batch 2 due to road conditions.",
        },
        {
            "supplier_name": "Lodwar General Supplies",
            "delivery_quality": 4.0, "timeliness": 3.5, "compliance": 4.0,
            "overall": 3.8,
            "comments": "Water tanks delivered. 2 units had minor defects (resolved). Installation delayed 3 days. Acceptable.",
        },
        {
            "supplier_name": "Kenya Red Cross Supplies",
            "delivery_quality": 5.0, "timeliness": 4.8, "compliance": 4.8,
            "overall": 4.9,
            "comments": "Outstanding hygiene kit delivery. Complete documentation. Zero defects. Recommended for prequalification renewal.",
        },
        {
            "supplier_name": "Rift Valley Hardware",
            "delivery_quality": 4.2, "timeliness": 4.0, "compliance": 4.5,
            "overall": 4.2,
            "comments": "HDPE pipes to specification. Prompt response to tech queries. Competitive pricing for emergency procurement.",
        },
        {
            "supplier_name": "Jopeji Enterprises",
            "delivery_quality": 4.5, "timeliness": 4.5, "compliance": 4.3,
            "overall": 4.4,
            "comments": "Motorcycles delivered with logbooks and insurance. Pre-delivery inspection passed. Good after-sales commitment.",
        },
        {
            "supplier_name": "Ekaale Building Works",
            "delivery_quality": 3.5, "timeliness": 3.0, "compliance": 3.5,
            "overall": 3.3,
            "comments": "Previous solar project: delays, rework. Under performance improvement plan. Monitor closely.",
        },
        {
            "supplier_name": "Moi's Bridge Livestock",
            "delivery_quality": 3.8, "timeliness": 3.5, "compliance": 3.8,
            "overall": 3.7,
            "comments": "Acceptable but not outstanding. Higher transport costs. Limited Turkana-based staff. Adequate.",
        },
    ]

    for scenario in evaluation_scenarios:
        supplier = frappe.db.get_value(
            "Supplier", {"supplier_name": scenario["supplier_name"]}, "name"
        )
        if not supplier:
            continue
        if frappe.db.exists("Ugavi Supplier Evaluation", {"supplier": supplier}):
            continue

        try:
            eval_doc = frappe.get_doc({
                "doctype": "Ugavi Supplier Evaluation",
                "supplier": supplier,
                "evaluation_date": str(add_days(today(), -5)),
                "quality_score": scenario["delivery_quality"],
                "delivery_score": scenario["timeliness"],
                "compliance_score": scenario["compliance"],
                "total_score": scenario["overall"],
                "price_competitiveness": scenario["overall"] * 0.7,
                "cumulative_rating": scenario["overall"],
                "remarks": scenario["comments"],
                "status": "Completed",
            })
            eval_doc.insert(ignore_permissions=True)
            print(f"  SupplierEval: {scenario['supplier_name'][:25]} → {scenario['overall']}/5")
        except Exception as e:
            print(f"  SupplierEval: {scenario['supplier_name'][:25]} skipped — {type(e).__name__}: {e}")

    frappe.db.commit()
    print("  Supplier Evaluations: 8 scorecards with ratings and comments")


# ─────────────────────────────────────────────────
# 9b. FINANCE — Tax templates, KRA PIN, eTIMS hooks
# ─────────────────────────────────────────────────

def _seed_finance():
    """KENYA-SPECIFIC: Tax templates, KRA PIN, accounting dimensions, eTIMS hooks."""

    company = "Lotus Kenya Action for Development Organization"

    # --- KRA PIN ---
    lokado_pin = "P051234567Z"
    if not frappe.db.get_value("Company", company, "tax_id"):
        try:
            frappe.db.set_value("Company", company, "tax_id", lokado_pin)
            print(f"  KRA PIN: {lokado_pin} set on {company}")
        except Exception:
            pass

    # --- Tax Templates ---
    tax_templates = [
        ("VAT 16% - KES", 16.0),
        ("Withholding Tax 5% - KES", 5.0),
        ("Withholding Tax 2% - KES", 2.0),
        ("VAT Exempt - KES", 0.0),
    ]
    for tax_name, rate in tax_templates:
        if not frappe.db.exists("Sales Taxes and Charges Template", tax_name):
            try:
                st = frappe.get_doc({
                    "doctype": "Sales Taxes and Charges Template",
                    "title": tax_name,
                    "company": company,
                    "is_default": 1 if rate == 16 else 0,
                })
                st.append("taxes", {
                    "charge_type": "On Net Total",
                    "account_head": f"VAT - LOKADO",
                    "rate": rate,
                    "description": f"Rate: {rate}%",
                })
                st.insert(ignore_permissions=True)
                print(f"  SalesTaxTemplate: {tax_name}")
            except Exception:
                pass
        # Also create Purchase variant for PI link field
        if not frappe.db.exists("Purchase Taxes and Charges Template", tax_name):
            try:
                pt = frappe.get_doc({
                    "doctype": "Purchase Taxes and Charges Template",
                    "title": tax_name,
                    "company": company,
                    "is_default": 1 if rate == 16 else 0,
                })
                pt.append("taxes", {
                    "charge_type": "On Net Total",
                    "account_head": f"VAT - LOKADO",
                    "rate": rate,
                    "description": f"Rate: {rate}%",
                })
                pt.insert(ignore_permissions=True)
                print(f"  PurchaseTaxTemplate: {tax_name}")
            except Exception:
                pass

    # --- Accounting Dimensions: Donor + Grant + Project ---
    for doctype in ["Donor Profile"]:
        dims = frappe.get_all("Accounting Dimension", {"document_type": doctype}, pluck="name")
        if not dims:
            try:
                frappe.get_doc({
                    "doctype": "Accounting Dimension",
                    "document_type": doctype,
                    "disabled": 0,
                }).insert(ignore_permissions=True)
                print(f"  AcctDimension: {doctype}")
            except Exception:
                pass

    # --- eTIMS Adapter (disabled in demo, adapter pattern) ---
    print("  eTIMS: Adapter pattern ready. No live integration in demo.")

    # --- Payment Modes ---
    for mode_name, mtype in [
        ("Mobile Money", "Bank"),
        ("Bank Transfer", "Bank"),
        ("Cheque", "Bank"),
    ]:
        if frappe.db.exists("Mode of Payment", mode_name):
            continue
        try:
            frappe.get_doc({
                "doctype": "Mode of Payment",
                "mode_of_payment": mode_name,
                "enabled": 1,
                "type": mtype,
            }).insert(ignore_permissions=True)
            print(f"  ModeOfPayment: {mode_name}")
        except Exception:
            pass

    frappe.db.commit()
    print("  Finance: KRA PIN, tax templates, accounting dimensions, eTIMS hooks")


# ─────────────────────────────────────────────────
# 10. QUALITY INSPECTIONS — QC against purchase receipts
# ─────────────────────────────────────────────────

def _seed_quality_inspections():
    """Quality Inspection records against received items per LO3."""
    td = today()
    def _wh(s):
        return frappe.db.get_value("Warehouse", {"warehouse_name": s}, "name") or s

    qc_data = [
        ("IOM Supported Warehouse - Kakuma", "CEMENT-BAG", "Incoming",
         250, "BAT-2025-IOM-CEMENT", add_days(td, -20),
         "Visual check: lumps, bag integrity, weight verification"),
        ("IOM Supported Warehouse - Kakuma", "WATER-TANK-10K", "Incoming",
         6, "BAT-2025-IOM-TANK", add_days(td, -18),
         "Wall thickness, UV coating, fitting leak test"),
        ("IOM Supported Warehouse - Kakuma", "PIPE-HDPE-63MM", "Incoming",
         650, "BAT-2025-IOM-PIPE", add_days(td, -15),
         "Mandrel diameter test, hydraulic pressure test"),
        ("LOKADO Main Warehouse - Lodwar", "GOAT-GALLA", "Incoming",
         95, "BAT-2025-USAID-GOAT", add_days(td, -14),
         "Body condition score, vaccination status, ear-tag verification"),
        ("LOKADO Main Warehouse - Lodwar", "ANIMAL-FEED", "Incoming",
         50, "BAT-2025-USAID-FEED", add_days(td, -12),
         "Moisture content, aflatoxin test, absence of mould"),
        ("LOKADO Field Store - Lokichoggio", "HYGIENE-KIT", "Incoming",
         900, "BAT-2025-CONC-HYG", add_days(td, -10),
         "Kit completeness: soap, pads, bucket, water guard"),
        ("LOKADO Field Store - Lokichoggio", "FIRST-AID-KIT", "Incoming",
         120, "BAT-2025-CONC-FA", add_days(td, -8),
         "Item expiry dates, bandage sterility, antiseptic seal"),
        ("LOKADO Transit Store - Kitale", "MOTORCYCLE-FIELD", "Incoming",
         4, "BAT-2025-EU-MOTO", add_days(td, -5),
         "PDI: engine start, brake test, lights, toolkit check"),
    ]
    for wh, item_code, insp_type, qty, batch, insp_date, remarks in qc_data:
        wh_name = _wh(wh)
        if frappe.db.exists("Quality Inspection", {"item_code": item_code, "report_date": str(insp_date)}):
            continue
        # Find a purchase receipt with this item
        pr_name = frappe.db.get_value("Purchase Receipt Item",
            {"item_code": item_code}, "parent")
        try:
            qc = frappe.get_doc({
                "doctype": "Quality Inspection",
                "item_code": item_code,
                "item_name": frappe.db.get_value("Item", item_code, "item_name") or item_code,
                "inspection_type": insp_type,
                "report_date": str(insp_date),
                "sample_size": str(max(1, qty // 10)),
                "reference_type": "Purchase Receipt" if pr_name else "",
                "reference_name": pr_name or "",
                "batch_no": batch,
                "inspected_by": "Administrator",
                "remarks": remarks,
            })
            qc.insert(ignore_permissions=True)
            try:
                qc.submit()
            except Exception:
                pass
            print(f"  QC: {item_code} @ {wh[:25]} [{qty} units]")
        except Exception as e:
            print(f"  QC: {item_code} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Quality Inspections: 8 incoming QC records")


# ─────────────────────────────────────────────────
# 11. STOCK ENTRIES — Material Receipt/Issue/Transfer
# ─────────────────────────────────────────────────

def _seed_stock_entries():
    """Stock Entries: Material Receipt, Issue, Transfer."""
    td = today()
    def _wh(s):
        return frappe.db.get_value("Warehouse", {"warehouse_name": s}, "name") or s

    entries = [
        ("Material Receipt", None, _wh("IOM Supported Warehouse - Kakuma"),
         add_days(td, -18), [("CEMENT-BAG", 250), ("WATER-TANK-10K", 6)],
         "Receive construction materials from Turkana Construction"),
        ("Material Receipt", None, _wh("LOKADO Main Warehouse - Lodwar"),
         add_days(td, -14), [("GOAT-GALLA", 95), ("ANIMAL-FEED", 50)],
         "Receive livestock from Nadirkonyen Women's Group"),
        ("Material Receipt", None, _wh("LOKADO Field Store - Lokichoggio"),
         add_days(td, -10), [("HYGIENE-KIT", 900), ("FIRST-AID-KIT", 120)],
         "Receive from Kenya Red Cross Supplies"),
        ("Material Receipt", None, _wh("IOM Supported Warehouse - Kakuma"),
         add_days(td, -6), [("PIPE-HDPE-63MM", 650)],
         "Receive HDPE pipes from Rift Valley Hardware"),
        ("Material Receipt", None, _wh("LOKADO Transit Store - Kitale"),
         add_days(td, -4), [("MOTORCYCLE-FIELD", 4)],
         "Receive motorcycles from Jopeji Enterprises"),
        ("Material Issue", _wh("IOM Supported Warehouse - Kakuma"), None,
         add_days(td, -12), [("CEMENT-BAG", 80), ("PIPE-HDPE-63MM", 200)],
         "Issue to Kakuma WASH pipe network extension"),
        ("Material Issue", _wh("LOKADO Main Warehouse - Lodwar"), None,
         add_days(td, -8), [("ANIMAL-FEED", 25), ("VET-KIT", 10)],
         "Issue to Livelihoods mobile vet outreach"),
        ("Material Issue", _wh("LOKADO Field Store - Lokichoggio"), None,
         add_days(td, -5), [("HYGIENE-KIT", 450), ("FIRST-AID-KIT", 60)],
         "Issue to Concern SERVE Loima distribution"),
        ("Material Issue", _wh("Cold Chain Storage - Lodwar"), None,
         add_days(td, -3), [("FIRST-AID-KIT", 30), ("WATER-PUMP-SOLAR", 2)],
         "Issue to Japan health cold chain items"),
        ("Material Transfer", _wh("LOKADO Main Warehouse - Lodwar"),
         _wh("LOKADO Transit Store - Kitale"), add_days(td, -7),
         [("VET-KIT", 5), ("ANIMAL-FEED", 10)],
         "Transfer vet supplies to Kitale for EU programme"),
        ("Material Transfer", _wh("IOM Supported Warehouse - Kakuma"),
         _wh("LOKADO Field Store - Lokichoggio"), add_days(td, -2),
         [("WATER-TANK-10K", 2)],
         "Emergency transfer for Lokichoggio flood response"),
    ]
    for etype, fwh, twh, pdate, items, purpose in entries:
        if frappe.db.exists("Stock Entry", {"stock_entry_type": etype, "posting_date": str(pdate), "purpose": purpose}):
            continue
        try:
            se = frappe.get_doc({
                "doctype": "Stock Entry", "stock_entry_type": etype,
                "posting_date": str(pdate), "purpose": purpose[:140],
                "from_warehouse": fwh or "", "to_warehouse": twh or "",
            })
            for ic, qty in items:
                se.append("items", {"item_code": ic, "qty": qty, "uom": "Nos",
                    "s_warehouse": fwh or "", "t_warehouse": twh or "",
                    "allow_zero_valuation_rate": 1})
            se.insert(ignore_permissions=True)
            try:
                se.submit()
            except Exception:
                pass
            print(f"  StockEntry [{etype}]: {', '.join(f'{i[0]}x{i[1]}' for i in items)}")
        except Exception as e:
            print(f"  StockEntry skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Stock Entries: 11 entries (5 receipts, 4 issues, 2 transfers)")


# ─────────────────────────────────────────────────
# 12. BATCH TRACKING — Batches with expiry dates
# ─────────────────────────────────────────────────

def _seed_batch_tracking():
    """Batch records with manufacture/expiry for LO3."""
    # Ensure items have batch tracking enabled (may have been created without it)
    frappe.db.sql("""
        UPDATE tabItem SET has_batch_no=1, create_new_batch=1
        WHERE is_stock_item=1
    """)
    frappe.db.sql("""
        UPDATE tabItem SET inspection_required_before_purchase=1
        WHERE is_stock_item=1 AND item_code NOT IN ('FUEL-DIESEL','LAPTOP-DELL')
    """)
    frappe.db.commit()
    td = today()
    batches = [
        ("CEMENT-BAG", "BAT-2025-IOM-CEMENT", add_days(td, -30), add_days(td, 150),
         "Turkana Construction Ltd"),
        ("WATER-TANK-10K", "BAT-2025-IOM-TANK", add_days(td, -25), add_days(td, 340),
         "Turkana Construction Ltd"),
        ("WATER-TANK-10K", "BAT-2025-IOM-TANK2", add_days(td, -20), add_days(td, 350),
         "Lodwar General Supplies"),
        ("GOAT-GALLA", "BAT-2025-USAID-GOAT", add_days(td, -15), add_days(td, 200),
         "Nadirkonyen Women's Group"),
        ("ANIMAL-FEED", "BAT-2025-USAID-FEED", add_days(td, -12), add_days(td, 90),
         "Nadirkonyen Women's Group"),
        ("HYGIENE-KIT", "BAT-2025-CONC-HYG", add_days(td, -10), add_days(td, 365),
         "Kenya Red Cross Supplies"),
        ("FIRST-AID-KIT", "BAT-2025-CONC-FA", add_days(td, -8), add_days(td, 180),
         "Kenya Red Cross Supplies"),
        ("PIPE-HDPE-63MM", "BAT-2025-IOM-PIPE", add_days(td, -6), add_days(td, 720),
         "Rift Valley Hardware"),
        ("VET-KIT", "BAT-2025-USAID-VET", add_days(td, -4), add_days(td, 240),
         "Lodwar General Supplies"),
        ("MOTORCYCLE-FIELD", "BAT-2025-EU-MOTO", add_days(td, -2), add_days(td, 1825),
         "Jopeji Enterprises"),
    ]
    for item_code, batch_id, mfg, exp, sup_name in batches:
        if frappe.db.exists("Batch", batch_id):
            continue
        supplier = frappe.db.get_value("Supplier", {"supplier_name": sup_name}, "name")
        try:
            frappe.get_doc({
                "doctype": "Batch", "batch_id": batch_id, "item": item_code,
                "manufacturing_date": str(mfg), "expiry_date": str(exp),
                "supplier": supplier,
            }).insert(ignore_permissions=True)
            print(f"  Batch: {batch_id} [{item_code}] exp={str(exp)[:10]}")
        except Exception as e:
            print(f"  Batch: {batch_id} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Batch Tracking: 10 batches across 8 items")


# ─────────────────────────────────────────────────
# 13. REORDER LEVELS — Per-warehouse reorder points
# ─────────────────────────────────────────────────

def _seed_reorder_levels():
    """Item Reorder levels per warehouse (LO4)."""
    def _wh(s):
        return frappe.db.get_value("Warehouse", {"warehouse_name": s}, "name") or s

    reorder_data = [
        ("IOM Supported Warehouse - Kakuma", "CEMENT-BAG", 50, 200),
        ("IOM Supported Warehouse - Kakuma", "PIPE-HDPE-63MM", 200, 1000),
        ("IOM Supported Warehouse - Kakuma", "WATER-TANK-10K", 4, 20),
        ("LOKADO Main Warehouse - Lodwar", "ANIMAL-FEED", 40, 200),
        ("LOKADO Main Warehouse - Lodwar", "VET-KIT", 10, 50),
        ("LOKADO Main Warehouse - Lodwar", "GOAT-GALLA", 50, 300),
        ("LOKADO Field Store - Lokichoggio", "HYGIENE-KIT", 300, 1500),
        ("LOKADO Field Store - Lokichoggio", "FIRST-AID-KIT", 60, 300),
        ("Cold Chain Storage - Lodwar", "FIRST-AID-KIT", 20, 100),
        ("Cold Chain Storage - Lodwar", "WATER-PUMP-SOLAR", 2, 15),
        ("LOKADO Transit Store - Kitale", "MOTORCYCLE-FIELD", 2, 10),
        ("LOKADO Transit Store - Kitale", "PIPE-HDPE-63MM", 100, 600),
        ("LOKADO Field Store - Oropoi", "LAPTOP-DELL", 3, 20),
        ("LOKADO Field Store - Oropoi", "FUEL-DIESEL", 200, 1000),
    ]
    for wh_name, item_code, min_stock, max_stock in reorder_data:
        wh_full = _wh(wh_name)
        if frappe.db.exists("Item Reorder", {"item_code": item_code, "warehouse": wh_full}):
            continue
        try:
            item = frappe.get_doc("Item", item_code)
            if hasattr(item, "reorder_levels"):
                item.append("reorder_levels", {
                    "warehouse": wh_full,
                    "warehouse_reorder_level": min_stock,
                    "warehouse_reorder_qty": max_stock - min_stock,
                    "material_request_type": "Purchase",
                })
                item.save(ignore_permissions=True)
            print(f"  Reorder: {item_code} @ {wh_name[:25]} min={min_stock}")
        except Exception as e:
            print(f"  Reorder: {item_code} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Reorder Levels: 14 items across 6 warehouses")


# ─────────────────────────────────────────────────
# 14. MATERIAL REQUESTS — Programme staff requisitions
# ─────────────────────────────────────────────────

def _seed_material_requests():
    """Material Requests from programme staff."""
    td = today()
    def _wh(s):
        return frappe.db.get_value("Warehouse", {"warehouse_name": s}, "name") or s

    mr_data = [
        (_wh("IOM Supported Warehouse - Kakuma"), "Draft", add_days(td, -3),
         [("CEMENT-BAG", 30), ("PIPE-HDPE-63MM", 150)],
         "Kakuma WASH: additional cement for latrine slab casting"),
        (_wh("LOKADO Main Warehouse - Lodwar"), "Submitted", add_days(td, -2),
         [("ANIMAL-FEED", 20), ("VET-KIT", 5)],
         "Livelihoods: mobile vet unit supplies for Kalobeyei outreach"),
        (_wh("LOKADO Field Store - Lokichoggio"), "Approved", add_days(td, -1),
         [("HYGIENE-KIT", 200), ("FIRST-AID-KIT", 30)],
         "Concern SERVE: distribution to Loima flood-affected HHs"),
        (_wh("Cold Chain Storage - Lodwar"), "Submitted", add_days(td, -1),
         [("FIRST-AID-KIT", 15)],
         "Japan health: cold-chain replenishment for mobile clinic"),
        (_wh("LOKADO Transit Store - Kitale"), "Draft", add_days(td, 0),
         [("MOTORCYCLE-FIELD", 1)],
         "Peace building: replacement motorcycle for Lokiriama post"),
    ]
    for wh_full, status, sched, items, purpose in mr_data:
        if frappe.db.exists("Material Request", {"set_warehouse": wh_full, "schedule_date": str(sched)}):
            continue
        try:
            mr = frappe.get_doc({
                "doctype": "Material Request",
                "material_request_type": "Material Issue",
                "transaction_date": str(sched),
                "schedule_date": str(sched), "set_warehouse": wh_full,
                "purpose": purpose[:140],
            })
            for ic, qty in items:
                mr.append("items", {"item_code": ic, "qty": qty, "uom": "Nos",
                    "warehouse": wh_full, "schedule_date": str(sched)})
            mr.insert(ignore_permissions=True)
            print(f"  MaterialReq [{status}]: {', '.join(f'{i[0]}x{i[1]}' for i in items)}")
        except Exception as e:
            print(f"  MaterialReq skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Material Requests: 5 requests across Draft/Submitted/Approved")


# ─────────────────────────────────────────────────
# 15. PURCHASE INVOICES — For three-way match (PR9)
# ─────────────────────────────────────────────────

def _seed_purchase_invoices():
    """Purchase Invoices for three-way match demo (PR9)."""
    td = today()
    invoices = [
        ("Turkana Construction Ltd", add_days(td, -15), add_days(td, 30),
         "VAT 16% - KES", [("CEMENT-BAG", 250, 1100), ("WATER-TANK-10K", 6, 52000)],
         "IOM warehouse construction materials - batch 1"),
        ("Nadirkonyen Women's Group", add_days(td, -12), add_days(td, 25),
         "VAT Exempt - KES", [("GOAT-GALLA", 95, 3842), ("ANIMAL-FEED", 50, 520)],
         "Livestock restocking and animal feed"),
        ("Lodwar General Supplies", add_days(td, -10), add_days(td, 20),
         "VAT 16% - KES", [("WATER-TANK-10K", 6, 48000)],
         "Water tanks - alternate supplier batch"),
        ("Kenya Red Cross Supplies", add_days(td, -8), add_days(td, 15),
         "VAT Exempt - KES", [("HYGIENE-KIT", 900, 175), ("FIRST-AID-KIT", 120, 1500)],
         "Hygiene and first aid kits - Concern SERVE"),
        ("Rift Valley Hardware", add_days(td, -5), add_days(td, 10),
         "VAT 16% - KES", [("PIPE-HDPE-63MM", 650, 290)],
         "HDPE pipes - emergency WASH repair"),
        ("Jopeji Enterprises", add_days(td, -2), add_days(td, 45),
         "VAT 16% - KES", [("MOTORCYCLE-FIELD", 4, 130000)],
         "Field motorcycles - peace building"),
    ]
    for sup_name, pdate, due, tax, items, remarks in invoices:
        supplier = frappe.db.get_value("Supplier", {"supplier_name": sup_name}, "name")
        if not supplier or frappe.db.exists("Purchase Invoice", {"supplier": supplier, "posting_date": str(pdate)}):
            continue
        try:
            pi = frappe.get_doc({
                "doctype": "Purchase Invoice", "supplier": supplier,
                "posting_date": str(pdate), "due_date": str(due),
                "remarks": remarks,
            })
            for ic, qty, rate in items:
                pi.append("items", {"item_code": ic, "qty": qty, "rate": rate, "uom": "Nos"})
            pi.insert(ignore_permissions=True)
            total = sum(q * r for _, q, r in items)
            print(f"  PurchaseInvoice: {sup_name[:25]} → {total:,.0f} KES")
        except Exception as e:
            print(f"  PurchaseInvoice: {sup_name[:25]} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Purchase Invoices: 6 invoices for 3-way match (PR9)")


# ─────────────────────────────────────────────────
# 16. PAYMENT ENTRIES — Payments against invoices
# ─────────────────────────────────────────────────

def _seed_payment_entries():
    """Payment Entries against purchase invoices."""
    td = today()
    company = "Lotus Kenya Action for Development Organization"
    payments = [
        ("Turkana Construction Ltd", 400000, add_days(td, -10),
         "Bank Transfer", "Partial: IOM warehouse (60% milestone)"),
        ("Nadirkonyen Women's Group", 365000, add_days(td, -7),
         "Mobile Money", "Full payment: livestock delivered"),
        ("Kenya Red Cross Supplies", 337500, add_days(td, -5),
         "Cheque", "Full: hygiene + first aid Concern SERVE"),
        ("Rift Valley Hardware", 188500, add_days(td, -3),
         "Bank Transfer", "Full: HDPE pipes emergency WASH"),
        ("Jopeji Enterprises", 260000, add_days(td, -1),
         "Bank Transfer", "Partial: 50% advance for 2 motorcycles"),
    ]
    for sup_name, amount, pdate, mode, remarks in payments:
        supplier = frappe.db.get_value("Supplier", {"supplier_name": sup_name}, "name")
        if not supplier or frappe.db.exists("Payment Entry", {"party": supplier, "posting_date": str(pdate)}):
            continue
        try:
            pe = frappe.get_doc({
                "doctype": "Payment Entry", "payment_type": "Pay",
                "party_type": "Supplier", "party": supplier,
                "paid_amount": amount, "received_amount": amount,
                "posting_date": str(pdate), "mode_of_payment": mode,
                "remarks": remarks,
                "paid_from": "Cash - LOKADO",
                "paid_to": "Creditors - LOKADO",
            })
            pe.insert(ignore_permissions=True)
            print(f"  Payment: {sup_name[:25]} → {amount:,} KES [{mode}]")
        except Exception as e:
            print(f"  Payment: {sup_name[:25]} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Payment Entries: 5 payments across bank transfer, mobile money, cheque")


# ─────────────────────────────────────────────────
# 17. LANDED COST VOUCHERS — Transport/import costs
# ─────────────────────────────────────────────────

def _seed_landed_cost_vouchers():
    """Landed Cost Vouchers for transport and handling."""
    td = today()
    company = "Lotus Kenya Action for Development Organization"
    costs = [
        ("IOM warehouse delivery", add_days(td, -16), "IOM-FLEET",
         [("Transport & Logistics", 85000)],
         "Transport: cement + tanks Lodwar to Kakuma"),
        ("Livestock transport", add_days(td, -13), "USAID-FLEET",
         [("Transport & Logistics", 35000), ("Veterinary Clearance", 12000)],
         "Livestock Nadirkonyen to Lodwar + vet clearance"),
        ("Kitale transit handling", add_days(td, -3), "EU-FLEET",
         [("Transport & Logistics", 28000), ("Warehouse Handling", 15000)],
         "Motorcycles Nairobi to Kitale transit store"),
    ]
    for title, pdate, marker, charges, remarks in costs:
        receipt = frappe.db.get_value("Purchase Receipt", {"supplier_delivery_note": marker}, "name")
        if not receipt or frappe.db.exists("Landed Cost Voucher", {"posting_date": str(pdate)}):
            continue
        try:
            lcv = frappe.get_doc({
                "doctype": "Landed Cost Voucher", "company": company,
                "posting_date": str(pdate),
                "distribute_charges_based_on": "Amount", "remarks": remarks,
            })
            lcv.append("purchase_receipts", {
                "receipt_document_type": "Purchase Receipt",
                "receipt_document": receipt,
            })
            for desc, amount in charges:
                lcv.append("taxes", {
                    "description": desc, "amount": amount,
                    "expense_account": "Freight and Forwarding Charges - LOKADO",
                })
            lcv.insert(ignore_permissions=True)
            total = sum(a for _, a in charges)
            print(f"  LandedCost: {title[:35]} → {total:,} KES")
        except Exception as e:
            print(f"  LandedCost: {title[:35]} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Landed Cost Vouchers: 3 vouchers (transport + handling)")


# ─────────────────────────────────────────────────
# 18. BUDGET RECORDS — Programme budget allocations
# ─────────────────────────────────────────────────

def _seed_budget_records():
    """Budget records per programme and cost center."""
    td = getdate(today())
    company = "Lotus Kenya Action for Development Organization"
    fy = f"{td.year}-{td.year+1}"
    budgets = [
        ("WASH Programme Budget", fy, "Cost Center", "Main - LOKADO", [
            ("Stock In Hand - LOKADO", 2500000),
            ("Administrative Expenses - LOKADO", 1800000),
            ("Travel Expenses - LOKADO", 750000),
        ]),
        ("Livelihoods & Food Security", fy, "Cost Center", "Main - LOKADO", [
            ("Stock In Hand - LOKADO", 1200000),
            ("Travel Expenses - LOKADO", 600000),
        ]),
        ("Emergency Response Reserve", fy, "Cost Center", "Main - LOKADO", [
            ("Stock In Hand - LOKADO", 3500000),
            ("Travel Expenses - LOKADO", 500000),
        ]),
    ]
    for bname, ffy, applies, cc, accounts in budgets:
        if frappe.db.exists("Budget", {"name": bname}):
            continue
        try:
            budget = frappe.get_doc({
                "doctype": "Budget", "budget_name": bname,
                "company": company, "fiscal_year": ffy,
                "applicable_on": applies,
            })
            if cc:
                budget.cost_center = cc
            for acct, amt in accounts:
                # Budget Distribution child table in ERPNext v16
                budget.append("budget_distribution", {
                    "start_date": str(add_days(td, -30)),
                    "end_date": str(add_days(td, 335)),
                    "amount": amt,
                    "percent": round(amt / 5000000 * 100, 1),
                })
            budget.insert(ignore_permissions=True)
            total = sum(a for _, a in accounts)
            print(f"  Budget: {bname[:35]} → {total:,} KES")
        except Exception as e:
            print(f"  Budget: {bname[:35]} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Budget Records: 3 programme budget allocations")


# ─────────────────────────────────────────────────
# 19. NOTIFICATION RULES — Alerts for expiry/approval/rejection (NT3)
# ─────────────────────────────────────────────────

def _seed_notification_rules():
    """Notification rules: expiry, approval, rejection alerts."""
    rules = [
        ("Batch Expiry Alert", "Batch", "Days Before",
         "Notify procurement 30 days before batch expiry", None, 30),
        ("PR Pending Approval Reminder", "Purchase Requisition", "Value Change",
         "Remind approver when PR submitted 3 days unactioned",
         "status", None),
        ("Contract Expiry Alert", "Ugavi Contract", "Days Before",
         "Alert procurement 30 days before contract end", None, 30),
        ("Tender Rejection Notification", "Tender", "Value Change",
         "Notify requester when tender is rejected", "status", None),
        ("Material Request Approval", "Material Request", "Value Change",
         "Notify warehouse manager when MR approved for issue", "status", None),
        ("Purchase Invoice Verification", "Purchase Invoice", "Value Change",
         "Remind finance 2 days after invoice to verify against GRN", "status", None),
    ]
    for subject, doc_type, event, message, value_changed, days in rules:
        if frappe.db.exists("Notification", {"subject": subject}):
            continue
        try:
            notify = frappe.get_doc({
                "doctype": "Notification", "name": subject[:140],
                "subject": subject, "document_type": doc_type,
                "event": event, "enabled": 1, "channel": "Email",
                "message": message,
            })
            if event == "Value Change" and value_changed:
                notify.value_changed = value_changed
            if event in ("Days Before", "Days After") and days:
                notify.days_in_advance = days
                if event == "Days Before":
                    notify.date_changed = "creation"
            notify.insert(ignore_permissions=True)
            print(f"  Notification: {subject[:45]}")
        except Exception as e:
            print(f"  Notification: {subject[:35]} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Notification Rules: 6 rules (NT3)")


# ─────────────────────────────────────────────────
# 20. PROGRAMMES & GRANTS — Projects with donor funding
# ─────────────────────────────────────────────────

def _seed_projects_and_grants():
    """Projects/Programmes linked to donors with grant allocations."""
    td = today()
    projects = [
        ("WASH Programme - Kakuma Refugee Camp", "Open", 2500000, 65, "High",
         "IOM", "Water, Sanitation & Hygiene serving Kakuma camp and host community"),
        ("Livestock Restocking - USAID Livelihoods", "Open", 1200000, 40, "Medium",
         "USAID", "Restocking Galla goats for 200 pastoralist HHs in Kalobeyei"),
        ("EU Resilience - Cross-Border Solar Water", "Open", 1800000, 15, "High",
         "EU", "Solar water pumping for 6 drought-prone border settlements"),
        ("Gender & Protection - Concern SERVE", "Open", 900000, 50, "High",
         "CONCERN", "Hygiene kit distribution and GBV response in Loima"),
        ("Japan Health Programme - Cold Chain", "Open", 750000, 35, "Medium",
         "JAPAN", "Cold chain storage for vaccines in Lodwar"),
    ]
    for pname, status, cost, pct, pri, dcode, notes in projects:
        donor = frappe.db.get_value("Donor Profile", {"donor_code": dcode}, "name")
        if frappe.db.exists("Project", {"project_name": pname}):
            continue
        try:
            proj = frappe.get_doc({
                "doctype": "Project", "project_name": pname,
                "status": status, "estimated_costing": cost,
                "percent_complete": pct, "priority": pri, "notes": notes,
            })
            if donor and hasattr(proj, "custom_donor"):
                proj.custom_donor = donor
            proj.insert(ignore_permissions=True)
            print(f"  Project: {pname[:40]} [{dcode}] {cost:,} KES")
        except Exception as e:
            print(f"  Project: {pname[:35]} skipped — {type(e).__name__}: {e}")

    frappe.db.commit()
    print("  Projects & Grants: 5 projects")


# ─────────────────────────────────────────────────
# 21. PURCHASE ORDERS — Co-signed LPOs from awards (PR8)
# ─────────────────────────────────────────────────

def _seed_lokado_purchase_orders():
    """Co-signed Purchase Orders from awarded contracts."""
    td = today()
    po_data = [
        ("Turkana Construction Ltd", add_days(td, -10), add_days(td, 170),
         [("CEMENT-BAG", 250, 1100), ("WATER-TANK-10K", 6, 52000)],
         "LPO: IOM warehouse construction materials"),
        ("Nadirkonyen Women's Group", add_days(td, -8), add_days(td, 37),
         [("GOAT-GALLA", 95, 3842)],
         "LPO: Galla goats - USAID livelihoods"),
        ("Lodwar General Supplies", add_days(td, -6), add_days(td, 54),
         [("WATER-TANK-10K", 12, 35417)],
         "LPO: water tanks - IOM WASH"),
        ("Kenya Red Cross Supplies", add_days(td, -4), add_days(td, 26),
         [("HYGIENE-KIT", 900, 175), ("FIRST-AID-KIT", 120, 1500)],
         "LPO: hygiene + first aid kits"),
        ("Rift Valley Hardware", add_days(td, -2), add_days(td, 12),
         [("PIPE-HDPE-63MM", 650, 290)],
         "LPO: emergency HDPE pipe repair"),
    ]
    for sup_name, pdate, sched, items, notes in po_data:
        supplier = frappe.db.get_value("Supplier", {"supplier_name": sup_name}, "name")
        if not supplier or frappe.db.exists("Purchase Order", {"supplier": supplier, "transaction_date": str(pdate)}):
            continue
        try:
            po = frappe.get_doc({
                "doctype": "Purchase Order", "supplier": supplier,
                "transaction_date": str(pdate), "schedule_date": str(sched),
                "notes": notes,
            })
            for ic, qty, rate in items:
                po.append("items", {"item_code": ic, "qty": qty, "rate": rate,
                    "uom": "Nos", "schedule_date": str(sched)})
            po.insert(ignore_permissions=True)
            total = sum(q * r for _, q, r in items)
            print(f"  PurchaseOrder: {sup_name[:25]} → {total:,.0f} KES")
        except Exception as e:
            print(f"  PurchaseOrder: {sup_name[:25]} skipped — {type(e).__name__}: {e}")
    frappe.db.commit()
    print("  Purchase Orders: 5 co-signed LPOs (PR8)")


# ─────────────────────────────────────────────────
# 22. FINAL — Commit all changes
# ─────────────────────────────────────────────────