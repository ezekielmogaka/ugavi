"""Authorized vehicle trips and odometer evidence."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime

from ugavi.fleet.doctype.fuel_log.fuel_log import recompute_vehicle_fuel_totals


class TripLog(Document):
    def validate(self):
        if self.end_date and get_datetime(self.end_date) < get_datetime(self.start_date):
            frappe.throw(_("End date cannot be before start date."))
        if self.end_odometer and self.start_odometer:
            if self.end_odometer < self.start_odometer:
                frappe.throw(_("End odometer must be at least the start odometer."))
            self.distance = self.end_odometer - self.start_odometer
        if not self.vehicle_allocation:
            frappe.throw(_("A Vehicle Allocation is required to authorize this trip."))
        self._apply_allocation()

    def before_submit(self):
        if self.status != "Completed" or not self.end_date or not self.end_odometer:
            frappe.throw(
                _("Complete the trip with an end date and odometer before submitting.")
            )
        previous = frappe.db.get_value(
            "Trip Log",
            {
                "vehicle": self.vehicle,
                "docstatus": 1,
                "name": ("!=", self.name),
            },
            "end_odometer",
            order_by="end_odometer desc",
        )
        if previous and self.start_odometer < previous:
            frappe.throw(
                _("Start odometer cannot be below the last submitted reading {0}.").format(
                    previous
                )
            )

    def on_submit(self):
        recompute_vehicle_fuel_totals(self.vehicle)

    def on_cancel(self):
        recompute_vehicle_fuel_totals(self.vehicle)

    def _apply_allocation(self):
        allocation = frappe.get_doc("Vehicle Allocation", self.vehicle_allocation)
        if allocation.vehicle != self.vehicle:
            frappe.throw(_("Vehicle Allocation belongs to a different vehicle."))
        trip_start = get_datetime(self.start_date).date()
        if trip_start < allocation.start_date or (
            allocation.end_date and trip_start > allocation.end_date
        ):
            frappe.throw(_("Trip date is outside the allocation period."))
        self.driver = allocation.allocated_to
        if not self.donor:
            self.donor = allocation.donor
        elif allocation.donor and self.donor != allocation.donor:
            frappe.throw(_("Trip donor must match the Vehicle Allocation donor."))

    @frappe.whitelist()
    def complete(self):
        if self.docstatus != 0:
            frappe.throw(_("Only a draft trip can be completed."))
        self.status = "Completed"
        self.end_date = frappe.utils.now_datetime()
        self.save()
