"""Vehicle allocation with exclusive date-range enforcement."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class VehicleAllocation(Document):
    def validate(self):
        if self.end_date and getdate(self.end_date) < getdate(self.start_date):
            frappe.throw(_("End date cannot be before start date."))
        if self.actual_return_date and getdate(self.actual_return_date) < getdate(
            self.start_date
        ):
            frappe.throw(_("Actual return date cannot be before start date."))
        if not frappe.db.get_value("User", self.allocated_to, "enabled"):
            frappe.throw(_("Vehicle can only be allocated to an enabled user."))
        vehicle_donor = frappe.db.get_value("Vehicle", self.vehicle, "ugavi_donor")
        if not self.donor:
            self.donor = vehicle_donor
        elif vehicle_donor and self.donor != vehicle_donor:
            frappe.throw(
                _("Allocation donor must match vehicle donor {0}.").format(
                    vehicle_donor
                )
            )
        self._validate_no_overlap()

    def _validate_no_overlap(self):
        overlap = frappe.db.sql(
            """SELECT name
               FROM `tabVehicle Allocation`
               WHERE vehicle = %s
                 AND name != %s
                 AND status = 'Active'
                 AND start_date <= COALESCE(%s, '9999-12-31')
                 AND COALESCE(end_date, '9999-12-31') >= %s
               LIMIT 1""",
            (self.vehicle, self.name or "", self.end_date, self.start_date),
        )
        if overlap:
            frappe.throw(
                _("Vehicle is already allocated in {0} for this period.").format(
                    overlap[0][0]
                )
            )

    @frappe.whitelist()
    def return_vehicle(self):
        if self.status != "Active":
            frappe.throw(_("Only an active allocation can be returned."))
        self.status = "Returned"
        self.actual_return_date = today()
        if not self.end_date or getdate(self.end_date) > getdate(self.actual_return_date):
            self.end_date = self.actual_return_date
        self.save()
