"""Fuel purchases allocated to vehicles from reconciled procurement sources."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from ugavi.fleet.services.purchase_reconciliation import (
    lock_and_validate_allocation,
    refresh_reconciliation,
)


class FuelLog(Document):
    def validate(self):
        if flt(self.litres) <= 0:
            frappe.throw(_("Litres must be greater than zero."))
        if flt(self.cost_per_litre) < 0:
            frappe.throw(_("Cost per litre cannot be negative."))
        self.total_cost = flt(self.litres) * flt(self.cost_per_litre)
        self._apply_purchase_source()
        self._validate_vehicle_and_odometer()

    def before_submit(self):
        lock_and_validate_allocation(
            self.source_reconciliation,
            self.litres,
            "Fuel",
            donor=self.donor,
        )

    def on_submit(self):
        refresh_reconciliation(self.source_reconciliation)
        recompute_vehicle_fuel_totals(self.vehicle)

    def on_cancel(self):
        refresh_reconciliation(self.source_reconciliation)
        recompute_vehicle_fuel_totals(self.vehicle)

    def _apply_purchase_source(self):
        if not self.source_reconciliation:
            return
        source = frappe.get_doc(
            "Fleet Purchase Reconciliation", self.source_reconciliation
        )
        if source.fleet_category != "Fuel":
            frappe.throw(
                _("Fleet purchase {0} is not classified as Fuel.").format(source.name)
            )
        self.purchase_order = source.purchase_order
        self.purchase_receipt = source.purchase_receipt
        self.purchase_invoice = source.purchase_invoice
        self.donor = source.donor
        if not self.cost_per_litre:
            self.cost_per_litre = source.valuation_rate
            self.total_cost = flt(self.litres) * flt(self.cost_per_litre)

    def _validate_vehicle_and_odometer(self):
        vehicle = frappe.db.get_value(
            "Vehicle",
            self.vehicle,
            ["ugavi_donor", "last_odometer"],
            as_dict=True,
        )
        if not vehicle:
            frappe.throw(_("Vehicle {0} does not exist.").format(self.vehicle))
        if vehicle.ugavi_donor and self.donor and vehicle.ugavi_donor != self.donor:
            frappe.throw(
                _("Vehicle donor {0} does not match purchase donor {1}.").format(
                    vehicle.ugavi_donor, self.donor
                )
            )
        previous_odometer = frappe.db.get_value(
            "Fuel Log",
            {
                "vehicle": self.vehicle,
                "docstatus": 1,
                "name": ("!=", self.name),
            },
            "odometer",
            order_by="odometer desc",
        )
        if self.odometer and previous_odometer and self.odometer < previous_odometer:
            frappe.throw(
                _("Fuel odometer cannot be below the last submitted reading {0}.").format(
                    previous_odometer
                )
            )


def recompute_vehicle_fuel_totals(vehicle_name):
    """Derive cached Vehicle totals only from submitted evidence."""
    totals = frappe.db.sql(
        """SELECT COALESCE(SUM(litres), 0), COALESCE(SUM(total_cost), 0),
                  COALESCE(MAX(odometer), 0)
           FROM `tabFuel Log`
           WHERE vehicle = %s AND docstatus = 1""",
        vehicle_name,
    )[0]
    trip_odometer = (
        frappe.db.get_value(
            "Trip Log",
            {"vehicle": vehicle_name, "docstatus": 1},
            "end_odometer",
            order_by="end_odometer desc",
        )
        or 0
    )
    frappe.db.set_value(
        "Vehicle",
        vehicle_name,
        {
            "ugavi_total_fuel_litres": totals[0],
            "ugavi_total_fuel_cost": totals[1],
            "last_odometer": max(flt(totals[2]), flt(trip_odometer)),
        },
        update_modified=False,
    )
