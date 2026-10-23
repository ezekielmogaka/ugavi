"""Deterministic submitted fleet journeys used by customer demo seeds."""

import frappe
from frappe.utils import add_days, today

from ugavi.fleet.services.purchase_reconciliation import (
    create_for_purchase_receipt,
)


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
    receipt = _ensure_fleet_purchase(
        company, supplier, donor, warehouse, scenario["marker"]
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
                "fuel_type": "Diesel",
                "uom": "Litres",
                "last_odometer": 10000,
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
    return vehicle


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


def _ensure_fleet_purchase(company, supplier, donor, warehouse, marker):
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
                        "item_code": "FUEL-DIESEL",
                        "qty": 120,
                        "rate": 210,
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
            f"Purpose: fleet fuel and spare-parts framework\n"
        ).encode(),
        "Ugavi Contract",
        contract.name,
        is_private=1,
    )
    contract.append(
        "documents",
        {
            "document_name": "Signed Fleet Supply Framework (Demo)",
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
    for offset, litres, odometer in ((-35, 50, 10100), (-15, 70, 10500)):
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
                "fuel_type": "Diesel",
                "litres": litres,
                "cost_per_litre": 210,
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
    for offset, start_odometer, end_odometer, purpose in (
        (-34, 10000, 10100, "Programme monitoring field visit"),
        (-14, 10100, 10500, "Donor-supported commodity delivery"),
    ):
        start_date = f"{add_days(today(), offset)} 08:00:00"
        if frappe.db.exists(
            "Trip Log",
            {
                "vehicle": vehicle,
                "start_odometer": start_odometer,
                "end_odometer": end_odometer,
                "docstatus": ("!=", 2),
            },
        ):
            continue
        doc = frappe.get_doc(
            {
                "doctype": "Trip Log",
                "vehicle": vehicle,
                "vehicle_allocation": allocation,
                "start_date": start_date,
                "end_date": f"{add_days(today(), offset)} 17:00:00",
                "start_odometer": start_odometer,
                "end_odometer": end_odometer,
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
    if existing:
        return
    report = frappe.get_doc(
        {
            "doctype": "Fleet Utilization Report",
            "donor": donor,
            "from_date": from_date,
            "to_date": today(),
        }
    )
    report.generate()
