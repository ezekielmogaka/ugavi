"""Schema-driven, idempotent demo seed for LOKADO (Lotus Kenya Action for Development Organization).

Validates schema-driven master defaults against DocType meta at runtime.
Refuses to run on production sites (developer_mode=0).
Run twice -- no duplicates, no errors.

Usage:
    make seed-lokado
    bench execute ugavi.scripts.seed_lokado.run
"""

from contextlib import contextmanager
import json

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today
from frappe.utils.password import update_password

_STRICT_FIELDS = True  # set False in tests to skip meta queries
_DEMO_PASSWORD = "Ugavi@2024"


@contextmanager
def _demo_actor(user):
    previous = frappe.session.user
    frappe.set_user(user)
    try:
        yield
    finally:
        frappe.set_user(previous)


def _progress_demo_requisition(pr, target_status):
    if target_status == "Draft" or pr.status in ("Approved", "Rejected", "Converted to Tender"):
        return
    with _demo_actor(pr.requester):
        if pr.status == "Draft":
            pr.submit_for_approval()
    if target_status == "Pending Approval":
        return
    actors = {
        "Approver Level 1": "approver1@lokado.org",
        "Approver Level 2": "approver2@lokado.org",
        "Procurement Officer": "procurement@lokado.org",
        "Finance Officer": "finance@lokado.org",
    }
    while pr.status == "Pending Approval":
        history = json.loads(pr.approval_history or "[]")
        done = {row["role"] for row in history if row["action"] == "Approved"}
        step = next(row for row in pr._approval_steps() if row["role"] not in done)
        actor = step.get("user") or actors[step["role"]]
        with _demo_actor(actor):
            if target_status == "Rejected":
                pr.reject("DEMO: request requires revised beneficiary or budget evidence.")
            else:
                pr.approve("DEMO: programme need, donor and quantities verified.")


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
    meta = frappe.get_meta(dt)
    valid = {f.fieldname for f in meta.fields} | {"doctype", "name"}
    bad = [k for k in data if k not in valid and not k.startswith("__")]
    if bad:
        frappe.throw(f"{dt}: unrecognized seed fields {bad}")
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
    _seed_demo_mail_relay()        # opening codes and notices land in Mailpit
    _seed_roles_and_users()
    _seed_donors()
    _seed_items_and_warehouses()   # creates Item Groups that suppliers need
    _seed_suppliers()
    _seed_supplier_portal_links()
    _seed_additional_supplier_categories()
    _seed_procurement_settings()
    _seed_finance()
    _seed_logistics()
    _seed_supplier_evaluations()   # post-receipt supplier scorecards
    _seed_fleet()
    _seed_assets()
    _seed_governance()            # DoA, waiver, SoD, audit log, delegation
    _seed_projects_and_grants()
    _seed_procurement_workflow()  # governed requests, source-linked tenders, submitted bids
    _prepare_live_opening_demo()
    _seed_evaluation_journeys()   # real opening -> COI -> scores -> minutes -> recommendation

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

    # ── Procurement Depth ──
    _seed_monthly_stock_reports()  # derive donor books after all stock/valuation postings

    frappe.db.commit()
    from ugavi.scripts.check_lokado_demo import run as check_demo

    check_demo()
    print("\n=== LOKADO demo seed complete ===")
# ─────────────────────────────────────────────────
# 1. FOUNDATION — LOKADO Company
# ─────────────────────────────────────────────────

DEMO_MAIL_ACCOUNT = "LOKADO Demo Mailpit"


def _seed_demo_mail_relay():
    """Route outgoing demo mail to the local Mailpit relay (developer sites only)."""
    if frappe.db.exists("Email Account", DEMO_MAIL_ACCOUNT):
        return
    if frappe.db.exists("Email Account", {"default_outgoing": 1, "enable_outgoing": 1}):
        return  # respect an operator-configured outgoing account
    frappe.get_doc({
        "doctype": "Email Account",
        "email_account_name": DEMO_MAIL_ACCOUNT,
        "email_id": "procurement@lokado.org",
        "enable_incoming": 0,
        "enable_outgoing": 1,
        "default_outgoing": 1,
        "smtp_server": frappe.conf.get("demo_mail_relay", "mailpit"),
        "smtp_port": 1025,
        "use_tls": 0,
        "use_ssl_for_outgoing": 0,
        "no_smtp_authentication": 1,
        "awaiting_password": 0,
    }).insert(ignore_permissions=True)
    print(f"  Mail relay: {DEMO_MAIL_ACCOUNT} -> Mailpit (http://localhost:8026)")


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
    "Tender Committee Chair",
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
    ("chair@lokado.org",        "Grace",   "Lokwang",   "Tender Committee Chair"),
    ("evaluator@lokado.org",    "Samuel",  "Lomuria",   "Evaluation Committee"),
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

# Evaluation panel for sealed tenders; distinct from the three opening officers.
LOKADO_EVALUATION_COMMITTEE = (
    ("chair@lokado.org", "Chairperson"),
    ("committee@lokado.org", "Secretary"),
    ("evaluator@lokado.org", "Member"),
)

LOKADO_UPSTREAM_ROLES = {
    "chair@lokado.org": ("Evaluation Committee",),
    "procurement@lokado.org": ("Purchase User",),
    "logistics@lokado.org": ("Stock User",),
    "storekeeper@lokado.org": ("Stock User",),
    "finance@lokado.org": ("Accounts User",),
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
            user = frappe.get_doc("User", email)
            user.add_roles(*((role,) if role else ()), *LOKADO_UPSTREAM_ROLES.get(email, ()))
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
        for upstream_role in LOKADO_UPSTREAM_ROLES.get(email, ()):
            user.append("roles", {"role": upstream_role})
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
        created, donor = _ensure("Donor Profile", "donor_code", code, {
            "donor_name": name,
            "donor_code": code,
            "currency": "KES",
            "require_segregated_stock": 1,
            "require_segregated_assets": 1,
            "reporting_frequency": "Monthly",
        })
        if created:
            frappe.get_doc("Donor Profile", donor).add_comment("Comment", desc)
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
# ── New LOKADO suppliers for expanded demo ──
    ("Lodwar Pharmaceuticals Ltd", "Medical Supplies", "Prequalified",
     "Pharmaceutical distributor serving Turkana County health facilities. Licensed PPB wholesaler."),
    ("Turkana Women's Handicrafts Cooperative", "Shelter & NFI", "Prequalified",
     "Women-led cooperative producing blankets, dignity kits and household essentials."),
    ("Kakuma Stationers & Supplies", "Educational Supplies", "Prequalified",
     "School supplies, stationery and educational materials distributor in Kakuma."),
    ("Lake Turkana Fishermen's Cooperative", "Food Security", "Prequalified",
     "Community fishing cooperative supplying Lake Turkana catch and fishing equipment."),
    ("Lokitaung Hardware & Building", "Construction Materials", "Prequalified",
     "Hardware and building supplies based in Lokitaung, serving northern Turkana."),
    ("Nadapal Transport & Logistics", "Field Equipment", "Prequalified",
     "Cross-border transport and last-mile delivery specialist. Fleet of 12 trucks."),
    ("Kalobeyei Refugee Supplies Ltd", "Shelter & NFI", "Prequalified",
     "NFI and shelter material supplier for Kalobeyei Settlement humanitarian operations."),
    ("Kainuk Agro-Vet Supplies", "Livestock & Agriculture", "Prequalified",
     "Veterinary pharmaceuticals and animal health products for pastoralist communities."),
    ("Lokichar General Traders", "Office Supplies", "Prequalified",
     "General trader based in Lokichar, serving oil-field and adjacent communities."),
    ("Lorugum Welding & Fabrication", "Construction Materials", "Prequalified",
     "Metal fabrication workshop specializing in school desks, tanks and structural steel."),
    ("Oropoi Community Supplies", "WASH Supplies", "Suspended",
     "Suspended pending resolution of quality concerns on water treatment chemicals."),
    ("Eliye Springs Boat Services", "Food Security", "Expired",
     "Previously supplied fishing boats and gear. Insurance certification expired."),
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
    print("  30 LOKADO suppliers seeded (24 prequalified, 3 expired, 3 suspended) + 54 total in system")


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
        "Educational Supplies", "Shelter & NFI", "Food Security",
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
        # ── New items for expanded demo ──
        ("SURGICAL-GLOVES", "Surgical Gloves - Box 100", "Medical Supplies", "Nos"),
        ("MOSQUITO-NET", "Mosquito Net - Long-Lasting", "Medical Supplies", "Nos"),
        ("ORS-SACHET", "ORS Sachet - WHO Formula", "Medical Supplies", "Nos"),
        ("DELIVERY-KIT", "Delivery Kit - Clean Birth", "Medical Supplies", "Nos"),
        ("SCHOOL-DESK", "School Desk - 3-Seater", "Educational Supplies", "Nos"),
        ("TEXTBOOKS-SET", "Textbooks Set - Primary (40)", "Educational Supplies", "Nos"),
        ("STATIONERY-KIT", "Stationery Kit - Student", "Educational Supplies", "Nos"),
        ("SOLAR-LANTERN", "Solar Lantern - Classroom", "Educational Supplies", "Nos"),
        ("TARPAULIN-4X6", "Tarpaulin - 4m x 6m", "Shelter & NFI", "Nos"),
        ("BLANKET-FLEECE", "Blanket - Fleece Double", "Shelter & NFI", "Nos"),
        ("JERRY-CAN-20L", "Jerry Can - 20 Litre", "Shelter & NFI", "Nos"),
        ("COOKING-POT-SET", "Cooking Pot Set - Family", "Shelter & NFI", "Nos"),
        ("SORGHUM-SEEDS", "Sorghum Seeds - Certified (5kg)", "Food Security", "Bag"),
        ("FISHING-NET", "Fishing Net - Gill (100m)", "Food Security", "Nos"),
        ("TIMBER-POLE", "Timber Pole - Treated (4m)", "Construction Materials", "Nos"),
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
    print(f"  30 items, {len(warehouses)} warehouses created")
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
{
                "donor_code": "JAPAN",
                "warehouse_name": "Cold Chain Storage - Lodwar",
                "license_plate": "KDQ 520J",
                "make": "Nissan",
                "model": "Navara",
                "marker": "LOKADO-DEMO-FLEET-JAPAN",
                "destination": "Cold chain vaccine delivery route",
            },
            {
                "donor_code": "LOKADO-OWN",
                "warehouse_name": "LOKADO Field Store - Oropoi",
                "license_plate": "KDR 711L",
                "make": "Toyota",
                "model": "Hiace Van",
                "marker": "LOKADO-DEMO-FLEET-OWN",
                "destination": "Programme staff shuttle Lodwar-Kakuma",
            },
            {
                "donor_code": "USAID",
                "warehouse_name": "LOKADO Main Warehouse - Lodwar",
                "license_plate": "KDS 143U",
                "make": "Toyota",
                "model": "Land Cruiser 79 Pickup",
                "marker": "LOKADO-DEMO-FLEET-USAID2",
                "destination": "Livestock restocking logistics to Kalobeyei",
            },
            {
                "donor_code": "CONCERN",
                "warehouse_name": "LOKADO Field Store - Lokichoggio",
                "license_plate": "KDT 890C",
                "make": "Mitsubishi",
                "model": "Canter 3T",
                "marker": "LOKADO-DEMO-FLEET-CONCERN2",
                "destination": "NFI distribution to Loima and Kerio wards",
            },
        ],
    )
    print("  Fleet: 8 donor vehicles with submitted fuel, spares, trips and reports")


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
        ("EU Field Store - Lake Turkana", "EU"),
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
{
            "tag": "LOK-RADIO-001",
            "name": "HF Radio Base Station",
            "category": "IT Equipment",
            "serial": "HF-CON-001",
            "price": 325000,
            "donor": "CONCERN",
            "location": "LOKADO Field Store - Lokichoggio",
            "condition": "Good",
        },
        {
            "tag": "LOK-BOAT-001",
            "name": "Fishing Research Boat - Fibreglass",
            "category": "Equipment",
            "serial": "BOAT-EU-001",
            "price": 780000,
            "donor": "EU",
            "location": "LOKADO Transit Store - Kitale",
            "destination": "EU Field Store - Lake Turkana",
            "condition": "New",
        },
        {
            "tag": "LOK-WELD-001",
            "name": "Welding Machine - Portable ARC",
            "category": "Equipment",
            "serial": "WELD-USA-001",
            "price": 55000,
            "donor": "USAID",
            "location": "LOKADO Main Warehouse - Lodwar",
            "condition": "Fair",
        },
        {
            "tag": "LOK-SCALE-001",
            "name": "Livestock Weighing Scale - Electronic",
            "category": "Equipment",
            "serial": "SCALE-USA-001",
            "price": 92000,
            "donor": "USAID",
            "location": "LOKADO Main Warehouse - Lodwar",
            "destination": "USAID Field Store - Oropoi",
            "condition": "Good",
        },
        {
            "tag": "LOK-TABLET-001",
            "name": "Field Data Collection Tablet",
            "category": "IT Equipment",
            "serial": "TAB-IOM-001",
            "price": 62000,
            "donor": "IOM",
            "location": "IOM Supported Warehouse - Kakuma",
            "condition": "Good",
        },
        {
            "tag": "LOK-WTR-001",
            "name": "Water Purification Unit - Portable",
            "category": "Equipment",
            "serial": "WTR-JPN-001",
            "price": 290000,
            "donor": "JAPAN",
            "location": "Cold Chain Storage - Lodwar",
            "condition": "New",
        },
        {
            "tag": "LOK-DRONE-001",
            "name": "Survey Drone - DJI Mavic 3",
            "category": "IT Equipment",
            "serial": "DRONE-EU-001",
            "price": 485000,
            "donor": "EU",
            "location": "LOKADO Transit Store - Kitale",
            "condition": "Good",
        },
        {
            "tag": "LOK-MEDFRIDGE-001",
            "name": "Medical Refrigerator - Solar",
            "category": "Equipment",
            "serial": "FRIDGE-JPN-002",
            "price": 370000,
            "donor": "JAPAN",
            "location": "Cold Chain Storage - Lodwar",
            "condition": "New",
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
    print("  Assets: 16 registers, 16 verifications, 5 controlled movements, 1 disposal")


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

def _seed_additional_supplier_categories():
    for supplier, category in (
        ("Lodwar General Supplies", "WASH Supplies"),
        ("Rift Valley Hardware", "WASH Supplies"),
        ("Lorugum Welding & Fabrication", "Educational Supplies"),
        ("Kainuk Agro-Vet Supplies", "Food Security"),
        ("Northern Kenya Solar Ltd", "Educational Supplies"),
        ("Turkwel Renewable Energy", "Educational Supplies"),
        ("Lake Turkana Water Services", "Educational Supplies"),
        ("Eldoret Office Technologies", "Educational Supplies"),
        ("Kenya Red Cross Supplies", "Medical Supplies"),
        ("Lodwar General Supplies", "Livestock & Agriculture"),
        ("Kenya Red Cross Supplies", "Livestock & Agriculture"),
        ("Lodwar General Supplies", "Food Security"),
        ("Lokichoggio Traders Ltd", "Food Security"),
    ):
        _ensure(
            "Supplier Prequalification", {"supplier": supplier, "category": category}, None,
            {"supplier": supplier, "category": category, "status": "Prequalified",
             "prequalification_date": add_days(today(), -30),
             "expiry_date": add_days(today(), 365)},
        )


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
         "Procurement of 100 Galla goats for distribution to 238 households in "
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
         "Open Tender", "Approved",
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
# PR11: Medical supplies — Japan funded, Direct RFQ, Approved
        ("Cold Chain Medical Supplies - Japan Health", "JAPAN", 160000,
         "Request for Quotation (Direct)", "Approved",
         "Peace Building & Conflict Resolution - LOKADO", "SURGICAL-GLOVES",
         "Procurement of surgical gloves and first aid supplies for mobile clinics "
         "serving Kakuma and Kalobeyei refugee populations."),
        # PR12: NFI tent procurement — Concern, Open Tender, Approved
        ("Emergency Shelter Tarpaulins - Concern DRC", "CONCERN", 550000,
         "Open Tender", "Approved",
         "Gender & Protection - LOKADO", "TARPAULIN-4X6",
         "Procurement of 800 heavy-duty tarpaulins for emergency shelter response "
         "in Loima and Lokichoggio flood-affected areas."),
        # PR13: Education materials — USAID, Restricted, Approved
        ("Classroom Furniture & Stationery - USAID Education", "USAID", 420000,
         "Restricted Tender", "Approved",
         "Institutional Development - LOKADO", "SCHOOL-DESK",
         "Provision of 3-seater desks, textbooks and stationery kits for 15 primary "
         "schools in Turkana West under USAID Tusome programme."),
        # PR14: Fishing equipment — EU, Restricted, Draft
        ("Fishing Livelihood Equipment - Lake Turkana", "EU", 380000,
         "Restricted Tender", "Draft",
         "Livelihoods & Food Security - LOKADO", "FISHING-NET",
         "Draft requirement for gill nets, boats and safety equipment for 12 fishing "
         "cooperatives along Lake Turkana shoreline."),
        # PR15: Construction timber — IOM, Direct, Pending
        ("Timber Poles - IOM School Construction", "IOM", 180000,
         "Request for Quotation (Direct)", "Pending Approval",
         "Institutional Development - LOKADO", "TIMBER-POLE",
         "Treated timber poles for 3 classroom blocks in Kakuma host community. "
         "Pending final school-site verification."),
        # PR16: Blankets — LOKADO-OWN, Direct, Approved
        ("Blankets & Bedding - Internal Programme Support", "LOKADO-OWN", 95000,
         "Request for Quotation (Direct)", "Approved",
         "Administration & Finance - LOKADO", "BLANKET-FLEECE",
         "Fleece blankets for staff guest house and field overnight stays in "
         "remote programme locations."),
        # PR17: Solar lanterns — JAPAN, Open, Approved
        ("Solar Lanterns - Japan Education Programme", "JAPAN", 320000,
         "Restricted Tender", "Approved",
         "Institutional Development - LOKADO", "SOLAR-LANTERN",
         "Solar lanterns for 40 primary schools enabling evening study for "
         "learners in off-grid Turkana communities."),
        # PR18: Jerry cans — IOM, Direct, Approved
        ("Emergency Jerry Cans - IOM WASH Response", "IOM", 175000,
         "Request for Quotation (Direct)", "Approved",
         "Emergency WASH - LOKADO", "JERRY-CAN-20L",
         "20-litre jerry cans for 2,000 households in Kakuma host community "
         "under emergency WASH response for cholera prevention."),
        # PR19: Sorghum seeds — EU, Restricted, Pending
        ("Certified Sorghum Seeds - EU Food Security", "EU", 260000,
         "Restricted Tender", "Pending Approval",
         "Livelihoods & Food Security - LOKADO", "SORGHUM-SEEDS",
         "Certified sorghum seeds for 500 smallholder farmers in Turkana South. "
         "Part of EU Resilience drought-recovery programme."),
        # PR20: Cooking pots — USAID, Direct, Approved
        ("Family Cooking Pot Sets - USAID NFI", "USAID", 150000,
         "Request for Quotation (Direct)", "Approved",
         "Gender & Protection - LOKADO", "COOKING-POT-SET",
         "Cooking pot sets for 300 displaced households in Oropoi and Lokiriama "
         "as part of NFI dignity kit distribution."),
        # PR21: Mosquito nets — CONCERN, Direct, Approved
        ("LLIN Mosquito Nets - Concern Health", "CONCERN", 140000,
         "Request for Quotation (Direct)", "Approved",
         "Peace Building & Conflict Resolution - LOKADO", "MOSQUITO-NET",
         "Long-lasting insecticidal nets for malaria prevention in Loima and "
         "Lokichoggio health catchment areas."),
        # PR22: Delivery kits — JAPAN, Open, Approved
        ("Clean Birth Delivery Kits - Japan MNCH", "JAPAN", 280000,
         "Restricted Tender", "Approved",
         "Peace Building & Conflict Resolution - LOKADO", "DELIVERY-KIT",
         "Clean delivery kits for 50 health facilities supporting maternal and "
         "newborn child health across Turkana County."),
        # PR23: Chicken restocking — USAID, Restricted, Rejected
        ("Indigenous Chicken Restocking - USAID Phase 2", "USAID", 310000,
         "Restricted Tender", "Rejected",
         "Livelihoods & Food Security - LOKADO", "CHICKEN-INDIG",
         "Rejected: beneficiary selection criteria requires revision. "
         "Procurement committee directed programme to revalidate HH list."),
        # PR24: ORS supplies — IOM, Direct, Approved
        ("ORS and Diarrhoea Kits - IOM Health", "IOM", 130000,
         "Request for Quotation (Direct)", "Approved",
         "Emergency WASH - LOKADO", "ORS-SACHET",
         "Oral rehydration salts for cholera prevention and treatment in "
         "Kakuma camp and host community health posts."),
        # PR25: Steel reinforcement — LOKADO-OWN, Open, Draft
        ("Steel Bars - LOKADO Office Extension", "LOKADO-OWN", 600000,
         "Open Tender", "Draft",
         "Institutional Development - LOKADO", "STEEL-Y12",
         "Draft: steel reinforcement bars for proposed 2-storey office extension "
         "at Lodwar HQ. Board approval pending."),
    ]

    pr_map = {}
    for title, donor_code, value, method, status, dept, item_code, justification in pr_data:
        pk = title[:40].replace(" ", "-").replace(",", "").replace("—", "-")
        exists = frappe.db.exists("Purchase Requisition", {"title": title})
        if exists:
            _progress_demo_requisition(frappe.get_doc("Purchase Requisition", exists), status)
            pr_map[pk] = exists
            pr_map[title] = exists
            continue

        qty_map = {
            "Water Tanks": 12,
            "Livestock": 100,
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
            "requester": "programme@lokado.org",
            "department": dept,
            "donor": dm.get(donor_code, donor_code),
            "justification": justification,
            "status": "Draft",
            "procurement_method": method,
            "estimated_value": value,
            "items": [{
                "item_code": item_code,
                "quantity": qty,
                "estimated_unit_price": value / qty,
                "uom": frappe.db.get_value("Item", item_code, "stock_uom"),
                "estimated_total": value,
            }],
        })
        with _demo_actor("programme@lokado.org"):
            pr.insert(ignore_permissions=True)
        _progress_demo_requisition(pr, status)
        pr_map[pk] = pr.name
        pr_map[title] = pr.name
        print(f"  PR: {title[:50]} [{donor_code}] {value:,} KES [{status}]")

    _seed_lokado_tenders_and_bids(td, dm, pr_map)
    frappe.db.commit()
    print("  Procurement: 25 PR lifecycle scenarios and 20 source-linked tender scenarios")
def _seed_lokado_tenders_and_bids(td, dm, pr_map):
    """Tenders matching LOKADO procurement scenarios."""

    tender_data = [
        ("Water Tanks WASH IOM", "IOM", 450000,
         "Restricted Tender", "Water Tanks - WASH Programme (IOM)"),
        ("Livestock Galla Goats USAID", "USAID", 380000,
         "Restricted Tender", "Livestock Restocking - Galla Goats (USAID)"),
        ("IOM Warehouse Construction Kakuma", "JAPAN", 1200000,
         "Open Tender", "Construction of IOM-Supported Warehouse - Kakuma"),
        ("Hygiene Kits Gender Concern", "CONCERN", 180000,
         "Request for Quotation (Direct)", "Hygiene Kits - Gender Programme (Concern)"),
        ("Field Motorcycles Peace Building USAID", "USAID", 520000,
         "Open Tender", "Field Motorcycles - Programme Officers (USAID)"),
        ("Solar Water Pumps EU Resilience", "EU", 780000,
         "Open Tender", "Solar Water Pumps - EU Resilience Programme"),
        ("Veterinary Outreach Kits USAID", "USAID", 240000,
         "Restricted Tender", "Veterinary Outreach Kits - USAID Livelihoods"),
        ("Emergency HDPE Pipe Repair IOM", "IOM", 195000,
         "Request for Quotation (Direct)", "Emergency HDPE Pipe Repair - IOM WASH"),
("Cold Chain Medical Supplies Japan", "JAPAN", 160000,
         "Request for Quotation (Direct)", "Cold Chain Medical Supplies - Japan Health"),
        ("Emergency Shelter Tarpaulins Concern", "CONCERN", 550000,
         "Open Tender", "Emergency Shelter Tarpaulins - Concern DRC"),
        ("Classroom Furniture USAID Education", "USAID", 420000,
         "Restricted Tender", "Classroom Furniture & Stationery - USAID Education"),
        ("Fishing Equipment Lake Turkana EU", "EU", 380000,
         "Restricted Tender", "Fishing Livelihood Equipment - Lake Turkana"),
        ("Timber Poles IOM School Construction", "IOM", 180000,
         "Request for Quotation (Direct)", "Timber Poles - IOM School Construction"),
        ("Blankets Internal Programme Support", "LOKADO-OWN", 95000,
         "Request for Quotation (Direct)", "Blankets & Bedding - Internal Programme Support"),
        ("Solar Lanterns Japan Education", "JAPAN", 320000,
         "Restricted Tender", "Solar Lanterns - Japan Education Programme"),
        ("Emergency Jerry Cans IOM WASH", "IOM", 175000,
         "Request for Quotation (Direct)", "Emergency Jerry Cans - IOM WASH Response"),
        ("Sorghum Seeds EU Food Security", "EU", 260000,
         "Restricted Tender", "Certified Sorghum Seeds - EU Food Security"),
        ("Family Cooking Pots USAID NFI", "USAID", 150000,
         "Request for Quotation (Direct)", "Family Cooking Pot Sets - USAID NFI"),
        ("LLIN Mosquito Nets Concern Health", "CONCERN", 140000,
         "Request for Quotation (Direct)", "LLIN Mosquito Nets - Concern Health"),
        ("Clean Birth Delivery Kits Japan MNCH", "JAPAN", 280000,
         "Restricted Tender", "Clean Birth Delivery Kits - Japan MNCH"),
    ]

    for t_title, donor_code, value, method, pr_key in tender_data:
        if frappe.db.exists("Tender", {"title": t_title}):
            continue

        pr_name = pr_map.get(pr_key)
        if not pr_name:
            frappe.throw(f"Tender {t_title} has no source requisition: {pr_key}")
        requisition = frappe.get_doc("Purchase Requisition", pr_name)
        tender = frappe.get_doc({
            "doctype": "Tender",
            "title": t_title,
            "purchase_requisition": pr_name,
            "donor": requisition.donor,
            "procurement_method": requisition.procurement_method,
            "estimated_value": value,
            "item_category": frappe.db.get_value("Item", requisition.items[0].item_code, "item_group"),
            "submission_deadline": str(add_days(td, 21)),
            "status": "Draft",
            "opening_officer_1": "opening1@lokado.org",
            "opening_officer_2": "opening2@lokado.org",
            "opening_officer_3": "opening3@lokado.org",
            "evaluation_committee": [
                {"user": user, "role": role, "email": user}
                for user, role in LOKADO_EVALUATION_COMMITTEE
            ] if requisition.procurement_method in ("Restricted Tender", "Open Tender") else [],
            "bid_security_required": (
                25000 if "Warehouse" in t_title else
                10000 if value > 500000 else 0
            ),
        })
        tender.insert(ignore_permissions=True)
        if requisition.status != "Approved":
            print(f"  Tender: {t_title} remains Draft until its requisition is approved")
            continue
        tender.publish()
        print(f"  Tender: {t_title[:45]} [{donor_code}] {value:,} KES [{method}]")

        # Fictional attachments use Frappe's private file storage.
        try:
            for dtype, doc_label in [("Bill of Quantities", "Bill of Quantities"),
                                       ("Specifications", "Technical Specifications"),
                                       ("Terms of Reference", "Terms of Reference")]:
                if hasattr(tender, "tender_documents"):
                    from frappe.utils.file_manager import save_file

                    attachment = save_file(
                        f"{tender.name}-{dtype.replace(' ', '-')}.txt",
                        f"FICTIONAL DEMO DOCUMENT\n{t_title}\n{doc_label}\n",
                        "Tender", tender.name, is_private=1,
                    )
                    tender.append("tender_documents", {
                        "document_type": dtype,
                        "document_name": f"{doc_label} - {t_title[:30]}",
                        "attachment": attachment.file_url,
                    })
            tender.save(ignore_permissions=True)
        except Exception:
            frappe.db.rollback()
            raise

    _seed_lokado_bids(td)
    _seed_lokado_addendum(td)


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
            ("Kainuk Agro-Vet Supplies", 400000),
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
            ("Moi's Bridge Livestock", 250000),
        ],
        "Cold Chain Medical Supplies Japan": [
            ("Lodwar Pharmaceuticals Ltd", 154000),
            ("Kenya Red Cross Supplies", 169000),
            ("Kakuma Cold Chain Solutions", 173000),
        ],
        "Emergency Shelter Tarpaulins Concern": [
            ("Kalobeyei Refugee Supplies Ltd", 610000),
            ("Lokichoggio Traders Ltd", 620000),
            ("Rift Valley Hardware", 638000),
        ],
        "Classroom Furniture USAID Education": [
            ("Lorugum Welding & Fabrication", 405000),
            ("Kakuma Stationers & Supplies", 418000),
            ("Eldoret Office Technologies", 425000),
        ],
        "Timber Poles IOM School Construction": [
            ("Lokitaung Hardware & Building", 175000),
            ("Rift Valley Hardware", 180000),
            ("Ekaale Building Works", 184000),
        ],
        "Solar Lanterns Japan Education": [
            ("Northern Kenya Solar Ltd", 299000),
            ("Turkwel Renewable Energy", 309000),
            ("Lake Turkana Water Services", 318000),
        ],
        "Emergency Jerry Cans IOM WASH": [
            ("Lokitaung Hardware & Building", 91000),
            ("Lodwar General Supplies", 94000),
            ("Lokichoggio Traders Ltd", 96000),
        ],
        "Sorghum Seeds EU Food Security": [
            ("Kainuk Agro-Vet Supplies", 280000),
            ("Lodwar General Supplies", 288000),
            ("Lokichoggio Traders Ltd", 295000),
        ],
        "Family Cooking Pots USAID NFI": [
            ("Lokichar General Traders", 144000),
            ("Lokichoggio Traders Ltd", 150000),
            ("Lodwar General Supplies", 155000),
        ],
        "LLIN Mosquito Nets Concern Health": [
            ("Lodwar Pharmaceuticals Ltd", 121000),
            ("Kenya Red Cross Supplies", 125000),
            ("Kalobeyei Refugee Supplies Ltd", 129000),
        ],
        "Clean Birth Delivery Kits Japan MNCH": [
            ("Lodwar Pharmaceuticals Ltd", 263000),
            ("Kenya Red Cross Supplies", 270000),
            ("Kakuma Cold Chain Solutions", 278000),
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
            frappe.throw(f"Missing tender for bid scenario: {t_title}")
        if frappe.db.get_value("Tender", tname, "status") == "Draft":
            continue
        for supplier_name, amount in bids:
            supplier = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
            if not supplier:
                frappe.throw(f"Missing supplier for bid scenario: {supplier_name}")
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
    print("  Procurement Workflow: source-linked PRs, eligible sealed bids; opening and award remain live")


def _prepare_live_opening_demo():
    """Date the submitted solar-pump fixture as a closed, unopened tender."""
    name = frappe.db.get_value(
        "Tender", {"title": "Solar Water Pumps EU Resilience"}, "name"
    )
    if not name:
        frappe.throw("The live-opening solar-pump demo tender is missing")
    tender = frappe.get_doc("Tender", name)
    if tender.status not in ("Published", "Bids Received"):
        return
    if getdate(tender.submission_deadline) >= getdate(today()):
        tender.publish_date = add_days(today(), -20)
        tender.submission_deadline = str(add_days(today(), -1)) + " 17:00:00"
        tender.save(ignore_permissions=True)
    print("  Live opening ready: Solar Water Pumps EU Resilience (closed, four sealed bids)")


# Tender -> whether the approved recommendation proceeds to an active standstill.
EVALUATION_JOURNEYS = (
    ("Field Motorcycles Peace Building USAID", True),
    ("Livestock Galla Goats USAID", False),
)


def _read_opening_code(officer, tender):
    """Read the officer's code from the local outbox, as the officer reads Mailpit."""
    import email
    import re

    rows = frappe.db.sql(
        """SELECT q.message FROM `tabEmail Queue` q
           JOIN `tabEmail Queue Recipient` r ON r.parent = q.name
           WHERE r.recipient = %s AND q.message LIKE %s
           ORDER BY q.creation DESC LIMIT 1""",
        (officer, f"%Bid Opening OTP - {tender}%"),
    )
    if not rows:
        frappe.throw(f"No opening code was delivered to {officer} for {tender}")
    message = email.message_from_string(rows[0][0])
    for part in message.walk():
        if part.get_content_maintype() == "text":
            body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
            match = re.search(r"Your OTP is (\d{6})", body)
            if match:
                return match.group(1)
    frappe.throw(f"Opening code for {officer} could not be read")


def _close_submission_window(tender):
    """Date a fixture tender as closed after its bids were submitted."""
    if getdate(tender.submission_deadline) >= getdate(today()):
        tender.publish_date = add_days(today(), -30)
        tender.submission_deadline = str(add_days(today(), -8)) + " 17:00:00"
        tender.save(ignore_permissions=True)


def _run_opening_ceremony(tender):
    from ugavi.procurement.services.sealed_bid import init_opening_ceremony, open_bids

    with _demo_actor(tender.opening_officer_1):
        init_opening_ceremony(tender.name)
        codes = {
            f"officer_{index}_otp": _read_opening_code(
                tender.get(f"opening_officer_{index}"), tender.name
            )
            for index in (1, 2, 3)
        }
        return open_bids(tender.name, **codes)


def _score_criteria(rank, evaluator_index, price_score):
    return [
        {"criterion_name": "Technical compliance with specification", "category": "Technical",
         "max_score": 100, "score": 88 - 6 * rank + evaluator_index, "weight": 40},
        {"criterion_name": "Price (lowest responsive bid = 100)", "category": "Financial",
         "max_score": 100, "score": price_score, "weight": 40},
        {"criterion_name": "Delivery schedule to Turkana sites", "category": "Delivery",
         "max_score": 100, "score": 85 - 5 * rank, "weight": 10},
        {"criterion_name": "Past performance and references", "category": "Past Performance",
         "max_score": 100, "score": 80 - 4 * rank, "weight": 10},
    ]


def _seed_evaluation_journeys():
    """Drive real opening, declarations, scoring, minutes and recommendation controllers."""
    from ugavi.tendering.doctype.coi_declaration.coi_declaration import create_coi_declaration
    from ugavi.tendering.services.evaluation import (
        approved_minutes,
        approved_recommendation,
        score_ranking,
    )

    chair, secretary = LOKADO_EVALUATION_COMMITTEE[0][0], LOKADO_EVALUATION_COMMITTEE[1][0]
    for title, start_standstill in EVALUATION_JOURNEYS:
        name = frappe.db.get_value("Tender", {"title": title}, "name")
        if not name:
            frappe.throw(f"Missing evaluation journey tender: {title}")
        tender = frappe.get_doc("Tender", name)
        if not tender.evaluation_committee and tender.status in ("Published", "Bids Received"):
            for user, role in LOKADO_EVALUATION_COMMITTEE:
                tender.append("evaluation_committee", {"user": user, "role": role, "email": user})
            tender.save(ignore_permissions=True)

        if tender.status in ("Published", "Bids Received"):
            _close_submission_window(tender)
            result = _run_opening_ceremony(tender)
            print(f"  Opening: {title[:40]} -> {result['opening_record']} ({result['bids_opened']} bids)")
            tender.reload()
        if tender.status != "Under Evaluation":
            continue

        for user, _role in LOKADO_EVALUATION_COMMITTEE:
            if not frappe.db.exists("COI Declaration", {"tender": tender.name, "declarant": user}):
                with _demo_actor(user):
                    create_coi_declaration(
                        tender.name, user,
                        "DEMO: no financial, family or business interest in any bidder.",
                    )

        bids = frappe.get_all(
            "Bid", filters={"tender": tender.name, "status": "Opened"},
            fields=["name", "bid_amount"], order_by="bid_amount asc",
        )
        lowest = bids[0].bid_amount
        for evaluator_index, (user, _role) in enumerate(LOKADO_EVALUATION_COMMITTEE):
            for rank, bid in enumerate(bids):
                if frappe.db.exists("Evaluation Score", {"bid": bid.name, "evaluator": user}):
                    continue
                with _demo_actor(user):
                    score = frappe.get_doc({
                        "doctype": "Evaluation Score",
                        "tender": tender.name,
                        "evaluator": user,
                        "bid": bid.name,
                        "criteria": _score_criteria(
                            rank, evaluator_index, round(100 * lowest / bid.bid_amount, 1)
                        ),
                        "comments": "DEMO: scored against the published criteria.",
                    })
                    score.insert()
                    score.submit_score()

        if not approved_minutes(tender.name):
            with _demo_actor(secretary):
                minutes = frappe.get_doc({
                    "doctype": "Evaluation Minutes",
                    "tender": tender.name,
                    "session_date": today(),
                    "chairperson": chair,
                    "secretary": secretary,
                    "attendees": [
                        {"user": user, "role": role, "present": 1}
                        for user, role in LOKADO_EVALUATION_COMMITTEE
                    ],
                    "recommendation": (
                        "<p>DEMO: The committee recommends the highest-ranked responsive bid "
                        "after technical, price, delivery and past-performance scoring.</p>"
                    ),
                    "next_steps": "Chair approval, then intended-award notice and standstill.",
                })
                minutes.insert()
            with _demo_actor(chair):
                minutes.approve()

        if not approved_recommendation(tender.name):
            best = score_ranking(tender.name)[0]
            with _demo_actor("procurement@lokado.org"):
                summary = frappe.get_doc({
                    "doctype": "Bid Evaluation Summary",
                    "tender": tender.name,
                    "evaluation_date": today(),
                    "evaluation_minutes": approved_minutes(tender.name),
                    "recommended_bidder": best["supplier"],
                    "recommended_amount": best["bid_amount"],
                    "justification": (
                        f"<p>DEMO: highest average committee score ({best['average']}) "
                        "and lowest evaluated price.</p>"
                    ),
                })
                summary.insert()
            with _demo_actor(chair):
                summary.approve()
            print(f"  Recommendation: {title[:40]} -> {best['supplier']} {best['bid_amount']:,.0f}")

        if start_standstill:
            with _demo_actor("procurement@lokado.org"):
                tender.reload()
                standstill = tender.start_standstill()
            print(f"  Standstill: {title[:40]} -> {standstill} (complaint window open)")

    frappe.db.commit()


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
{
            "tender_title": "Emergency Shelter Tarpaulins Concern",
            "supplier_name": "Kalobeyei Refugee Supplies Ltd",
            "amount": 520000,
            "duration_days": 45,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Stock mobilisation from Kakuma", 30, 7),
                ("First distribution Loima (400 units)", 35, 21),
                ("Second distribution Lokichoggio (400 units)", 35, 45),
            ],
        },
        {
            "tender_title": "Classroom Furniture USAID Education",
            "supplier_name": "Lorugum Welding & Fabrication",
            "amount": 400000,
            "duration_days": 90,
            "retention_pct": 5,
            "bond_amount": 0,
            "milestones": [
                ("Raw material procurement", 15, 10),
                ("Fabrication batch 1 - 100 desks", 35, 35),
                ("Fabrication batch 2 - 100 desks", 25, 60),
                ("Delivery & installation to 15 schools", 25, 90),
            ],
        },
        {
            "tender_title": "Field Motorcycles Peace Building USAID",
            "supplier_name": "Jopeji Enterprises",
            "amount": 510000,
            "duration_days": 30,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Pre-delivery inspection & registration", 30, 7),
                ("Delivery to 4 field offices", 50, 20),
                ("After-sales training & toolkit handover", 20, 30),
            ],
        },
        {
            "tender_title": "Fishing Equipment Lake Turkana EU",
            "supplier_name": "Lake Turkana Fishermen's Cooperative",
            "amount": 365000,
            "duration_days": 60,
            "retention_pct": 5,
            "bond_amount": 0,
            "milestones": [
                ("Net procurement & QA", 30, 15),
                ("Distribution to 12 cooperatives", 45, 40),
                ("Training on sustainable fishing", 25, 60),
            ],
        },
        {
            "tender_title": "Solar Lanterns Japan Education",
            "supplier_name": "Northern Kenya Solar Ltd",
            "amount": 305000,
            "duration_days": 45,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Procurement & import clearance", 40, 14),
                ("Distribution to 20 schools (phase 1)", 30, 28),
                ("Distribution to 20 schools (phase 2)", 30, 45),
            ],
        },
        {
            "tender_title": "Sorghum Seeds EU Food Security",
            "supplier_name": "Kainuk Agro-Vet Supplies",
            "amount": 248000,
            "duration_days": 35,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Seed certification & packaging", 30, 10),
                ("Distribution to 250 farmer groups (phase 1)", 40, 22),
                ("Distribution to 250 farmer groups (phase 2)", 30, 35),
            ],
        },
        {
            "tender_title": "Clean Birth Delivery Kits Japan MNCH",
            "supplier_name": "Lodwar Pharmaceuticals Ltd",
            "amount": 265000,
            "duration_days": 40,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Procurement from Nairobi", 35, 10),
                ("Cold-chain delivery to 25 facilities (phase 1)", 40, 25),
                ("Cold-chain delivery to 25 facilities (phase 2)", 25, 40),
            ],
        },
        {
            "tender_title": "Cold Chain Medical Supplies Japan",
            "supplier_name": "Lodwar Pharmaceuticals Ltd",
            "amount": 155000,
            "duration_days": 21,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Procurement & QA clearance", 50, 7),
                ("Delivery to 5 mobile clinic hubs", 50, 21),
            ],
        },
        {
            "tender_title": "Emergency Jerry Cans IOM WASH",
            "supplier_name": "Lokichoggio Traders Ltd",
            "amount": 170000,
            "duration_days": 14,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Stock mobilisation", 40, 3),
                ("Distribution to 2,000 households", 60, 14),
            ],
        },
        {
            "tender_title": "Timber Poles IOM School Construction",
            "supplier_name": "Lokitaung Hardware & Building",
            "amount": 175000,
            "duration_days": 30,
            "retention_pct": 0,
            "bond_amount": 0,
            "milestones": [
                ("Timber procurement & treatment", 40, 10),
                ("Delivery to 3 school sites", 60, 30),
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
    print("  Contracts: 15 Ugavi Contracts with milestones, retention and bonds")


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
            ("GOAT-GALLA", 100, 3650, "BAT-2025-USAID-GOAT", "2026-06-30"),
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
        ("Kalobeyei Refugee Supplies Ltd", "LOKADO Field Store - Lokichoggio", [
            ("TARPAULIN-4X6", 800, 650, None, None),
            ("BLANKET-FLEECE", 500, 480, None, None),
        ]),
        ("Lorugum Welding & Fabrication", "LOKADO Main Warehouse - Lodwar", [
            ("SCHOOL-DESK", 200, 2000, None, None),
            ("STATIONERY-KIT", 300, 350, None, None),
        ]),
        ("Lodwar Pharmaceuticals Ltd", "Cold Chain Storage - Lodwar", [
            ("SURGICAL-GLOVES", 200, 800, None, None),
            ("DELIVERY-KIT", 250, 1060, None, None),
        ]),
        ("Lokitaung Hardware & Building", "IOM Supported Warehouse - Kakuma", [
            ("TIMBER-POLE", 300, 583, None, None),
            ("JERRY-CAN-20L", 2000, 85, None, None),
        ]),
        ("Northern Kenya Solar Ltd", "Cold Chain Storage - Lodwar", [
            ("SOLAR-LANTERN", 200, 1525, None, None),
        ]),
        ("Lake Turkana Fishermen's Cooperative", "LOKADO Transit Store - Kitale", [
            ("FISHING-NET", 120, 3042, None, None),
        ]),
        ("Kainuk Agro-Vet Supplies", "LOKADO Transit Store - Kitale", [
            ("SORGHUM-SEEDS", 500, 496, None, None),
        ]),
        ("Lodwar Pharmaceuticals Ltd", "LOKADO Field Store - Lokichoggio", [
            ("MOSQUITO-NET", 600, 233, None, None),
            ("ORS-SACHET", 400, 325, None, None),
        ]),
        ("Lokichar General Traders", "LOKADO Field Store - Oropoi", [
            ("LAPTOP-DELL", 5, 97500, None, None),
        ]),
        ("Kakuma Stationers & Supplies", "LOKADO Main Warehouse - Lodwar", [
            ("TEXTBOOKS-SET", 100, 2800, None, None),
        ]),
        ("Turkwel Renewable Energy", "Cold Chain Storage - Lodwar", [
            ("WATER-PUMP-SOLAR", 5, 185000, None, None),
        ]),
        ("Turkana Women's Handicrafts Cooperative", "LOKADO Field Store - Oropoi", [
            ("BLANKET-FLEECE", 100, 480, None, None),
        ]),
        ("Lokitaung Hardware & Building", "LOKADO Main Warehouse - Lodwar", [
            ("IRON-SHEET-G32", 100, 850, None, None),
        ]),
        ("Lake Turkana Water Services", "IOM Supported Warehouse - Kakuma", [
            ("WATER-TANK-10K", 4, 48000, None, None),
        ]),
        ("Lokichoggio Traders Ltd", "LOKADO Field Store - Lokichoggio", [
            ("JERRY-CAN-20L", 1000, 85, None, None),
        ]),
        ("Eldoret Office Technologies", "LOKADO Field Store - Oropoi", [
            ("LAPTOP-DELL", 5, 97500, None, None),
        ]),
        ("Lokichar General Traders", "LOKADO Main Warehouse - Lodwar", [
            ("COOKING-POT-SET", 300, 500, None, None),
        ]),
        ("Kalobeyei Refugee Supplies Ltd", "LOKADO Transit Store - Kitale", [
            ("TARPAULIN-4X6", 200, 650, None, None),
        ]),
    ]

    for supplier_name, wh_name, items in receipt_scenarios:
        from ugavi.scripts.seed_fleet_journey import _activate_contract

        supplier = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
        wh_full = _wh(wh_name)
        if not supplier or not wh_full:
            frappe.throw(f"Missing supplier or warehouse for {supplier_name}: {wh_name}")
        # Check if a receipt for this supplier+warehouse combo already exists
        existing_receipt = frappe.db.exists("Purchase Receipt", {
            "supplier": supplier,
            "set_warehouse": wh_full, "docstatus": 1,
        })
        contract_scenario = {
            "marker": f"LOKADO-DEMO-GRN-{supplier_name}-{wh_name}"[:140],
            "purpose": f"Programme supplies delivered to {wh_name}",
        }
        if existing_receipt:
            _activate_contract(frappe.get_doc("Purchase Receipt", existing_receipt), contract_scenario)
            continue
        try:
            order = _ensure_logistics_purchase_order(supplier, supplier_name, wh_full, items, td)
            from erpnext.buying.doctype.purchase_order.purchase_order import (
                make_purchase_receipt,
            )

            pr = make_purchase_receipt(order.name)
            pr.supplier_delivery_note = f"LOKADO-DEMO-GRN-{supplier_name}-{wh_name}"[:140]
            pr.set_warehouse = wh_full
            pr.set_posting_time = 1
            pr.posting_date = str(add_days(td, -10))
            for child in pr.items:
                child.warehouse = wh_full
                batch_no = next(
                    (b for code, _q, _r, b, _e in items if code == child.item_code), None
                )
                # Only set batch_no if the Batch record exists (created by the fleet seed)
                if batch_no and frappe.db.exists("Batch", batch_no):
                    child.batch_no = batch_no
            pr.insert(ignore_permissions=True)
            _inspect_demo_receipt(pr)
            pr.reload()
            pr.submit()
            _activate_contract(pr, contract_scenario)
            frappe.db.commit()
            print(f"  PurchaseReceipt: {supplier_name[:25]} → {wh_name[:35]} (from {order.name})")
        except Exception:
            frappe.db.rollback()
            raise

    frappe.db.commit()
    print(f"  Logistics: {len(receipt_scenarios)} submitted supplier/warehouse receipts")
    print(
        f"  {len(LOKADO_USERS)} users available "
        f"({len(LOKADO_USERS) - len(SUPPLIER_PORTAL_LINKS)} staff + "
        f"{len(SUPPLIER_PORTAL_LINKS)} supplier portal users)"
    )


def _inspect_demo_receipt(receipt):
    """Use incoming inspections before submission, including on partial reruns."""
    for row in receipt.items:
        if not frappe.db.get_value("Item", row.item_code, "inspection_required_before_purchase"):
            continue
        existing = frappe.db.get_value(
            "Quality Inspection",
            {"reference_type": "Purchase Receipt", "reference_name": receipt.name,
             "item_code": row.item_code, "docstatus": 1}, "name",
        )
        if existing:
            continue
        inspection = frappe.get_doc({
            "doctype": "Quality Inspection",
            "inspection_type": "Incoming",
            "reference_type": "Purchase Receipt",
            "reference_name": receipt.name,
            "item_code": row.item_code,
            "report_date": receipt.posting_date,
            "sample_size": min(row.qty, max(1, row.qty // 10)),
            "inspected_by": "Administrator",
            "status": "Accepted",
            "remarks": "DEMO: specification, quantity and packaging accepted before GRN submission.",
        })
        inspection.insert(ignore_permissions=True)
        inspection.submit()


def _seed_monthly_stock_reports():
    """Generate current-period donor books from posted stock, never sample totals."""
    month = frappe.utils.get_first_day(today())
    scenarios = [
        ("IOM", 60, "IOM Supported Warehouse - Kakuma"),
        ("USAID", 30, "LOKADO Main Warehouse - Lodwar"),
        ("CONCERN", 45, "LOKADO Field Store - Lokichoggio"),
        ("JAPAN", 75, "Cold Chain Storage - Lodwar"),
        ("EU", 90, "LOKADO Transit Store - Kitale"),
        ("LOKADO-OWN", 15, "LOKADO Field Store - Oropoi"),
    ]
    for code, legacy_days_ago, warehouse_name in scenarios:
        donor = frappe.db.get_value("Donor Profile", {"donor_code": code}, "name")
        warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": warehouse_name}, "name")
        filters = {"donor": donor, "warehouse": warehouse, "report_month": month}
        name = frappe.db.get_value("Monthly Stock Report", filters, "name")
        if not name:
            # Upgrade the earlier demo fixture in place; do not remove historical user reports.
            name = frappe.db.get_value(
                "Monthly Stock Report",
                {**filters, "report_month": add_days(today(), -legacy_days_ago)}, "name",
            )
        if name:
            report = frappe.get_doc("Monthly Stock Report", name)
            report.report_month = month
        else:
            report = frappe.get_doc({"doctype": "Monthly Stock Report", **filters})
            report.insert(ignore_permissions=True)
        report.generate()
        print(f"  StockReport: {code} [{month}] — {len(report.items)} ledger-derived rows")


def _ensure_logistics_purchase_order(supplier, supplier_name, warehouse, items, td):
    """Submitted, donor-tagged PO so receipts and invoices form a real three-way match."""
    title = f"LOKADO-GRN-{supplier_name}-{warehouse}"[:140]
    name = frappe.db.get_value(
        "Purchase Order", {"title": title, "docstatus": ("<", 2)}, "name"
    )
    if name:
        order = frappe.get_doc("Purchase Order", name)
    else:
        order = frappe.get_doc({
            "doctype": "Purchase Order",
            "title": title,
            "company": "Lotus Kenya Action for Development Organization",
            "supplier": supplier,
            "transaction_date": str(add_days(td, -25)),
            "schedule_date": str(add_days(td, -12)),
            "set_warehouse": warehouse,
            "ugavi_donor": frappe.db.get_value(
                "Donor Warehouse", {"warehouse": warehouse}, "donor"
            ),
            "items": [
                {
                    "item_code": item_code,
                    "qty": qty,
                    "rate": rate,
                    "schedule_date": str(add_days(td, -12)),
                    "warehouse": warehouse,
                }
                for item_code, qty, rate, _batch, _expiry in items
            ],
        })
        order.insert(ignore_permissions=True)
    if order.docstatus == 0:
        order.submit()
    return order


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
{
            "supplier_name": "Northern Kenya Solar Ltd",
            "delivery_quality": 4.5, "timeliness": 4.3, "compliance": 4.5,
            "overall": 4.4,
            "comments": "Solar lantern delivery to specification. Installation training provided for 10 school technicians. Good warranty documentation.",
        },
        {
            "supplier_name": "Lake Turkana Water Services",
            "delivery_quality": 4.7, "timeliness": 4.5, "compliance": 4.8,
            "overall": 4.7,
            "comments": "Water treatment chemicals delivered on time with full MSDS documentation. Consistent quality across 4 quarterly deliveries.",
        },
        {
            "supplier_name": "Lokichoggio Traders Ltd",
            "delivery_quality": 4.2, "timeliness": 4.0, "compliance": 4.0,
            "overall": 4.1,
            "comments": "Jerry cans and WASH items. Minor packaging issue on initial batch. Prompt corrective action. Good logistics to remote sites.",
        },
        {
            "supplier_name": "Kakuma Cold Chain Solutions",
            "delivery_quality": 4.9, "timeliness": 4.5, "compliance": 4.8,
            "overall": 4.7,
            "comments": "Vaccine refrigerators delivered within cold-chain integrity. Full installation and maintenance training. Excellent technical support.",
        },
        {
            "supplier_name": "Eldoret Office Technologies",
            "delivery_quality": 4.3, "timeliness": 4.0, "compliance": 4.2,
            "overall": 4.2,
            "comments": "Laptops and IT equipment. Slight delay on Dell shipment. Good after-sales setup and configuration support provided.",
        },
        {
            "supplier_name": "Turkwel Renewable Energy",
            "delivery_quality": 4.4, "timeliness": 3.8, "compliance": 4.5,
            "overall": 4.2,
            "comments": "Solar pumping equipment delivered. 3-day delay on battery shipment resolved. Installation quality excellent.",
        },
        {
            "supplier_name": "North Rift Transporters",
            "delivery_quality": 3.9, "timeliness": 3.5, "compliance": 3.8,
            "overall": 3.7,
            "comments": "Transport services acceptable. One truck breakdown caused 2-day delay. Recovery was prompt. Recommend fleet maintenance schedule.",
        },
        {
            "supplier_name": "Lodwar Pharmaceuticals Ltd",
            "delivery_quality": 5.0, "timeliness": 4.7, "compliance": 5.0,
            "overall": 4.9,
            "comments": "Clean birth delivery kits and surgical gloves. PPB certification verified. Cold chain maintained throughout. Outstanding supplier.",
        },
        {
            "supplier_name": "Lorugum Welding & Fabrication",
            "delivery_quality": 4.0, "timeliness": 4.2, "compliance": 3.8,
            "overall": 4.0,
            "comments": "School desks fabricated to specification. Welding quality acceptable. Paint finish needs improvement. Price competitive for local supplier.",
        },
        {
            "supplier_name": "Kainuk Agro-Vet Supplies",
            "delivery_quality": 4.3, "timeliness": 4.0, "compliance": 4.5,
            "overall": 4.3,
            "comments": "Certified sorghum seeds with KEPHIS documentation. Germination rate 92%. Extension support for farmer groups appreciated.",
        },
    ]

    # Suppliers without a stock delivery are evaluated against a direct service
    # invoice, the same source document the Purchase Invoice hook uses in production.
    direct_service_purchases = {
        "Ekaale Building Works": (
            "LOK-SVC-EKAALE-001", "Solar pump house repair works (rework completed)", 145000,
        ),
        "Moi's Bridge Livestock": (
            "LOK-SVC-MOIS-001", "Livestock transport Kitale to Lodwar", 98000,
        ),
        "Kakuma Cold Chain Solutions": (
            "LOK-SVC-COLD-001", "Cold-chain installation and temperature validation", 125000,
        ),
        "North Rift Transporters": (
            "LOK-SVC-TRANSPORT-001", "Last-mile programme transport and delivery", 112000,
        ),
    }

    completed = 0
    for scenario in evaluation_scenarios:
        supplier = frappe.db.get_value(
            "Supplier", {"supplier_name": scenario["supplier_name"]}, "name"
        )
        if not supplier:
            continue
        if scenario["supplier_name"] in direct_service_purchases:
            _ensure_direct_service_invoice(
                supplier, *direct_service_purchases[scenario["supplier_name"]]
            )
        evaluation_name = _pending_or_completed_evaluation(supplier, scenario["comments"])
        if not evaluation_name:
            frappe.throw(f"No purchase source for demo evaluation: {scenario['supplier_name']}")
        evaluation = frappe.get_doc("Ugavi Supplier Evaluation", evaluation_name)
        if evaluation.status == "Completed":
            completed += 1
            continue
        # Scenario ratings are on a 5-point scale; the scorecard uses 0-10.
        evaluation.quality_score = scenario["delivery_quality"] * 2
        evaluation.delivery_score = scenario["timeliness"] * 2
        evaluation.compliance_score = scenario["compliance"] * 2
        evaluation.price_competitiveness = scenario["overall"] * 2
        evaluation.evaluation_date = str(add_days(today(), -5))
        evaluation.remarks = scenario["comments"]
        evaluation.flags.ignore_permissions = True
        evaluation.complete_evaluation()
        completed += 1
        print(
            f"  SupplierEval: {scenario['supplier_name'][:25]} → "
            f"{evaluation.total_score}% (cumulative {evaluation.cumulative_rating}%)"
        )

    for bill_no, supplier_name, warehouse_name, _share, _mode in RECEIPT_INVOICES:
        receipt = _logistics_receipt(supplier_name, warehouse_name)
        if not receipt:
            frappe.throw(f"Missing receipt for scorecard: {bill_no}")
        evaluation_name = frappe.db.get_value(
            "Ugavi Supplier Evaluation", {"purchase_receipt": receipt}, "name"
        )
        evaluation = frappe.get_doc("Ugavi Supplier Evaluation", evaluation_name)
        if evaluation.status == "Pending":
            evaluation.quality_score = 8
            evaluation.delivery_score = 8
            evaluation.compliance_score = 9
            evaluation.price_competitiveness = 8
            evaluation.remarks = f"DEMO: delivery inspected and accepted for {bill_no}"
            evaluation.flags.ignore_permissions = True
            evaluation.complete_evaluation()
    frappe.db.commit()
    print(f"  Supplier Evaluations: {completed}/{len(evaluation_scenarios)} scenario scorecards completed")


def _pending_or_completed_evaluation(supplier, comments):
    """Reuse this scenario's completed scorecard, else take the oldest pending one."""
    return frappe.db.get_value(
        "Ugavi Supplier Evaluation",
        {"supplier": supplier, "status": "Completed", "remarks": comments},
        "name",
    ) or frappe.db.get_value(
        "Ugavi Supplier Evaluation",
        {"supplier": supplier, "status": "Pending"},
        "name",
        order_by="creation asc",
    )


def _ensure_service_item():
    item_code = "SVC-FIELD-WORKS"
    if not frappe.db.exists("Item", item_code):
        frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Field Works and Logistics Services",
            "item_group": "Services" if frappe.db.exists("Item Group", "Services") else "All Item Groups",
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "is_purchase_item": 1,
            "include_item_in_manufacturing": 0,
        }).insert(ignore_permissions=True)
    return item_code


def _ensure_direct_service_invoice(supplier, bill_no, description, amount):
    """Submitted non-stock invoice; its on_submit hook creates the pending evaluation."""
    existing = frappe.db.get_value(
        "Purchase Invoice", {"supplier": supplier, "bill_no": bill_no, "docstatus": ("<", 2)},
        ["name", "docstatus"], as_dict=True,
    )
    if existing and existing.docstatus == 1:
        return existing.name
    if existing:
        invoice = frappe.get_doc("Purchase Invoice", existing.name)
    else:
        invoice = frappe.get_doc({
            "doctype": "Purchase Invoice",
            "company": "Lotus Kenya Action for Development Organization",
            "supplier": supplier,
            "bill_no": bill_no,
            "bill_date": str(add_days(today(), -20)),
            "posting_date": str(add_days(today(), -20)),
            "set_posting_time": 1,
            "remarks": description,
            "items": [{
                "item_code": _ensure_service_item(),
                "description": description,
                "qty": 1,
                "rate": amount,
                "expense_account": "Miscellaneous Expenses - LOKADO",
            }],
        })
        invoice.insert(ignore_permissions=True)
    invoice.submit()
    print(f"  DirectInvoice: {bill_no} → {amount:,} KES (service, no receipt)")
    return invoice.name


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
    from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
        get_doctypes_with_dimensions,
        make_dimension_in_accounting_doctypes,
    )
    for doctype in ["Donor Profile"]:
        dims = frappe.get_all("Accounting Dimension", {"document_type": doctype}, pluck="name")
        if not dims:
            dimension = frappe.get_doc({
                "doctype": "Accounting Dimension",
                "document_type": doctype,
                "disabled": 0,
            }).insert(ignore_permissions=True)
        else:
            dimension = frappe.get_doc("Accounting Dimension", dims[0])
        # Complete ERPNext's queued schema setup before posting demo transactions.
        make_dimension_in_accounting_doctypes(
            dimension, doclist=list(dict.fromkeys(get_doctypes_with_dimensions() + ["Budget"])),
        )
        print(f"  AcctDimension: {doctype} schema ready")

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
        ("LOKADO Field Store - Lokichoggio", "TARPAULIN-4X6", "Incoming",
         800, "BAT-2025-CONC-TARP", add_days(td, -8),
         "UV resistance test, tear strength, eyelet integrity"),
        ("LOKADO Main Warehouse - Lodwar", "SCHOOL-DESK", "Incoming",
         200, "BAT-2025-USA-DESK", add_days(td, -7),
         "Weld integrity, dimensional accuracy, paint coat thickness"),
        ("LOKADO Field Store - Lokichoggio", "BLANKET-FLEECE", "Incoming",
         500, "BAT-2025-OWN-BLANK", add_days(td, -6),
         "Fibre content verification, dimensional check, colour fastness"),
        ("LOKADO Transit Store - Kitale", "FISHING-NET", "Incoming",
         120, "BAT-2025-EU-NET", add_days(td, -5),
         "Mesh size calibration, tensile strength test, float integrity"),
        ("Cold Chain Storage - Lodwar", "SURGICAL-GLOVES", "Incoming",
         200, "BAT-2025-JPN-GLOVES", add_days(td, -4),
         "Sterility seal, box integrity, expiry date verification"),
        ("IOM Supported Warehouse - Kakuma", "TIMBER-POLE", "Incoming",
         300, "BAT-2025-IOM-POLE", add_days(td, -3),
         "CCA treatment verification, straightness, diameter tolerance"),
        ("IOM Supported Warehouse - Kakuma", "JERRY-CAN-20L", "Incoming",
         2000, "BAT-2025-IOM-JERRY", add_days(td, -2),
         "Drop test, cap seal integrity, food-grade plastic certification"),
        ("Cold Chain Storage - Lodwar", "SOLAR-LANTERN", "Incoming",
         200, "BAT-2025-JPN-LANTERN", add_days(td, -3),
         "Charge-discharge cycle test, lumen output, waterproof rating"),
        ("Cold Chain Storage - Lodwar", "DELIVERY-KIT", "Incoming",
         250, "BAT-2025-JPN-DELIV", add_days(td, -2),
         "Sterile seal on each kit, completeness check, expiry dates"),
        ("LOKADO Main Warehouse - Lodwar", "COOKING-POT-SET", "Incoming",
         300, "BAT-2025-USA-POT", add_days(td, -1),
         "Aluminium gauge, handle rivet strength, lid fit"),
        ("LOKADO Transit Store - Kitale", "SORGHUM-SEEDS", "Incoming",
         500, "BAT-2025-EU-SORGHUM", add_days(td, -2),
         "Germination rate test, purity analysis, KEPHIS certification check"),
        ("LOKADO Field Store - Lokichoggio", "MOSQUITO-NET", "Incoming",
         600, "BAT-2025-CONC-MOSQ", add_days(td, -1),
         "WHOPES certification, mesh integrity, insecticide treatment verification"),
    ]
    for wh, item_code, insp_type, qty, batch, insp_date, remarks in qc_data:
        wh_name = _wh(wh)
        receipt_rows = frappe.db.sql(
            """SELECT i.parent, i.qty, i.serial_and_batch_bundle, p.posting_date
               FROM `tabPurchase Receipt Item` i
               JOIN `tabPurchase Receipt` p ON p.name = i.parent
               WHERE p.docstatus = 1 AND i.item_code = %s AND i.warehouse = %s
               ORDER BY p.creation, i.idx LIMIT 1""",
            (item_code, wh_name), as_dict=True,
        )
        if not receipt_rows:
            frappe.throw(f"QC has no submitted receipt: {item_code} in {wh_name}")
        source = receipt_rows[0]
        pr_name = source.parent
        if frappe.db.exists("Quality Inspection", {
            "item_code": item_code, "reference_name": pr_name, "docstatus": 1,
        }):
            continue
        batch = (
            frappe.db.get_value("Serial and Batch Entry",
                                {"parent": source.serial_and_batch_bundle}, "batch_no")
            if source.serial_and_batch_bundle else None
        )
        try:
            qc = frappe.get_doc({
                "doctype": "Quality Inspection",
                "item_code": item_code,
                "item_name": frappe.db.get_value("Item", item_code, "item_name") or item_code,
                "inspection_type": insp_type,
                "report_date": str(insp_date),
                "sample_size": min(source.qty, max(1, source.qty // 10)),
                "reference_type": "Purchase Receipt",
                "reference_name": pr_name,
                "batch_no": batch,
                "inspected_by": "Administrator",
                "remarks": remarks,
                "status": "Accepted",
            })
            qc.insert(ignore_permissions=True)
            qc.submit()
            print(f"  QC: {item_code} @ {wh[:25]} [{qty} units]")
        except Exception:
            frappe.db.rollback()
            raise
    frappe.db.commit()
    print("  Quality Inspections: 20 incoming QC records")


# ─────────────────────────────────────────────────
# 11. STOCK ENTRIES — Material Receipt/Issue/Transfer
# ─────────────────────────────────────────────────

STOCK_RECEIPT_RATES = {
    "CEMENT-BAG": 1100, "WATER-TANK-10K": 52000, "GOAT-GALLA": 3650,
    "ANIMAL-FEED": 520, "VET-KIT": 4500, "HYGIENE-KIT": 175,
    "FIRST-AID-KIT": 1500, "PIPE-HDPE-63MM": 290, "MOTORCYCLE-FIELD": 130000,
    "WATER-PUMP-SOLAR": 185000, "LAPTOP-DELL": 97500, "FUEL-DIESEL": 210,
    "CHICKEN-INDIG": 380, "STEEL-Y12": 95000, "IRON-SHEET-G32": 850,
    "TARPAULIN-4X6": 650, "BLANKET-FLEECE": 480, "JERRY-CAN-20L": 85,
    "COOKING-POT-SET": 500, "SCHOOL-DESK": 2000, "STATIONERY-KIT": 350,
    "TEXTBOOKS-SET": 2800, "SOLAR-LANTERN": 1525, "SORGHUM-SEEDS": 520,
    "FISHING-NET": 3042, "TIMBER-POLE": 583, "SURGICAL-GLOVES": 800,
    "DELIVERY-KIT": 1060, "MOSQUITO-NET": 233, "ORS-SACHET": 325,
}


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
         add_days(td, -14), [("GOAT-GALLA", 100), ("ANIMAL-FEED", 50), ("VET-KIT", 30)],
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
        ("Material Receipt", None, _wh("Cold Chain Storage - Lodwar"),
         add_days(td, -9), [("FIRST-AID-KIT", 100), ("WATER-PUMP-SOLAR", 5)],
         "Receive Japan health cold-chain and solar pump stock"),
        ("Material Receipt", None, _wh("LOKADO Field Store - Oropoi"),
         add_days(td, -12), [("LAPTOP-DELL", 12), ("FUEL-DIESEL", 600)],
         "Receive LOKADO own-funds laptops and generator diesel at Oropoi"),
        ("Material Issue", _wh("IOM Supported Warehouse - Kakuma"), None,
         add_days(td, -5), [("CEMENT-BAG", 80), ("PIPE-HDPE-63MM", 200)],
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
        ("Material Issue", _wh("LOKADO Field Store - Oropoi"), None,
         add_days(td, -4), [("LAPTOP-DELL", 3), ("FUEL-DIESEL", 360)],
         "Issue own-funds laptops and generator diesel to Oropoi field office"),
        ("Material Receipt", None, _wh("LOKADO Field Store - Lokichoggio"),
         add_days(td, -10), [("TARPAULIN-4X6", 800), ("BLANKET-FLEECE", 500)],
         "Receive shelter materials from Kalobeyei Refugee Supplies"),
        ("Material Receipt", None, _wh("LOKADO Main Warehouse - Lodwar"),
         add_days(td, -9), [("SCHOOL-DESK", 200), ("STATIONERY-KIT", 300)],
         "Receive classroom furniture from Lorugum Welding"),
        ("Material Receipt", None, _wh("Cold Chain Storage - Lodwar"),
         add_days(td, -8), [("SURGICAL-GLOVES", 200), ("DELIVERY-KIT", 250)],
         "Receive medical supplies from Lodwar Pharmaceuticals"),
        ("Material Receipt", None, _wh("IOM Supported Warehouse - Kakuma"),
         add_days(td, -7), [("TIMBER-POLE", 300), ("JERRY-CAN-20L", 2000)],
         "Receive construction and WASH from Lokitaung Hardware"),
        ("Material Receipt", None, _wh("LOKADO Transit Store - Kitale"),
         add_days(td, -6), [("FISHING-NET", 120)],
         "Receive EU fishing gear from Lake Turkana Fishers Co-op"),
        ("Material Receipt", None, _wh("Cold Chain Storage - Lodwar"),
         add_days(td, -6), [("SOLAR-LANTERN", 200)],
         "Receive Japan classroom solar lantern opening stock"),
        ("Material Receipt", None, _wh("LOKADO Transit Store - Kitale"),
         add_days(td, -5), [("SORGHUM-SEEDS", 500)],
         "Receive food security items from Kainuk Agro-Vet"),
        ("Material Receipt", None, _wh("LOKADO Main Warehouse - Lodwar"),
         add_days(td, -5), [("COOKING-POT-SET", 300)],
         "Receive USAID household cooking pot opening stock"),
        ("Material Receipt", None, _wh("LOKADO Field Store - Lokichoggio"),
         add_days(td, -4), [("MOSQUITO-NET", 600), ("ORS-SACHET", 400)],
         "Receive health supplies from Lodwar Pharmaceuticals"),
        ("Material Issue", _wh("LOKADO Field Store - Lokichoggio"), None,
         add_days(td, -3), [("TARPAULIN-4X6", 400)],
         "Issue shelter and NFI to Lokichoggio flood response"),
        ("Material Issue", _wh("LOKADO Main Warehouse - Lodwar"), None,
         add_days(td, -3), [("COOKING-POT-SET", 150)],
         "Issue USAID household cooking pots to flood response"),
        ("Material Issue", _wh("LOKADO Main Warehouse - Lodwar"), None,
         add_days(td, -2), [("SCHOOL-DESK", 100)],
         "Issue to 5 primary schools in Turkana West"),
        ("Material Issue", _wh("Cold Chain Storage - Lodwar"), None,
         add_days(td, -2), [("SOLAR-LANTERN", 100)],
         "Issue Japan classroom solar lanterns to Turkana schools"),
        ("Material Issue", _wh("IOM Supported Warehouse - Kakuma"), None,
         add_days(td, -2), [("JERRY-CAN-20L", 1000), ("TIMBER-POLE", 150)],
         "Issue to Kakuma host community WASH and school project"),
        ("Material Issue", _wh("Cold Chain Storage - Lodwar"), None,
         add_days(td, -1), [("DELIVERY-KIT", 125), ("SURGICAL-GLOVES", 100)],
         "Issue to mobile clinic cold chain replenishment"),
        ("Material Issue", _wh("LOKADO Transit Store - Kitale"), None,
         add_days(td, -1), [("FISHING-NET", 60), ("SORGHUM-SEEDS", 250)],
         "Issue to 6 fisheries cooperatives and 250 farmer groups"),
        ("Material Receipt", None, _wh("LOKADO Field Store - Oropoi"),
         add_days(td, -3), [("CHICKEN-INDIG", 200), ("ANIMAL-FEED", 40)],
         "Receive poultry restocking from Nadirkonyen Women's Group"),
        ("Material Receipt", None, _wh("Cold Chain Storage - Lodwar"),
         add_days(td, -2), [("DELIVERY-KIT", 100), ("MOSQUITO-NET", 300)],
         "Receive Japan MNCH and malaria supplies"),
        ("Material Issue", _wh("LOKADO Field Store - Oropoi"), None,
         add_days(td, -1), [("CHICKEN-INDIG", 100)],
         "Issue to Kalobeyei poultry livelihoods project"),
    ]
    for etype, fwh, twh, pdate, items, purpose in entries:
        existing = frappe.db.get_value(
            "Stock Entry",
            {"stock_entry_type": etype, "remarks": purpose, "docstatus": ("<", 2)},
            ["name", "docstatus"], as_dict=True,
        )
        if existing and existing.docstatus == 1:
            continue
        try:
            if existing:
                se = frappe.get_doc("Stock Entry", existing.name)
            else:
                se = frappe.get_doc({
                    "doctype": "Stock Entry", "stock_entry_type": etype,
                    "posting_date": str(pdate), "set_posting_time": 1,
                    "remarks": purpose,
                    "from_warehouse": fwh or "", "to_warehouse": twh or "",
                })
                for ic, qty in items:
                    row = {"item_code": ic, "qty": qty,
                           "s_warehouse": fwh or "", "t_warehouse": twh or ""}
                    if etype == "Material Receipt":
                        row["basic_rate"] = STOCK_RECEIPT_RATES[ic]
                    se.append("items", row)
                se.insert(ignore_permissions=True)
            se.submit()
            frappe.db.commit()
            print(f"  StockEntry [{etype}]: {', '.join(f'{i[0]}x{i[1]}' for i in items)}")
        except Exception:
            frappe.db.rollback()
            raise
    frappe.db.commit()

    # Cross-donor movements must go through an approved Inter Donor Transfer;
    # completing the transfer creates the linked Stock Entry (the production path).
    completed_transfers = [
        (_wh("LOKADO Main Warehouse - Lodwar"), _wh("LOKADO Transit Store - Kitale"),
         "USAID", "EU", [("VET-KIT", 5), ("ANIMAL-FEED", 10)],
         "DEMO-COMPLETED: Vet supplies lent to EU programme at Kitale, donor consent on file."),
        (_wh("IOM Supported Warehouse - Kakuma"), _wh("LOKADO Field Store - Lokichoggio"),
         "IOM", "CONCERN", [("WATER-TANK-10K", 2)],
         "DEMO-COMPLETED: Emergency water tanks for Lokichoggio flood response."),
(_wh("Cold Chain Storage - Lodwar"), _wh("LOKADO Field Store - Oropoi"),
         "JAPAN", "LOKADO-OWN", [("FIRST-AID-KIT", 20), ("DELIVERY-KIT", 30)],
         "DEMO-COMPLETED: Medical supplies for LOKADO staff clinic at Oropoi field office."),
        (_wh("LOKADO Main Warehouse - Lodwar"), _wh("IOM Supported Warehouse - Kakuma"),
         "USAID", "IOM", [("SCHOOL-DESK", 25), ("STATIONERY-KIT", 50)],
         "DEMO-COMPLETED: School furniture loan to IOM Kakuma education project."),
        (_wh("LOKADO Transit Store - Kitale"), _wh("LOKADO Field Store - Lokichoggio"),
         "EU", "CONCERN", [("TARPAULIN-4X6", 100)],
         "DEMO-COMPLETED: Tarpaulins reallocated from EU to Concern flood response."),
        (_wh("LOKADO Field Store - Lokichoggio"), _wh("LOKADO Main Warehouse - Lodwar"),
         "CONCERN", "USAID", [("MOSQUITO-NET", 100)],
         "DEMO-COMPLETED: Malaria nets shared with USAID maternal health programme."),
    ]
    for fwh, twh, from_code, to_code, items, reason in completed_transfers:
        name = frappe.db.get_value("Inter Donor Transfer", {"reason": reason}, "name")
        if name and frappe.db.get_value("Inter Donor Transfer", name, "status") == "Completed":
            continue
        try:
            if name:
                idt = frappe.get_doc("Inter Donor Transfer", name)
            else:
                idt = frappe.get_doc({
                    "doctype": "Inter Donor Transfer",
                    "from_warehouse": fwh, "to_warehouse": twh,
                    "status": "Pending Approval",
                    "transfer_date": str(add_days(td, -1)),
                    "reason": reason,
                    "items": [{"item_code": ic, "qty": qty,
                               "uom": frappe.db.get_value("Item", ic, "stock_uom")}
                              for ic, qty in items],
                })
                idt.insert(ignore_permissions=True)
            if idt.status == "Pending Approval":
                idt.approve()
            idt.complete()
            frappe.db.commit()
            print(f"  InterDonorTransfer: {from_code} -> {to_code} completed with linked Stock Entry")
        except Exception:
            frappe.db.rollback()
            raise
    frappe.db.commit()
    print(f"  Stock Entries: {len(entries)} direct receipts/issues + {len(completed_transfers)} governed transfers")


# ─────────────────────────────────────────────────
# 12. BATCH TRACKING — Batches with expiry dates
# ─────────────────────────────────────────────────

def _seed_batch_tracking():
    """Batch records with manufacture/expiry for LO3."""
    # Batch tracking is set when items are created; it must never be flipped after
    # stock transactions exist (ERPNext forbids it). Inspection is a plain flag.
    for item_code in frappe.get_all(
        "Item",
        filters={
            "is_stock_item": 1,
            "inspection_required_before_purchase": 0,
            "item_code": ("not in", ["FUEL-DIESEL", "LAPTOP-DELL"]),
            "ugavi_fleet_category": ("is", "not set"),
        },
        pluck="name",
    ):
        frappe.db.set_value("Item", item_code, "inspection_required_before_purchase", 1)
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
        ("TARPAULIN-4X6", "BAT-2025-CONC-TARP", add_days(td, -14), add_days(td, 540),
         "Kalobeyei Refugee Supplies Ltd"),
        ("SCHOOL-DESK", "BAT-2025-USA-DESK", add_days(td, -12), add_days(td, 1825),
         "Lorugum Welding & Fabrication"),
        ("SURGICAL-GLOVES", "BAT-2025-JPN-GLOVES", add_days(td, -10), add_days(td, 365),
         "Lodwar Pharmaceuticals Ltd"),
        ("BLANKET-FLEECE", "BAT-2025-OWN-BLANK", add_days(td, -9), add_days(td, 540),
         "Turkana Women's Handicrafts Cooperative"),
        ("FISHING-NET", "BAT-2025-EU-NET", add_days(td, -8), add_days(td, 540),
         "Lake Turkana Fishermen's Cooperative"),
        ("SOLAR-LANTERN", "BAT-2025-JPN-LANTERN", add_days(td, -7), add_days(td, 365),
         "Northern Kenya Solar Ltd"),
        ("SORGHUM-SEEDS", "BAT-2025-EU-SORGHUM", add_days(td, -6), add_days(td, 90),
         "Kainuk Agro-Vet Supplies"),
        ("MOSQUITO-NET", "BAT-2025-CONC-MOSQ", add_days(td, -5), add_days(td, 365),
         "Lodwar Pharmaceuticals Ltd"),
        ("JERRY-CAN-20L", "BAT-2025-IOM-JERRY", add_days(td, -4), add_days(td, 1825),
         "Lokichoggio Traders Ltd"),
        ("CHICKEN-INDIG", "BAT-2025-USAID-CHICK", add_days(td, -3), add_days(td, 540),
         "Nadirkonyen Women's Group"),
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
    print("  Batch Tracking: 20 batches across 18 items")


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
        ("LOKADO Field Store - Lokichoggio", "TARPAULIN-4X6", 100, 800),
        ("LOKADO Main Warehouse - Lodwar", "SCHOOL-DESK", 50, 300),
        ("LOKADO Field Store - Lokichoggio", "BLANKET-FLEECE", 50, 400),
        ("Cold Chain Storage - Lodwar", "SURGICAL-GLOVES", 50, 300),
        ("Cold Chain Storage - Lodwar", "DELIVERY-KIT", 30, 200),
        ("IOM Supported Warehouse - Kakuma", "TIMBER-POLE", 50, 400),
        ("IOM Supported Warehouse - Kakuma", "JERRY-CAN-20L", 500, 3000),
        ("LOKADO Transit Store - Kitale", "FISHING-NET", 30, 200),
        ("Cold Chain Storage - Lodwar", "SOLAR-LANTERN", 40, 300),
        ("LOKADO Transit Store - Kitale", "SORGHUM-SEEDS", 100, 500),
        ("LOKADO Field Store - Lokichoggio", "MOSQUITO-NET", 200, 800),
        ("LOKADO Field Store - Oropoi", "CHICKEN-INDIG", 50, 300),
        ("Cold Chain Storage - Lodwar", "MOSQUITO-NET", 50, 300),
        ("Cold Chain Storage - Lodwar", "ORS-SACHET", 100, 500),
        ("LOKADO Main Warehouse - Lodwar", "STATIONERY-KIT", 100, 500),
        ("LOKADO Main Warehouse - Lodwar", "COOKING-POT-SET", 50, 400),
    ]
    for wh_name, item_code, min_stock, max_stock in reorder_data:
        wh_full = _wh(wh_name)
        if frappe.db.exists(
            "Item Reorder",
            {"parenttype": "Item", "parent": item_code, "warehouse": wh_full,
             "material_request_type": "Purchase"},
        ):
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
    print("  Reorder Levels: 30 items across 6 warehouses")


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
                (_wh("LOKADO Field Store - Lokichoggio"), "Submitted", add_days(td, -2),
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
(_wh("LOKADO Main Warehouse - Lodwar"), "Submitted", add_days(td, -2),
         [("TARPAULIN-4X6", 100), ("BLANKET-FLEECE", 80)],
         "Shelter: emergency NFI for Lokichoggio flood camp"),
        (_wh("LOKADO Main Warehouse - Lodwar"), "Draft", add_days(td, -1),
         [("SCHOOL-DESK", 50), ("STATIONERY-KIT", 40)],
         "Education: classroom materials for Kakuma host schools"),
        (_wh("Cold Chain Storage - Lodwar"), "Draft", add_days(td, -1),
         [("SOLAR-LANTERN", 40)], "Japan education: classroom solar lanterns"),
        (_wh("Cold Chain Storage - Lodwar"), "Submitted", add_days(td, 0),
         [("DELIVERY-KIT", 30), ("SURGICAL-GLOVES", 50)],
         "MNCH: delivery supplies for mobile clinic outreach"),
        (_wh("IOM Supported Warehouse - Kakuma"), "Approved", add_days(td, -1),
         [("JERRY-CAN-20L", 500)],
         "WASH: cholera prevention supplies for Kakuma camp"),
        (_wh("LOKADO Field Store - Lokichoggio"), "Draft", add_days(td, 0),
         [("MOSQUITO-NET", 200), ("BLANKET-FLEECE", 50)],
         "Health: malaria nets and NFI for Kerio ward"),
        (_wh("LOKADO Transit Store - Kitale"), "Submitted", add_days(td, -1),
         [("FISHING-NET", 30), ("SORGHUM-SEEDS", 100)],
         "Livelihoods: fishing gear and seeds for 6 co-ops"),
        (_wh("IOM Supported Warehouse - Kakuma"), "Draft", add_days(td, -1),
         [("TIMBER-POLE", 80)],
         "Construction: materials for 2 classroom block repair"),
        (_wh("Cold Chain Storage - Lodwar"), "Submitted", add_days(td, 0),
         [("MOSQUITO-NET", 100), ("FIRST-AID-KIT", 25)],
         "Health: combined malaria and first aid supplies"),
        (_wh("LOKADO Field Store - Oropoi"), "Draft", add_days(td, 0),
         [("CHICKEN-INDIG", 80), ("ANIMAL-FEED", 15)],
         "Livelihoods: poultry restocking Oropoi women groups"),
        (_wh("LOKADO Main Warehouse - Lodwar"), "Submitted", add_days(td, -2),
         [("STATIONERY-KIT", 100)],
         "Admin: IT and stationery for programme field offices"),
        (_wh("LOKADO Field Store - Oropoi"), "Draft", add_days(td, -2),
         [("LAPTOP-DELL", 5)], "Own funds: IT equipment for programme field offices"),
    ]
    submitted = 0
    for wh_full, status, sched, items, purpose in mr_data:
        title = purpose[:140]
        existing = frappe.db.get_value(
            "Material Request", {"title": title, "docstatus": ("<", 2)},
            ["name", "docstatus"], as_dict=True,
        )
        if existing and (existing.docstatus == 1 or status == "Draft"):
            submitted += existing.docstatus
            continue
        try:
            if existing:
                mr = frappe.get_doc("Material Request", existing.name)
            else:
                mr = frappe.get_doc({
                    "doctype": "Material Request",
                    "material_request_type": "Material Issue",
                    "transaction_date": str(add_days(sched, -2)),
                    "schedule_date": str(sched), "set_warehouse": wh_full,
                    "title": title,
                })
                for ic, qty in items:
                    mr.append("items", {"item_code": ic, "qty": qty,
                        "uom": frappe.db.get_value("Item", ic, "stock_uom"),
                        "warehouse": wh_full, "schedule_date": str(sched)})
                mr.insert(ignore_permissions=True)
            if status != "Draft":
                mr.submit()
                submitted += 1
            frappe.db.commit()
            print(f"  MaterialReq [{status}]: {', '.join(f'{i[0]}x{i[1]}' for i in items)}")
        except Exception as e:
            frappe.db.rollback()
            print(f"  MaterialReq FAILED — {type(e).__name__}: {e}")
    print(f"  Material Requests: {len(mr_data)} requests ({submitted} submitted, rest draft)")


# ─────────────────────────────────────────────────
# 15. PURCHASE INVOICES — For three-way match (PR9)
# ─────────────────────────────────────────────────

LOKADO_COMPANY = "Lotus Kenya Action for Development Organization"


def _logistics_receipt(supplier_name, warehouse_name):
    """The stock receipt created by _seed_logistics for a supplier and warehouse."""
    supplier = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
    warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": warehouse_name}, "name")
    if not supplier or not warehouse:
        return None
    return frappe.db.get_value(
        "Purchase Receipt",
        {"supplier": supplier, "set_warehouse": warehouse, "docstatus": 1},
        "name",
    )


# Supplier invoice number, receipt (supplier, warehouse), payment share, payment mode
RECEIPT_INVOICES = [
    ("LOK-INV-LGT-POTS", "Lokichar General Traders", "LOKADO Main Warehouse - Lodwar", 0.5, "Bank Transfer"),
    ("LOK-INV-KRS-EU", "Kalobeyei Refugee Supplies Ltd", "LOKADO Transit Store - Kitale", 1.0, "Bank Transfer"),
    ("LOK-INV-TCL-0412", "Turkana Construction Ltd", "IOM Supported Warehouse - Kakuma", 0.6, "Bank Transfer"),
    ("LOK-INV-NWG-0088", "Nadirkonyen Women's Group", "LOKADO Main Warehouse - Lodwar", 1.0, "Mobile Money"),
    ("LOK-INV-LGS-1190", "Lodwar General Supplies", "IOM Supported Warehouse - Kakuma", 0.0, None),
    ("LOK-INV-KRC-2207", "Kenya Red Cross Supplies", "LOKADO Field Store - Lokichoggio", 1.0, "Cheque"),
    ("LOK-INV-RVH-0731", "Rift Valley Hardware", "IOM Supported Warehouse - Kakuma", 1.0, "Bank Transfer"),
    ("LOK-INV-JOP-0056", "Jopeji Enterprises", "LOKADO Transit Store - Kitale", 0.5, "Bank Transfer"),
    ("LOK-INV-KRS-3101", "Kalobeyei Refugee Supplies Ltd", "LOKADO Field Store - Lokichoggio", 0.7, "Bank Transfer"),
    ("LOK-INV-LWF-0220", "Lorugum Welding & Fabrication", "LOKADO Main Warehouse - Lodwar", 1.0, "Mobile Money"),
    ("LOK-INV-LPH-1405", "Lodwar Pharmaceuticals Ltd", "Cold Chain Storage - Lodwar", 1.0, "Bank Transfer"),
    ("LOK-INV-LKH-0755", "Lokitaung Hardware & Building", "IOM Supported Warehouse - Kakuma", 0.5, "Cheque"),
    ("LOK-INV-NKS-0922", "Northern Kenya Solar Ltd", "Cold Chain Storage - Lodwar", 1.0, "Bank Transfer"),
    ("LOK-INV-LTF-0603", "Lake Turkana Fishermen's Cooperative", "LOKADO Transit Store - Kitale", 0.8, "Mobile Money"),
    ("LOK-INV-KAV-0150", "Kainuk Agro-Vet Supplies", "LOKADO Transit Store - Kitale", 1.0, "Cheque"),
    ("LOK-INV-LPH-1406", "Lodwar Pharmaceuticals Ltd", "LOKADO Field Store - Lokichoggio", 0.5, "Bank Transfer"),
    ("LOK-INV-LGT-2301", "Lokichar General Traders", "LOKADO Field Store - Oropoi", 0.0, None),
    ("LOK-INV-KST-1804", "Kakuma Stationers & Supplies", "LOKADO Main Warehouse - Lodwar", 0.6, "Bank Transfer"),
    ("LOK-INV-TWL-1120", "Turkwel Renewable Energy", "Cold Chain Storage - Lodwar", 1.0, "Bank Transfer"),
    ("LOK-INV-OPT-0330", "Turkana Women's Handicrafts Cooperative", "LOKADO Field Store - Oropoi", 0.0, None),
    ("LOK-INV-LKH-0756", "Lokitaung Hardware & Building", "LOKADO Main Warehouse - Lodwar", 0.7, "Bank Transfer"),
    ("LOK-INV-LTW-0425", "Lake Turkana Water Services", "IOM Supported Warehouse - Kakuma", 1.0, "Cheque"),
]


def _seed_purchase_invoices():
    """Receipt-linked Purchase Invoices; submit triggers the Ugavi Three-Way Match record."""
    from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

    submitted = 0
    for bill_no, supplier_name, warehouse_name, _share, _mode in RECEIPT_INVOICES:
        existing = frappe.db.get_value(
            "Purchase Invoice", {"bill_no": bill_no, "docstatus": ("<", 2)},
            ["name", "docstatus"], as_dict=True,
        )
        if existing and existing.docstatus == 1:
            submitted += 1
            continue
        receipt = _logistics_receipt(supplier_name, warehouse_name)
        if not receipt:
            print(f"  PurchaseInvoice: {bill_no} has no submitted receipt to bill")
            continue
        try:
            if existing:
                invoice = frappe.get_doc("Purchase Invoice", existing.name)
            else:
                receipt_date = frappe.db.get_value("Purchase Receipt", receipt, "posting_date")
                invoice = make_purchase_invoice(receipt)
                invoice.bill_no = bill_no
                invoice.bill_date = str(add_days(receipt_date, 2))
                invoice.set_posting_time = 1
                invoice.posting_date = str(add_days(receipt_date, 2))
                invoice.due_date = str(add_days(receipt_date, 32))
                invoice.payment_schedule = []
                invoice.remarks = f"Supplier invoice {bill_no} against {receipt}"
                invoice.insert(ignore_permissions=True)
            invoice.submit()
            frappe.db.commit()
            submitted += 1
            print(f"  PurchaseInvoice: {bill_no} ← {receipt} → {invoice.grand_total:,.0f} KES")
        except Exception as e:
            frappe.db.rollback()
            print(f"  PurchaseInvoice: {bill_no} FAILED — {type(e).__name__}: {e}")
    print(f"  Purchase Invoices: {submitted}/{len(RECEIPT_INVOICES)} receipt-linked invoices submitted")


# ─────────────────────────────────────────────────
# 16. PAYMENT ENTRIES — Payments against invoices
# ─────────────────────────────────────────────────

def _seed_payment_entries():
    """Full and partial payments allocated to invoices, passing the evaluation gate."""
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

    td = today()
    paid = 0
    for index, (bill_no, supplier_name, _wh, share, mode) in enumerate(RECEIPT_INVOICES):
        if not share:
            continue
        reference_no = f"PAY-{bill_no}"
        if frappe.db.exists("Payment Entry", {"reference_no": reference_no, "docstatus": 1}):
            paid += 1
            continue
        invoice = frappe.db.get_value(
            "Purchase Invoice", {"bill_no": bill_no, "docstatus": 1},
            ["name", "outstanding_amount", "posting_date"], as_dict=True,
        )
        if not invoice or not invoice.outstanding_amount:
            print(f"  Payment: {bill_no} has no outstanding submitted invoice")
            continue
        try:
            draft = frappe.db.get_value(
                "Payment Entry", {"reference_no": reference_no, "docstatus": 0}, "name"
            )
            if draft:
                payment = frappe.get_doc("Payment Entry", draft)
            else:
                amount = round(invoice.outstanding_amount * share, 2)
                payment = get_payment_entry(
                    "Purchase Invoice", invoice.name, party_amount=amount
                )
                payment.mode_of_payment = mode
                payment.paid_from = "Cash - LOKADO"
                payment.posting_date = str(add_days(invoice.posting_date, 1))
                payment.reference_no = reference_no
                payment.reference_date = payment.posting_date
                payment.remarks = (
                    f"{'Full' if share == 1 else f'Partial ({int(share * 100)}%)'} "
                    f"payment of {bill_no} via {mode}"
                )
                payment.insert(ignore_permissions=True)
            payment.submit()
            frappe.db.commit()
            paid += 1
            print(f"  Payment: {bill_no} → {payment.paid_amount:,.0f} KES [{mode}]")
        except Exception:
            frappe.db.rollback()
            raise
    print(f"  Payment Entries: {paid} submitted (full, partial; one invoice left outstanding)")


# ─────────────────────────────────────────────────
# 17. LANDED COST VOUCHERS — Transport/import costs
# ─────────────────────────────────────────────────

def _seed_landed_cost_vouchers():
    """Submitted Landed Cost Vouchers that capitalise freight into receipt valuation."""
    costs = [
        ("Turkana Construction Ltd", "IOM Supported Warehouse - Kakuma",
         [("Transport: cement + tanks Lodwar to Kakuma", 85000)]),
        ("Nadirkonyen Women's Group", "LOKADO Main Warehouse - Lodwar",
         [("Livestock transport Nadirkonyen to Lodwar", 35000),
          ("Veterinary movement permit and clearance", 12000)]),
        ("Jopeji Enterprises", "LOKADO Transit Store - Kitale",
         [("Motorcycles Nairobi to Kitale transit", 28000),
          ("Warehouse handling and assembly", 15000)]),
        ("Rift Valley Hardware", "IOM Supported Warehouse - Kakuma",
         [("Transport: pipes Eldoret to Kakuma", 42000)]),
        ("Kalobeyei Refugee Supplies Ltd", "LOKADO Field Store - Lokichoggio",
         [("Emergency shelter freight to Lokichoggio", 65000),
          ("Warehouse handling and fumigation", 18000)]),
        ("Lorugum Welding & Fabrication", "LOKADO Main Warehouse - Lodwar",
         [("Transport: desks Lorugum to Lodwar", 22000)]),
        ("Lodwar Pharmaceuticals Ltd", "Cold Chain Storage - Lodwar",
         [("Cold-chain transport Nairobi to Lodwar", 48000),
          ("Temperature monitoring and certification", 15000)]),
        ("Lake Turkana Fishermen's Cooperative", "LOKADO Transit Store - Kitale",
         [("Transport: nets from Kalokol to Kitale", 18000),
          ("Marine equipment handling", 8000)]),
    ]
    vouchers = 0
    for supplier_name, warehouse_name, charges in costs:
        receipt = _logistics_receipt(supplier_name, warehouse_name)
        if not receipt:
            print(f"  LandedCost: {supplier_name[:25]} has no submitted receipt")
            continue
        existing = frappe.db.get_value(
            "Landed Cost Purchase Receipt",
            {"parenttype": "Landed Cost Voucher", "receipt_document": receipt},
            "parent",
        )
        if existing and frappe.db.get_value("Landed Cost Voucher", existing, "docstatus") == 1:
            vouchers += 1
            continue
        try:
            if existing:
                lcv = frappe.get_doc("Landed Cost Voucher", existing)
            else:
                lcv = frappe.get_doc({
                    "doctype": "Landed Cost Voucher",
                    "company": LOKADO_COMPANY,
                    "distribute_charges_based_on": "Amount",
                })
                lcv.append("purchase_receipts", {
                    "receipt_document_type": "Purchase Receipt",
                    "receipt_document": receipt,
                    "supplier": frappe.db.get_value("Purchase Receipt", receipt, "supplier"),
                    "posting_date": frappe.db.get_value("Purchase Receipt", receipt, "posting_date"),
                })
                lcv.get_items_from_purchase_receipts()
                for description, amount in charges:
                    lcv.append("taxes", {
                        "description": description,
                        "amount": amount,
                        "expense_account": "Freight and Forwarding Charges - LOKADO",
                    })
                lcv.insert(ignore_permissions=True)
            lcv.submit()
            frappe.db.commit()
            vouchers += 1
            print(f"  LandedCost: {receipt} + {sum(a for _, a in charges):,} KES freight/handling")
        except Exception:
            frappe.db.rollback()
            raise
    print(f"  Landed Cost Vouchers: {vouchers}/{len(costs)} submitted")


# ─────────────────────────────────────────────────
# 18. BUDGET RECORDS — Donor budget control (ERPNext v16 Budget)
# ─────────────────────────────────────────────────

def _seed_budget_records():
    """Donor-dimension budgets: one Budget per donor and expense account (v16 schema)."""
    fiscal_year = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": ("<=", today()), "year_end_date": (">=", today()), "disabled": 0},
        "name",
    )
    if not fiscal_year:
        print("  Budget: no active fiscal year covering today")
        return
    budgets = [
        ("IOM", "Freight and Forwarding Charges - LOKADO", 1150000),
        ("IOM", "Administrative Expenses - LOKADO", 600000),
        ("USAID", "Travel Expenses - LOKADO", 750000),
        ("USAID", "Miscellaneous Expenses - LOKADO", 400000),
        ("EU", "Travel Expenses - LOKADO", 600000),
        ("CONCERN", "Administrative Expenses - LOKADO", 1200000),
        ("JAPAN", "Miscellaneous Expenses - LOKADO", 500000),
        ("LOKADO-OWN", "Administrative Expenses - LOKADO", 250000),
        ("EU", "Freight and Forwarding Charges - LOKADO", 750000),
        ("CONCERN", "Freight and Forwarding Charges - LOKADO", 1000000),
    ]
    created = 0
    for donor_code, account, amount in budgets:
        donor = frappe.db.get_value("Donor Profile", {"donor_code": donor_code}, "name")
        if not donor:
            continue
        key = {
            "budget_against": "Donor Profile", "donor_profile": donor,
            "account": account, "from_fiscal_year": fiscal_year, "docstatus": ("<", 2),
        }
        existing = frappe.db.get_value("Budget", key, ["name", "docstatus"], as_dict=True)
        if existing and existing.docstatus == 1:
            created += 1
            continue
        try:
            if existing:
                budget = frappe.get_doc("Budget", existing.name)
            else:
                budget = frappe.get_doc({
                    "doctype": "Budget",
                    "company": LOKADO_COMPANY,
                    "budget_against": "Donor Profile",
                    "donor_profile": donor,
                    "account": account,
                    "from_fiscal_year": fiscal_year,
                    "to_fiscal_year": fiscal_year,
                    "budget_amount": amount,
                    "distribution_frequency": "Quarterly",
                    "distribute_equally": 1,
                    "applicable_on_purchase_order": 1,
                    "action_if_annual_budget_exceeded_on_po": "Warn",
                    "action_if_accumulated_monthly_budget_exceeded_on_po": "Warn",
                    "applicable_on_booking_actual_expenses": 1,
                    "action_if_annual_budget_exceeded": "Warn",
                    "action_if_accumulated_monthly_budget_exceeded": "Warn",
                })
                budget.insert(ignore_permissions=True)
            budget.submit()
            frappe.db.commit()
            created += 1
            print(f"  Budget: {donor_code} / {account} → {amount:,} KES ({fiscal_year})")
        except Exception:
            frappe.db.rollback()
            raise
    print(f"  Budget Records: {created}/{len(budgets)} donor budgets submitted")


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
# 20. PROGRAMMES & GRANTS — Donor-funded projects with grant allocations (NP3)
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
         [("GOAT-GALLA", 100, 3650)],
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
        ("Jopeji Enterprises", add_days(td, -5), add_days(td, 25),
         [("MOTORCYCLE-FIELD", 4, 127500)],
         "LPO: field motorcycles - USAID peace building"),
        ("Kalobeyei Refugee Supplies Ltd", add_days(td, -4), add_days(td, 45),
         [("TARPAULIN-4X6", 800, 650)],
         "LPO: emergency shelter tarpaulins - Concern"),
        ("Lorugum Welding & Fabrication", add_days(td, -4), add_days(td, 90),
         [("SCHOOL-DESK", 200, 2000)],
         "LPO: classroom desks - USAID education"),
        ("Lodwar Pharmaceuticals Ltd", add_days(td, -3), add_days(td, 40),
         [("SURGICAL-GLOVES", 200, 800), ("DELIVERY-KIT", 250, 1060)],
         "LPO: medical supplies - Japan MNCH"),
        ("Lokitaung Hardware & Building", add_days(td, -3), add_days(td, 30),
         [("TIMBER-POLE", 300, 583), ("JERRY-CAN-20L", 2000, 85)],
         "LPO: construction + WASH - IOM"),
        ("Northern Kenya Solar Ltd", add_days(td, -2), add_days(td, 45),
         [("SOLAR-LANTERN", 200, 1525)],
         "LPO: solar lanterns - Japan education"),
        ("Lake Turkana Fishermen's Cooperative", add_days(td, -2), add_days(td, 60),
         [("FISHING-NET", 120, 3042)],
         "LPO: fishing equipment - EU livelihoods"),
        ("Kainuk Agro-Vet Supplies", add_days(td, -1), add_days(td, 35),
         [("SORGHUM-SEEDS", 500, 496)],
         "LPO: certified seeds - EU food security"),
        ("Lodwar Pharmaceuticals Ltd", add_days(td, -1), add_days(td, 21),
         [("MOSQUITO-NET", 600, 233), ("ORS-SACHET", 400, 312)],
         "LPO: health supplies - Concern/Japan"),
        ("Eldoret Office Technologies", add_days(td, 0), add_days(td, 14),
         [("LAPTOP-DELL", 5, 97500)],
         "LPO: programme laptops - LOKADO admin"),
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
    print("  Purchase Orders: 15 co-signed LPOs (PR8)")


# ─────────────────────────────────────────────────
# 22. FINAL — Commit all changes
# ─────────────────────────────────────────────────