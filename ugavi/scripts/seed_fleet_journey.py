"""Deterministic submitted fleet journeys used by customer demo seeds."""

import frappe
from frappe.utils import add_days, today

from ugavi.fleet.services.purchase_reconciliation import (
    create_for_purchase_receipt,
)


FUEL_ITEMS = {"Diesel": "FUEL-DIESEL", "Petrol": "FUEL-PETROL"}
FUEL_RATES = {"Diesel": 210, "Petrol": 180}
FUEL_LOG_OFFSETS = (-40, -20, -5)
UNMETERED_CLASSES = {"boat", "generator"}


def _vehicle_class(scenario):
    model = scenario.get("model", "")
    if scenario.get("make") in ("Bajaj", "TVS"):
        return "motorcycle"
    if "Generator" in model:
        return "generator"
    if "Boat" in model or "Fiberglass" in model:
        return "boat"
    if any(t in model for t in ("Truck", "Canter", "Fuso", "FVR", "Dyna", "Bowser")):
        return "truck"
    return "light"


def _trip_plan(scenario):
    """Chronological trips whose odometer readings chain from the vehicle's base reading."""
    vehicle_class = _vehicle_class(scenario)
    trips = [
        (-38, 100, "Programme monitoring field visit"),
        (-18, 400, "Donor-supported commodity delivery"),
    ]
    if "Cross-border" in scenario.get("destination", ""):
        trips.append((-50, 400, "Cross-border peace-building mission — Kenya/Uganda border"))
    if vehicle_class == "truck":
        trips.append((-7, 600, "Bulk construction materials delivery to field site"))
    trips.sort()

    metered = vehicle_class not in UNMETERED_CLASSES
    odometer = scenario.get("last_odometer", 10000) if metered else 0
    plan = []
    for offset, distance, purpose in trips:
        end = odometer + distance if metered else 0
        plan.append((offset, odometer, end, purpose))
        odometer = end
    return plan


def _fuel_plan(scenario):
    """Fuel draws (offset, litres, odometer) consistent with the trip timeline."""
    litres = (8, 12, 10) if _vehicle_class(scenario) == "motorcycle" else (50, 70, 55)
    trips = _trip_plan(scenario)
    metered = _vehicle_class(scenario) not in UNMETERED_CLASSES
    base = scenario.get("last_odometer", 10000)
    plan = []
    for offset, quantity in zip(FUEL_LOG_OFFSETS, litres):
        odometer = 0
        if metered:
            odometer = max([end for start_offset, _s, end, _p in trips if start_offset < offset] or [base])
        plan.append((offset, quantity, odometer))
    return plan


def seed_fleet_journey(company, fleet_user, supplier, scenarios):
    """Seed real procurement-backed fleet records for the supplied donor scenarios."""
    _ensure_fleet_items()
    for scenario in scenarios:
        _seed_scenario(company, fleet_user, supplier, scenario)
    frappe.db.commit()


def _seed_scenario(company, fleet_user, supplier, scenario):
    donor = frappe.db.get_value(
        "Donor Profile", {"donor_code": scenario["donor_code"]}, "name"
    )
    if not donor:
        frappe.throw(f"Demo donor {scenario['donor_code']} does not exist")
    warehouse = frappe.db.get_value(
        "Warehouse", {"warehouse_name": scenario["warehouse_name"]}, "name"
    )
    if not warehouse:
        frappe.throw(f"Demo warehouse {scenario['warehouse_name']} does not exist")
    if not frappe.db.exists(
        "Donor Warehouse", {"donor": donor, "warehouse": warehouse}
    ):
        frappe.get_doc(
            {
                "doctype": "Donor Warehouse",
                "donor": donor,
                "warehouse": warehouse,
                "restricted_items": 0,
            }
        ).insert(ignore_permissions=True)

    vehicle = _ensure_vehicle(company, donor, warehouse, scenario)
    allocation = _ensure_allocation(vehicle, fleet_user, donor, scenario)
    fuel_type = scenario.get("fuel_type", "Diesel")
    receipt = _ensure_fleet_purchase(
        company,
        supplier,
        donor,
        warehouse,
        scenario["marker"],
        fuel_item=FUEL_ITEMS[fuel_type],
        fuel_qty=sum(litres for _o, litres, _odo in _fuel_plan(scenario)),
        fuel_rate=FUEL_RATES[fuel_type],
    )
    create_for_purchase_receipt(receipt)
    _activate_contract(receipt, scenario)
    _complete_supplier_evaluation(receipt)

    fuel_source = frappe.db.get_value(
        "Fleet Purchase Reconciliation",
        {
            "purchase_receipt": receipt.name,
            "fleet_category": "Fuel",
            "status": ("!=", "Cancelled"),
        },
        "name",
    )
    spare_source = frappe.db.get_value(
        "Fleet Purchase Reconciliation",
        {
            "purchase_receipt": receipt.name,
            "fleet_category": "Spare Part",
            "status": ("!=", "Cancelled"),
        },
        "name",
    )
    if not fuel_source or not spare_source:
        frappe.throw(f"Fleet reconciliation was not created for {receipt.name}")

    _ensure_fuel_logs(vehicle, donor, fuel_source, scenario)
    _ensure_spare_issues(vehicle, donor, warehouse, spare_source, scenario)
    _ensure_trips(vehicle, donor, allocation, scenario)
    _ensure_report(donor, scenario)


def _ensure_fleet_items():
    for uom, whole in (("Litres", 0), ("Nos", 1)):
        if not frappe.db.exists("UOM", uom):
            frappe.get_doc(
                {"doctype": "UOM", "uom_name": uom, "must_be_whole_number": whole}
            ).insert(ignore_permissions=True)
    if not frappe.db.exists("Item Group", "Vehicles & Spares"):
        frappe.get_doc(
            {"doctype": "Item Group", "item_group_name": "Vehicles & Spares"}
        ).insert(ignore_permissions=True)
    for code, name, uom, category in (
        ("FUEL-DIESEL", "Fuel - Diesel", "Litres", "Fuel"),
        ("FUEL-PETROL", "Fuel - Petrol", "Litres", "Fuel"),
        ("VEHICLE-SPARE-OIL", "Engine Oil 5W-30", "Nos", "Spare Part"),
    ):
        if not frappe.db.exists("Item", code):
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": code,
                    "item_name": name,
                    "item_group": "Vehicles & Spares",
                    "stock_uom": uom,
                    "is_stock_item": 1,
                    "valuation_rate": 0,
                }
            ).insert(ignore_permissions=True)
        frappe.db.set_value(
            "Item", code, "ugavi_fleet_category", category, update_modified=False
        )


def _ensure_vehicle(company, donor, warehouse, scenario):
    plate = scenario["license_plate"]
    vehicle = frappe.db.get_value("Vehicle", {"license_plate": plate}, "name")
    if not vehicle:
        doc = frappe.get_doc(
            {
                "doctype": "Vehicle",
                "license_plate": plate,
                "make": scenario.get("make", "Toyota"),
                "model": scenario.get("model", "Land Cruiser"),
                "company": company,
                "fuel_type": scenario.get("fuel_type", "Diesel"),
                "uom": "Litres",
                "last_odometer": scenario.get("last_odometer", 10000),
                "acquisition_date": add_days(today(), -730),
                "vehicle_value": scenario.get("vehicle_value", 4500000),
                "ugavi_donor": donor,
                "ugavi_warehouse": warehouse,
                "ugavi_status": "Active",
                "ugavi_next_service_date": add_days(today(), 30),
            }
        )
        doc.insert(ignore_permissions=True)
        vehicle = doc.name
    else:
        frappe.db.set_value(
            "Vehicle",
            vehicle,
            {
                "ugavi_donor": donor,
                "ugavi_warehouse": warehouse,
                "ugavi_status": "Active",
            },
            update_modified=False,
        )
    # ── Driver record ──
    _ensure_driver(vehicle, scenario)
    # ── Insurance ──
    _ensure_insurance(vehicle, scenario)
    # ── Maintenance logs ──
    _ensure_maintenance(vehicle, scenario)
    # ── Incident (some vehicles had a field incident) ──
    if sum(ord(c) for c in plate) % 3 == 0:
        _ensure_incident(vehicle, scenario)
    return vehicle


# ─────────────────────────────────────────────────
# DRIVERS — LOKADO field drivers assigned to vehicles
# ─────────────────────────────────────────────────

LOKADO_DRIVERS = [
    ("driver1@lokado.org", "Simon", "Ekimat", "+254712000101"),
    ("driver2@lokado.org", "Martin", "Lopeyok", "+254712000102"),
    ("driver3@lokado.org", "Ezekiel", "Emoru", "+254712000103"),
    ("driver4@lokado.org", "Joseph", "Esekon", "+254712000104"),
    ("driver5@lokado.org", "Benson", "Lotulia", "+254712000105"),
    ("driver6@lokado.org", "Patrick", "Ngikor", "+254712000106"),
    ("driver7@lokado.org", "Tom", "Lokwawi", "+254712000107"),
    ("driver8@lokado.org", "Lucas", "Edong", "+254712000108"),
    ("driver9@lokado.org", "Peter", "Ngimor", "+254712000109"),
    ("driver10@lokado.org", "Francis", "Eregae", "+254712000110"),
]


def _ensure_driver(vehicle, scenario):
    """Create or re-use a driver for this vehicle (deterministic)."""
    plate = scenario["license_plate"]
    driver_idx = sum(ord(c) for c in plate) % len(LOKADO_DRIVERS)
    email, first, last, mobile = LOKADO_DRIVERS[driver_idx]

    # Ensure user exists
    if not frappe.db.exists("User", email):
        user = frappe.get_doc({
            "doctype": "User", "email": email,
            "first_name": first, "last_name": last,
            "send_welcome_email": 0, "enabled": 1,
            "new_password": "Ugavi@2024", "mobile_no": mobile,
        })
        user.append("roles", {"role": "Fleet Manager"})
        user.insert(ignore_permissions=True)

    # Ensure Driver doctype record
    if frappe.db.exists("DocType", "Driver"):
        if not frappe.db.exists("Driver", {"user": email}):
            frappe.get_doc({
                "doctype": "Driver",
                "full_name": f"{first} {last}",
                "user": email, "cell_number": mobile,
            }).insert(ignore_permissions=True)


def _ensure_insurance(vehicle, scenario):
    """Vehicle comprehensive insurance (mandatory in Kenya)."""
    if not frappe.db.exists("DocType", "Vehicle Insurance"):
        return
    plate = scenario["license_plate"]
    if frappe.db.exists("Vehicle Insurance", {"license_plate": plate, "docstatus": ("!=", 2)}):
        return
    ins = frappe.get_doc({
        "doctype": "Vehicle Insurance",
        "license_plate": plate,
        "insurance_company": "Kenya Orient Insurance",
        "policy_number": f"KOI-V-{plate.replace(' ', '-')}-2024",
        "start_date": add_days(today(), -180),
        "end_date": add_days(today(), 185),
        "premium_amount": int(scenario.get("vehicle_value", 4500000) * 0.035),
        "comprehensive_cover": 1,
    })
    ins.insert(ignore_permissions=True)
    ins.submit()


def _ensure_maintenance(vehicle, scenario):
    """One completed service (30 days ago) + upcoming set on vehicle record."""
    if not frappe.db.exists("DocType", "Vehicle Service"):
        return
    plate = scenario["license_plate"]
    service_date = str(add_days(today(), -30))
    if frappe.db.exists("Vehicle Service", {"license_plate": plate, "service_date": service_date}):
        return
    svc = frappe.get_doc({
        "doctype": "Vehicle Service",
        "license_plate": plate,
        "service_date": add_days(today(), -30),
        "odometer": max(0, scenario.get("last_odometer", 10000) - 5000),
        "service_type": "Scheduled",
        "garage_name": "Lodwar Motors Garage",
        "description": "Engine oil + filters, brake pads, suspension check & alignment.",
        "total_cost": int(scenario.get("vehicle_value", 4500000) * 0.008),
    })
    svc.insert(ignore_permissions=True)
    svc.submit()


def _ensure_incident(vehicle, scenario):
    """Record a field incident (1 in 3 vehicles)."""
    if not frappe.db.exists("DocType", "Vehicle Incident"):
        return
    plate = scenario["license_plate"]
    if frappe.db.exists("Vehicle Incident", {"license_plate": plate}):
        return
    incidents = [
        ("Breakdown - Tyre Burst on rocky track near Oropoi", "Resolved", "Spare tyre fitted. Back on road same day.", "Breakdown"),
        ("Minor Accident - Reversing into boulder at Lokipoto", "Resolved", "Rear bumper damage. Panel beating at Lodwar Motors.", "Accident"),
        ("Overheating - Radiator on Kakuma-Lodwar road", "Resolved", "Towed. Radiator replaced, coolant flush.", "Breakdown"),
        ("Mechanical - Clutch failure near Kalobeyei", "Resolved", "Clutch kit replaced. 4-day downtime.", "Breakdown"),
        ("Electrical - Alternator failure at Letea field site", "Resolved", "Jump-started, alternator replaced. 1-day delay.", "Breakdown"),
    ]
    desc, status, resolution, itype = incidents[sum(ord(c) for c in plate) % len(incidents)]
    frappe.get_doc({
        "doctype": "Vehicle Incident",
        "license_plate": plate,
        "incident_date": add_days(today(), -90),
        "incident_type": itype,
        "description": desc,
        "resolution": resolution,
        "status": status,
        "estimated_cost": int(scenario.get("vehicle_value", 4500000) * 0.015),
    }).insert(ignore_permissions=True)


# ─────────────────────────────────────────────────


def _ensure_allocation(vehicle, fleet_user, donor, scenario):
    allocation = frappe.db.get_value(
        "Vehicle Allocation",
        {
            "vehicle": vehicle,
            "allocated_to": fleet_user,
            "status": "Active",
        },
        "name",
    )
    if allocation:
        return allocation
    start_date = add_days(today(), -120)
    doc = frappe.get_doc(
        {
            "doctype": "Vehicle Allocation",
            "vehicle": vehicle,
            "allocated_to": fleet_user,
            "donor": donor,
            "project": scenario.get("project"),
            "start_date": start_date,
            "end_date": add_days(today(), 120),
            "status": "Active",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_fleet_purchase(
    company, supplier, donor, warehouse, marker, fuel_item, fuel_qty, fuel_rate
):
    receipt_name = frappe.db.get_value(
        "Purchase Receipt", {"supplier_delivery_note": marker}, "name"
    )
    if receipt_name:
        receipt = frappe.get_doc("Purchase Receipt", receipt_name)
        if receipt.docstatus != 1:
            receipt.submit()
        return receipt

    order_name = frappe.db.get_value("Purchase Order", {"title": marker}, "name")
    if order_name:
        order = frappe.get_doc("Purchase Order", order_name)
    else:
        order = frappe.get_doc(
            {
                "doctype": "Purchase Order",
                "title": marker,
                "company": company,
                "supplier": supplier,
                "transaction_date": add_days(today(), -45),
                "schedule_date": add_days(today(), -40),
                "ugavi_donor": donor,
                "items": [
                    {
                        "item_code": fuel_item,
                        "qty": fuel_qty,
                        "rate": fuel_rate,
                        "schedule_date": add_days(today(), -40),
                        "warehouse": warehouse,
                    },
                    {
                        "item_code": "VEHICLE-SPARE-OIL",
                        "qty": 10,
                        "rate": 1800,
                        "schedule_date": add_days(today(), -40),
                        "warehouse": warehouse,
                    },
                ],
            }
        )
        order.insert(ignore_permissions=True)
        order.submit()

    from erpnext.buying.doctype.purchase_order.purchase_order import (
        make_purchase_receipt,
    )

    receipt = make_purchase_receipt(order.name)
    receipt.supplier_delivery_note = marker
    receipt.set_posting_time = 1
    receipt.posting_date = add_days(today(), -40)
    receipt.posting_time = "09:00:00"
    receipt.insert(ignore_permissions=True)
    receipt.submit()
    return receipt


def _activate_contract(receipt, scenario):
    purchase_order = receipt.items[0].purchase_order
    contract_name = frappe.db.get_value(
        "Ugavi Contract", {"purchase_order": purchase_order}, "name"
    )
    if not contract_name:
        from ugavi.procurement.doctype.ugavi_contract.ugavi_contract import (
            ensure_contract_for_purchase_order,
        )

        ensure_contract_for_purchase_order(frappe.get_doc("Purchase Order", purchase_order))
        contract_name = frappe.db.get_value(
            "Ugavi Contract", {"purchase_order": purchase_order}, "name"
        )
    contract = frappe.get_doc("Ugavi Contract", contract_name)
    if contract.status != "Draft":
        return
    from frappe.utils.file_manager import save_file

    file_doc = save_file(
        f"{scenario['marker']}-contract.txt",
        (
            f"DEMO CONTRACT\nPurchase Order: {purchase_order}\n"
            f"Purpose: {scenario.get('purpose', 'fleet fuel and spare-parts framework')}\n"
        ).encode(),
        "Ugavi Contract",
        contract.name,
        is_private=1,
    )
    contract.append(
        "documents",
        {
            "document_name": "Signed Supply Agreement (Demo)",
            "attachment": file_doc.file_url,
            "expiry_date": contract.end_date,
        },
    )
    contract.append(
        "milestones",
        {
            "milestone_name": "Delivery, inspection and acceptance",
            "due_date": contract.end_date,
            "amount": contract.contract_value,
            "status": "Pending",
        },
    )
    contract.retention_percentage = 10
    contract.status = "Active"
    contract.save(ignore_permissions=True)


def _complete_supplier_evaluation(receipt):
    evaluation_name = frappe.db.get_value(
        "Ugavi Supplier Evaluation", {"purchase_receipt": receipt.name}, "name"
    )
    if not evaluation_name:
        frappe.throw(f"Supplier evaluation missing for {receipt.name}")
    evaluation = frappe.get_doc("Ugavi Supplier Evaluation", evaluation_name)
    if evaluation.status == "Completed":
        return
    evaluation.quality_score = 9
    evaluation.delivery_score = 8
    evaluation.compliance_score = 9
    evaluation.price_competitiveness = 8
    evaluation.remarks = "Demo delivery inspected and accepted by Fleet Manager."
    evaluation.complete_evaluation()


def _ensure_fuel_logs(vehicle, donor, source, scenario):
    fuel_type = scenario.get("fuel_type", "Diesel")
    cost_per_litre = FUEL_RATES[fuel_type]
    fuel_items = _fuel_plan(scenario)
    for offset, litres, odometer in fuel_items:
        log_date = add_days(today(), offset)
        if frappe.db.exists(
            "Fuel Log",
            {
                "vehicle": vehicle,
                "source_reconciliation": source,
                "receipt_number": f"{scenario['marker']}-{abs(offset)}",
                "docstatus": ("!=", 2),
            },
        ):
            continue
        doc = frappe.get_doc(
            {
                "doctype": "Fuel Log",
                "vehicle": vehicle,
                "source_reconciliation": source,
                "date": log_date,
                "fuel_type": fuel_type,
                "litres": litres,
                "cost_per_litre": cost_per_litre,
                "odometer": odometer,
                "station": scenario.get("station", "LOKADO Approved Fuel Station"),
                "receipt_number": f"{scenario['marker']}-{abs(offset)}",
                "donor": donor,
            }
        )
        doc.insert(ignore_permissions=True)
        doc.submit()


def _ensure_spare_issues(vehicle, donor, warehouse, source, scenario):
    for quantity in (4, 6):
        existing = frappe.db.sql(
            """SELECT p.name
               FROM `tabSpare Parts Issue` p
               INNER JOIN `tabFleet Spare Part Item` i ON i.parent = p.name
               WHERE p.vehicle = %s AND p.docstatus = 1
                 AND i.source_reconciliation = %s AND i.quantity = %s
               LIMIT 1""",
            (vehicle, source, quantity),
        )
        if existing:
            continue
        doc = frappe.get_doc(
            {
                "doctype": "Spare Parts Issue",
                "vehicle": vehicle,
                "warehouse": warehouse,
                "donor": donor,
                "items": [
                    {
                        "source_reconciliation": source,
                        "quantity": quantity,
                    }
                ],
            }
        )
        doc.insert(ignore_permissions=True)
        doc.submit()


def _ensure_trips(vehicle, donor, allocation, scenario):
    for offset, s_odo, e_odo, purpose in _trip_plan(scenario):
        start_date_str = f"{add_days(today(), offset)} 08:00:00"
        lookup = {"vehicle": vehicle, "purpose": purpose, "docstatus": ("!=", 2)}
        if frappe.db.exists("Trip Log", lookup):
            continue
        doc = frappe.get_doc(
            {
                "doctype": "Trip Log",
                "vehicle": vehicle,
                "vehicle_allocation": allocation,
                "start_date": start_date_str,
                "end_date": f"{add_days(today(), offset)} 17:00:00",
                "start_odometer": s_odo,
                "end_odometer": e_odo,
                "purpose": purpose,
                "destination": scenario.get("destination", "Field programme site"),
                "donor": donor,
                "status": "Completed",
            }
        )
        doc.insert(ignore_permissions=True)
        doc.submit()


def _ensure_report(donor, scenario):
    from_date = add_days(today(), -60)
    existing = frappe.db.exists(
        "Fleet Utilization Report",
        {"donor": donor, "docstatus": ("!=", 2)},
    )
    report = frappe.get_doc("Fleet Utilization Report", existing) if existing else frappe.get_doc(
        {"doctype": "Fleet Utilization Report", "donor": donor}
    )
    report.from_date = from_date
    report.to_date = today()
    report.generate()
