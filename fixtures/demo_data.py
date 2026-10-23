"""Fixtures - demo data for Ugavi."""
import frappe
from frappe.utils import today, add_days


def run():
    try: _seed_roles()
    except Exception as e: print(f"Roles: {e}")
    try: _seed_users()
    except Exception as e: print(f"Users: {e}")
    try: _seed_donors()
    except Exception as e: print(f"Donors: {e}")
    try: _seed_settings()
    except Exception as e: print(f"Settings: {e}")
    try: _seed_uoms()
    except Exception as e: print(f"UOMs: {e}")
    try: _seed_item_groups()
    except Exception as e: print(f"ItemGroups: {e}")
    try: _seed_items()
    except Exception as e: print(f"Items: {e}")
    try: _seed_supplier_groups()
    except Exception as e: print(f"SupplierGroups: {e}")
    try: _seed_suppliers()
    except Exception as e: print(f"Suppliers: {e}")
    try: _seed_vehicles_and_fleet()
    except Exception as e: print(f"Fleet: {e}")
    try: _seed_assets()
    except Exception as e: print(f"Assets: {e}")
    try: _seed_doa()
    except Exception as e: print(f"DoA({type(e).__name__}): {e}")
    try: _seed_threshold_rules()
    except Exception as e: print(f"Thresholds: {e}")
    try: _seed_procurement_workflow()
    except Exception as e: print(f"Procurement: {e}")
    print("\\n=== Seed data complete ===")


def _seed_roles():
    for role in ["Procurement Officer","Approver Level 1","Approver Level 2",
                 "Bid Opening Officer","Evaluation Committee","Fleet Manager",
                 "Asset Manager","Logistics Officer"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype":"Role","role_name":role}).insert()
            print(f"  Role: {role}")


def _seed_users():
    for email, fname, role in [
        ("procurement@ugavi.demo","Procurement Officer","Procurement Officer"),
        ("approver1@ugavi.demo","Approver One","Approver Level 1"),
        ("approver2@ugavi.demo","Approver Two","Approver Level 2"),
        ("opening1@ugavi.demo","Opening Officer A","Bid Opening Officer"),
        ("opening2@ugavi.demo","Opening Officer B","Bid Opening Officer"),
        ("opening3@ugavi.demo","Opening Officer C","Bid Opening Officer"),
        ("logistics@ugavi.demo","Logistics Officer","Logistics Officer"),
        ("fleet@ugavi.demo","Fleet Manager","Fleet Manager"),
        ("assets@ugavi.demo","Asset Manager","Asset Manager")]:
        if not frappe.db.exists("User", email):
            frappe.get_doc({"doctype":"User","email":email,"first_name":fname,
                "roles":[{"role":role}],"send_welcome_email":0}).insert(ignore_permissions=True)
            print(f"  User: {email}")


def _seed_donors():
    for code, name, full, email, desc in [
        ("DON-001","USAID","USAID","usaid@demo.org","Donor-funded health supply chain"),
        ("DON-002","Global Fund","Global Fund","globalfund@demo.org","Health systems"),
        ("DON-003","UNICEF","UNICEF","unicef@demo.org","Maternal and child health"),
        ("DON-004","World Bank","World Bank","wb@demo.org","Infrastructure and health"),
        ("DON-005","DFID","DFID","dfid@demo.org","Health sector support")]:
        # Check by donor_code since autoname is hash-based
        existing_name = frappe.db.get_value("Donor Profile", {"donor_code": code}, "name")
        if not existing_name:
            try:
                frappe.get_doc({"doctype":"Donor Profile","donor_code":code,
                    "donor_name":name,"full_name":full,"contact_email":email,
                    "description":desc,"status":"Active"}).insert(ignore_permissions=True)
                print(f"  Donor: {name}")
            except Exception:
                # Already exists by donor_name
                pass


def _seed_settings():
    if not frappe.db.exists("Ugavi Procurement Settings","Ugavi Procurement Settings"):
        frappe.get_doc({"doctype":"Ugavi Procurement Settings","direct_threshold":200000,
            "restricted_threshold":500000,"default_currency":"KES",
            "auto_close_tenders_days":30,"prequalification_validity_days":365}).insert()
        print("  Settings: Ugavi Procurement")


def _seed_uoms():
    for name in ["30-pack","24-pack","Box of 100","Box of 50","Single vial","Unit"]:
        if not frappe.db.exists("UOM", name):
            frappe.get_doc({"doctype":"UOM","uom_name":name}).insert()
            print(f"  UOM: {name}")


def _seed_item_groups():
    for name in ["Drugs","Lab Supplies","Medical Supplies","IT Equipment","Office Equipment","Furniture","Equipment"]:
        if not frappe.db.exists("Item Group", name):
            frappe.get_doc({"doctype":"Item Group","item_group_name":name,"parent_item_group":"All Item Groups"}).insert()
            print(f"  ItemGroup: {name}")


def _seed_items():
    for code, name, uom, group, rate in [
        ("ART-001","ARV Tablet TLD","30-pack","Drugs",450),
        ("ART-002","ARV Tablet ABC/3TC","30-pack","Drugs",380),
        ("MAL-001","ACT Co-blister AL","24-pack","Drugs",120),
        ("MAL-002","Artesunate Injection 60mg","Single vial","Drugs",80),
        ("LAB-001","HIV Rapid Test Kit","Box of 100","Lab Supplies",2500),
        ("LAB-002","Malaria RDT Kit","Box of 100","Lab Supplies",1800),
        ("MED-001","Disposable Gloves","Box of 100","Medical Supplies",350),
        ("MED-002","Surgical Mask N95","Box of 50","Medical Supplies",1200),
        ("NCL-001","Laptop Dell Latitude","Unit","IT Equipment",85000),
        ("NCL-002","Printer/Copier","Unit","Office Equipment",45000),
        ("NCL-003","Office Desk","Unit","Furniture",15000),
        ("NCL-004","Generator 15kVA","Unit","Equipment",320000)]:
        if not frappe.db.exists("Item", code):
            frappe.get_doc({"doctype":"Item","item_code":code,"item_name":name,
                "item_group":group,"stock_uom":uom,"valuation_rate":rate,
                "is_stock_item":1,"is_purchase_item":1,"default_warehouse":"Stores"}).insert()
            print(f"  Item: {code}")


def _seed_supplier_groups():
    for name in ["PHARMACEUTICAL","LAB","IT","OFFICE"]:
        if not frappe.db.exists("Supplier Group", name):
            frappe.get_doc({"doctype":"Supplier Group","supplier_group_name":name}).insert(ignore_permissions=True)
            print(f"  SupplierGroup: {name}")


def _seed_suppliers():
    for code, name, group, email in [
        ("MEDSUPPLY-KE","Medical Supplies Kenya Ltd","PHARMACEUTICAL","mdsupply@demo.co.ke"),
        ("PHARMA-INTL","Pharma International Ltd","PHARMACEUTICAL","pharma@demo.co.ke"),
        ("DIAGNOSTICS-AFRICA","Diagnostics Africa Ltd","LAB","diag@demo.co.ke"),
        ("IT-SOLUTIONS","IT Solutions EA","IT","itsol@demo.co.ke"),
        ("OFFICE-WORLD","Office World Ltd","OFFICE","office@demo.co.ke")]:
        existing = frappe.db.exists("Supplier", {"supplier_name": name})
        if not existing:
            frappe.get_doc({"doctype":"Supplier","supplier_name":name,"supplier_group":group,
                "default_currency":"KES","supplier_email":email,"is_internal_supplier":0}).insert(ignore_permissions=True)
            print(f"  Supplier: {name}")
        else:
            # Ensure supplier_name matches for existing records
            pass


def _seed_vehicles_and_fleet():
    imports_map = {}
    for plate, make, model, chassis, year, fuel, status in [
        ("KCA-001A","Toyota","Land Cruiser Prado","LC-001",2019,"Diesel","Active"),
        ("KCB-002B","Toyota","Hilux Double Cab","HL-002",2020,"Diesel","Active"),
        ("KCC-003C","Nissan","Patrol","NP-003",2018,"Diesel","Active"),
        ("KCD-004D","Mitsubishi","Fuso Canter","FC-004",2021,"Diesel","Under Repair"),
        ("KCE-005E","Toyota","Hiace Van","HV-005",2022,"Petrol","Active")]:
        if not frappe.db.exists("Vehicle",{"license_plate":plate}):
            v = frappe.get_doc({"doctype":"Vehicle","license_plate":plate,
                "vehicle_name":f"{make} {model}","make":make,"model":model,
                "chassis_no":chassis,"year_of_manufacture":year,"fuel_type":fuel,
                "status":status,"insurance_expiry":add_days(today(),180)}).insert()
            imports_map[plate] = v.name
            print(f"  Vehicle: {v.name}")
        else:
            imports_map[plate] = frappe.db.get_value("Vehicle",{"license_plate":plate},"name")
    # Allocations (idempotent: skip if already have allocations)
    try:
        if frappe.db.count("Vehicle Allocation") >= 4:
            print("  Fleet: already seeded (allocations), skipping rest")
            return
    except Exception:
        pass
    for vehicle, user, start, end, purpose in [
        ("KCA-001A","approver1@ugavi.demo",add_days(today(),-30),add_days(today(),60),"Field visits"),
        ("KCB-002B","logistics@ugavi.demo",add_days(today(),-15),add_days(today(),45),"Procurement"),
        ("KCC-003C","procurement@ugavi.demo",add_days(today(),-10),add_days(today(),90),"Project visits"),
        ("KCE-005E","opening1@ugavi.demo",add_days(today(),-5),add_days(today(),30),"Inspections")]:
        an = f"{imports_map[vehicle]}-{start}"
        if not frappe.db.exists("Vehicle Allocation",an):
            frappe.get_doc({"doctype":"Vehicle Allocation","vehicle":imports_map[vehicle],
                "allocated_to":user,"start_date":start,"allocation_end":end,"purpose":purpose}).insert()
            print(f"  Allocation: {imports_map[vehicle]}")
    # Fuel logs
    for vehicle, date, amount, litres, station in [
        ("KCA-001A",today(),4500,25.5,"Shell Kilimani"),
        ("KCB-002B",add_days(today(),-5),3800,22,"Total Westlands"),
        ("KCC-003C",add_days(today(),-3),5200,30,"Shell Mombasa")]:
        fn = f"{imports_map[vehicle]}-{date}"
        if not frappe.db.exists("Fuel Log",fn):
            frappe.get_doc({"doctype":"Fuel Log","vehicle":imports_map[vehicle],
                "date":date,"fuel_cost":amount,"fuel_quantity":litres,
                "fuel_station":station,"fuel_type":"Diesel"}).insert()
            print(f"  Fuel: {imports_map[vehicle]}")
    # Trip logs
    for vehicle, date, dist, hours, route, purpose in [
        ("KCA-001A",today(),120,3.5,"Nairobi-Machakos","Field Visit"),
        ("KCB-002B",add_days(today(),-2),45,1.5,"Nairobi CBD","Procurement"),
        ("KCC-003C",add_days(today(),-1),85,2,"Site inspection","Project")]:
        tn = f"{imports_map[vehicle]}-{date}"
        if not frappe.db.exists("Trip Log",tn):
            frappe.get_doc({"doctype":"Trip Log","vehicle":imports_map[vehicle],
                "start_date":date,"distance_km":dist,"duration_hours":hours,
                "route":route,"purpose":purpose}).insert()
            print(f"  Trip: {imports_map[vehicle]}")


def _seed_assets():
    # Quick check if assets already seeded
    if frappe.db.count("Asset Register") >= 5:
        print("  Assets: already seeded, skipping")
        return
    for code, name, category, value, date, location, dept, life in [
        ("AST-001","Server Dell PowerEdge","IT Equipment",450000,today(),"Head Office","IT",5),
        ("AST-002","Generator 100kVA Cummins","Equipment",1200000,add_days(today(),-365),"Warehouse 1","Facilities",10),
        ("AST-003","Cold Chain Refrigerator","Equipment",350000,add_days(today(),-180),"Clinic A","Health",7),
        ("AST-004","Solar Array 10kW","Equipment",650000,add_days(today(),-90),"Field Office","Energy",15),
        ("AST-005","Microscope Olympus CX23","Equipment",85000,add_days(today(),-30),"Lab","Health",5)]:
        if not frappe.db.exists("Asset Register",{"asset_code": code}):
            a = frappe.get_doc({"doctype":"Asset Register","asset_code":code,
                "asset_name":name,"asset_category":category,"purchase_value":value,
                "acquisition_date":date,"current_location":location,
                "custodian_department":dept,"useful_life_years":life,"status":"Active"}).insert()
            print(f"  Asset: {a.name}")
    # Skip movements (needs valid warehouse)
    # Skip disposal


def _seed_doa():
    """Delegation of Authority: amount-based approval thresholds per donor/department."""
    # Resolve donor names
    donor_map = {}
    for d in frappe.get_all("Donor Profile", fields=["name", "donor_name"]):
        donor_map[d.donor_name] = d.name
    for dn in ["USAID", "Global Fund", "UNICEF"]:
        if dn not in donor_map:
            donor_map[dn] = dn

    # Skip if already seeded
    try:
        if frappe.db.count("Delegation of Authority") >= 3:
            print("  DoA: already seeded, skipping")
            return
    except Exception:
        pass

    rules = [
        # (dept, donor, min, max, level, role, eff_from, eff_to)
        ("Operations - OT", "USAID", 0, 500000, 1, "Approver Level 1",
         add_days(today(), -180), add_days(today(), 365)),
        ("Operations - OT", "USAID", 500001, 5000000, 2, "Approver Level 2",
         add_days(today(), -180), add_days(today(), 365)),
        ("Operations - OT", "Global Fund", 0, 300000, 1, "Approver Level 1",
         add_days(today(), -180), add_days(today(), 365)),
        ("Operations - OT", "Global Fund", 300001, 3000000, 2, "Approver Level 2",
         add_days(today(), -180), add_days(today(), 365)),
        ("Purchase - OT", None, 0, 1000000, 1, "Approver Level 1",
         add_days(today(), -90), None),
    ]
    for dept, donor, min_amt, max_amt, level, role, eff_from, eff_to in rules:
        name = f"{dept}-{donor or 'ALL'}-L{level}-{min_amt}"
        if not frappe.db.exists("Delegation of Authority", name):
            doc = {
                "doctype": "Delegation of Authority", "enabled": 1,
                "department": dept, "min_amount": min_amt,
                "approval_level": level, "approver_role": role,
                "effective_from": eff_from,
            }
            if donor: doc["donor"] = donor_map.get(donor, donor)
            if max_amt: doc["max_amount"] = max_amt
            if eff_to: doc["effective_to"] = eff_to
            frappe.get_doc(doc).insert(ignore_permissions=True)
            print(f"  DoA: {dept} | {donor or 'Any'} | L{level} | {min_amt:,}-{max_amt or chr(0x221E)}")

    # Approval Delegations (temporary)
    delegations = [
        ("approver1@ugavi.demo", "approver2@ugavi.demo", "All Procurement",
         0, add_days(today(), 0), add_days(today(), 30), "Annual leave coverage"),
        ("procurement@ugavi.demo", "logistics@ugavi.demo", "Purchase Requisition",
         2000000, add_days(today(), -10), add_days(today(), 20), "Training absence"),
    ]
    for frm, to, dtype, max_amt, start, end, reason in delegations:
        name = f"{frm}-to-{to}-{start}"
        if not frappe.db.exists("Approval Delegation", name):
            frappe.get_doc({
                "doctype": "Approval Delegation", "delegated_from": frm,
                "delegated_to": to, "delegation_type": dtype,
                "max_amount": max_amt, "start_date": start,
                "end_date": end, "active": 1, "reason": reason,
            }).insert(ignore_permissions=True)
            print(f"  Delegation: {frm} -> {to} ({dtype})")


def _seed_threshold_rules():
    """Donor Rules: value thresholds -> procurement method.
    NOTE: Donor Rule is a child table; seed skipped. Use API to add rules to parent."""
    if frappe.get_meta("Donor Rule").istable:
        print("  Thresholds: Donor Rule is child table, skipping")
        return
    rules = [
        ("USAID", 0, 200000, "Request for Quotation (Direct)",
         add_days(today(), -365), None, "Direct procurement below threshold"),
        ("USAID", 200001, 2000000, "Restricted Tender",
         add_days(today(), -365), None, "Restricted tender for mid-range"),
        ("USAID", 2000001, None, "Open Tender",
         add_days(today(), -365), None, "Open tender for large contracts"),
        ("Global Fund", 0, 300000, "Request for Quotation (Direct)",
         add_days(today(), -365), None, "RFQ for small procurements"),
        ("Global Fund", 300001, 3000000, "Restricted Tender",
         add_days(today(), -365), None, "Restricted for mid-range"),
        ("Global Fund", 3000001, None, "Open Tender",
         add_days(today(), -365), None, "Open tender for large contracts"),
        ("UNICEF", 0, 500000, "Restricted Tender",
         add_days(today(), -180), None, "All UNICEF procurement restricted+"),
        ("UNICEF", 500001, None, "Open Tender",
         add_days(today(), -180), None, "Large UNICEF open tender"),
    ]
    for donor, min_v, max_v, method, eff_from, eff_to, notes in rules:
        name = f"{donor}-{min_v}-{method}"
        if not frappe.db.exists("Donor Rule", name):
            doc = {
                "doctype": "Donor Rule", "enabled": 1,
                "min_value": min_v, "procurement_method": method,
                "effective_from": eff_from, "notes": f"[{donor}] {notes}",
            }
            if max_v: doc["max_value"] = max_v
            if eff_to: doc["effective_to"] = eff_to
            frappe.get_doc(doc).insert(ignore_permissions=True)
            print(f"  Threshold: {donor} | {min_v:,}-{max_v or chr(0x221E)} | {method}")


def _seed_procurement_workflow():
    """End-to-end records: PRs -> Tenders -> Contracts -> Scorecards."""
    today_date = today()

    # Resolve donor names to actual DocType names (autoname is hash-based)
    donor_map = {}
    for d in frappe.get_all("Donor Profile", fields=["name", "donor_name"]):
        donor_map[d.donor_name] = d.name
    # Fallback: if donor_name matches, use it directly
    for dn in ["USAID", "Global Fund", "UNICEF"]:
        if dn not in donor_map:
            donor_map[dn] = dn

    # -- Purchase Requisitions with items --
    for pr_name, requester, dept, donor, est_val, method, justification, items in [
        ("PR-2026-001", "procurement@ugavi.demo", "Operations - OT", "USAID", 1250000,
         "Restricted Tender", "Quarterly ARV drug replenishment for 5 hospitals",
         [("ART-001", 200, "30-pack", 450), ("ART-002", 150, "30-pack", 380)]),
        ("PR-2026-002", "procurement@ugavi.demo", "Operations - OT", "Global Fund", 3500000,
         "Open Tender", "HIV rapid test kits and malaria RDTs",
         [("LAB-001", 500, "Box of 100", 2500), ("LAB-002", 300, "Box of 100", 1800)]),
        ("PR-2026-003", "logistics@ugavi.demo", "Purchase - OT", "USAID", 195000,
         "Request for Quotation (Direct)", "Office supplies and IT for HQ",
         [("NCL-001", 3, "Unit", 85000), ("MED-001", 100, "Box of 100", 350)]),
    ]:
        if not frappe.db.exists("Purchase Requisition", pr_name):
            pr = frappe.get_doc({
                "doctype": "Purchase Requisition", "title": pr_name,
                "status": "Draft", "requester": requester,
                "department": dept, "donor": donor_map.get(donor, donor),
                "estimated_value": est_val,
                "procurement_method": method,
                "waiver_required": 0, "justification": justification,
                "items": [{"item_code": ic, "quantity": q, "uom": u,
                           "estimated_unit_price": up, "estimated_total": q * up}
                          for ic, q, u, up in items],
            }).insert(ignore_permissions=True)
            print(f"  PR: {pr_name} | {donor} | {est_val:,} KES")

    # -- Supplier Prequalification --
    for cat in ["PHARMACEUTICAL", "LAB", "IT", "OFFICE"]:
        name = f"SUP-CAT-{cat}"
        if not frappe.db.exists("Prequalification Category", name):
            frappe.get_doc({"doctype": "Prequalification Category",
                            "category": cat, "status": "Active"}).insert()
            print(f"  PrequalCategory: {cat}")

    for supplier, cat, pq_date, exp, rev in [
        ("MEDSUPPLY-KE", "PHARMACEUTICAL", add_days(today_date, -90), add_days(today_date, 275), "procurement@ugavi.demo"),
        ("PHARMA-INTL", "PHARMACEUTICAL", add_days(today_date, -60), add_days(today_date, 305), "procurement@ugavi.demo"),
        ("DIAGNOSTICS-AFRICA", "LAB", add_days(today_date, -45), add_days(today_date, 320), "procurement@ugavi.demo"),
        ("IT-SOLUTIONS", "IT", add_days(today_date, -30), add_days(today_date, 335), "logistics@ugavi.demo"),
    ]:
        if not frappe.db.exists("Supplier Prequalification", f"{supplier}-{cat}"):
            frappe.get_doc({
                "doctype": "Supplier Prequalification", "supplier": supplier,
                "status": "Approved", "category": cat,
                "prequalification_date": pq_date, "expiry_date": exp,
                "reviewed_by": rev,
                "review_comments": "Meets all Ugavi requirements",
            }).insert(ignore_permissions=True)
            print(f"  Prequal: {supplier} -> {cat}")

    # -- Tenders --
    tender_names = {}
    for t_title, pr, donor, method, est_val, cat, pub, dead, open_d, o1, o2, o3 in [
        ("TND-2026-001", "PR-2026-001", "USAID", "Restricted Tender",
         1250000, "Drugs", add_days(today_date, -20), add_days(today_date, 5),
         add_days(today_date, 7),
         "opening1@ugavi.demo", "opening2@ugavi.demo", "opening3@ugavi.demo"),
        ("TND-2026-002", "PR-2026-002", "Global Fund", "Open Tender",
         3500000, "Lab Supplies", add_days(today_date, -15), add_days(today_date, 10),
         add_days(today_date, 12),
         "opening1@ugavi.demo", "opening2@ugavi.demo", "opening3@ugavi.demo"),
    ]:
        if not frappe.db.exists("Tender", t_title):
            t = frappe.get_doc({
                "doctype": "Tender", "title": t_title, "status": "Published",
                "purchase_requisition": pr, "donor": donor_map.get(donor, donor),
                "procurement_method": method, "estimated_value": est_val,
                "item_category": cat, "publish_date": pub,
                "submission_deadline": dead, "bid_opening_date": open_d,
                "opening_officer_1": o1, "opening_officer_2": o2,
                "opening_officer_3": o3,
            }).insert(ignore_permissions=True)
            tender_names[t_title] = t.name
            print(f"  Tender: {t_title} | {donor} | Published")
# -- Evaluation Committees --
    for ec_name, members in [
        ("EC-USAID-2026", ["approver1@ugavi.demo", "opening1@ugavi.demo", "logistics@ugavi.demo"]),
        ("EC-GF-2026", ["approver2@ugavi.demo", "opening2@ugavi.demo", "procurement@ugavi.demo"]),
    ]:
        if not frappe.db.exists("Evaluation Committee", ec_name):
            ec = frappe.get_doc({"doctype": "Evaluation Committee", "name": ec_name})
            for user_email in members:
                ec.append("members", {"user": user_email, "role": "Member"})
            ec.insert(ignore_permissions=True)
            print(f"  Committee: {ec_name} ({len(members)} members)")

    # -- Ugavi Contracts with milestones --
    for c_tender, c_supplier, c_donor, c_val, c_ret, c_bond, milestones in [
        ("TND-2026-001", "MEDSUPPLY-KE", "USAID", 1180000, 5, 59000, [
            ("Initial Delivery", add_days(today_date, 30), 400000),
            ("Mid-term Delivery", add_days(today_date, 120), 400000),
            ("Final Delivery & Acceptance", add_days(today_date, 210), 380000)]),
        ("TND-2026-002", "DIAGNOSTICS-AFRICA", "Global Fund", 3200000, 10, 320000, [
            ("Batch 1: 30% Delivery", add_days(today_date, 45), 960000),
            ("Batch 2: 40% Delivery", add_days(today_date, 120), 1280000),
            ("Batch 3: 30% Delivery (Final)", add_days(today_date, 200), 960000)]),
    ]:
        cname = f"CON-{c_tender}"
        if not frappe.db.exists("Ugavi Contract", cname):
            frappe.get_doc({
                "doctype": "Ugavi Contract", "tender": c_tender,
                "supplier": c_supplier, "donor": c_donor, "status": "Draft",
                "start_date": add_days(today_date, 14), "end_date": add_days(today_date, 365),
                "contract_value": c_val, "retention_percentage": c_ret,
                "performance_bond_required": 1, "bond_amount": c_bond,
                "milestones": [{"milestone_name": mn, "due_date": d, "amount": a}
                               for mn, d, a in milestones],
            }).insert(ignore_permissions=True)
            print(f"  Contract: {cname} | {c_supplier} | {c_val:,} KES | {len(milestones)} ms")

    # -- Supplier Scorecards --
    for supplier, eval_date, q, d, c, p, remarks in [
        ("MEDSUPPLY-KE", add_days(today_date, -60), 9, 8, 10, 8, "Excellent quality, on-time"),
        ("DIAGNOSTICS-AFRICA", add_days(today_date, -60), 8, 7, 9, 9, "Good quality, slight delay"),
    ]:
        sn = f"{supplier}-{eval_date}"
        if not frappe.db.exists("Supplier Scorecard", sn):
            frappe.get_doc({
                "doctype": "Supplier Scorecard", "supplier": supplier,
                "evaluation_date": eval_date, "quality_score": q,
                "delivery_score": d, "compliance_score": c,
                "price_competitiveness": p,
                "total_score": q + d + c + p,
                "cumulative_rating": (q + d + c + p) / 40 * 100,
                "remarks": remarks,
            }).insert(ignore_permissions=True)
            print(f"  Scorecard: {supplier} | {eval_date}")

    # -- Segregation of Duties --
    for r1, r2, ctype, enforce, desc in [
        ("Procurement Officer", "Approver Level 1", "Approval", "Hard Block",
         "Requester cannot approve own PRs"),
        ("Procurement Officer", "Bid Opening Officer", "Bid Management", "Hard Block",
         "PO cannot open bids"),
        ("Bid Opening Officer", "Evaluation Committee", "Evaluation", "Soft Warning",
         "Bid opener should not evaluate"),
    ]:
        sod_name = f"{r1}-{r2}-{ctype}"
        if not frappe.db.exists("Segregation of Duties", sod_name):
            frappe.get_doc({
                "doctype": "Segregation of Duties", "role_1": r1, "role_2": r2,
                "conflict_type": ctype, "enforcement": enforce,
                "description": desc,
            }).insert(ignore_permissions=True)
            print(f"  SoD: {r1} != {r2} ({enforce})")

    # -- Donor Warehouses --
    for donor, warehouse in [("USAID", "Stores - OT"), ("Global Fund", "Stores - OT"),
                              ("UNICEF", "Stores - OT"), ("World Bank", "Stores - OT")]:
        dw_name = f"{donor}-{warehouse}"
        if not frappe.db.exists("Donor Warehouse", dw_name):
            frappe.get_doc({
                "doctype": "Donor Warehouse", "warehouse": warehouse,
                "donor": donor_map.get(donor, donor), "restricted_items": 0,
            }).insert(ignore_permissions=True)
            print(f"  DonorWH: {donor} <-> {warehouse}")

    # -- Budget Encumbrances --
    for po_ref, donor, amount, budget_ref, status in [
        ("PO-2026-001", "USAID", 1180000, "USAID-FY26-HEALTH", "Encumbered"),
        ("PO-2026-002", "Global Fund", 3200000, "GF-FY26-MALARIA", "Encumbered"),
    ]:
        be_name = f"ENC-{po_ref}"
        if not frappe.db.exists("Budget Encumbrance", be_name):
            frappe.get_doc({
                "doctype": "Budget Encumbrance", "purchase_order": po_ref,
                "budget": budget_ref, "encumbered_amount": amount,
                "donor": donor_map.get(donor, donor), "status": status,
            }).insert(ignore_permissions=True)
            print(f"  BudgetEnc: {donor} | {amount:,} KES")

    print("  === Procurement workflow seed complete ===")
