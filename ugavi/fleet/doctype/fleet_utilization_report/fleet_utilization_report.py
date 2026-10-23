"""Fleet Utilization Report — summary of vehicle usage, fuel, trips."""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate
from frappe.utils.data import now_datetime


class FleetUtilizationReport(Document):
    """Report summarizing fleet usage: distance, fuel consumption, trip duration."""

    @property
    def columns(self):
        return [
            {"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 150},
            {"label": "Make/Model", "fieldname": "make_model", "fieldtype": "Data", "width": 150},
            {"label": "Total Trips", "fieldname": "total_trips", "fieldtype": "Int", "width": 100},
            {"label": "Total Distance (km)", "fieldname": "total_distance", "fieldtype": "Float", "width": 130},
            {"label": "Total Hours", "fieldname": "total_hours", "fieldtype": "Float", "width": 100},
            {"label": "Fuel Used (L)", "fieldname": "fuel_used", "fieldtype": "Float", "width": 120},
            {"label": "Fuel Cost (KES)", "fieldname": "fuel_cost", "fieldtype": "Currency", "width": 130},
            {"label": "Spare Parts Cost (KES)", "fieldname": "spare_parts_cost", "fieldtype": "Currency", "width": 140},
            {"label": "Unallocated Purchases", "fieldname": "unallocated_purchases", "fieldtype": "Float", "width": 140},
            {"label": "Avg km/L", "fieldname": "avg_kmpl", "fieldtype": "Float", "width": 100},
            {"label": "Eff. Anomaly", "fieldname": "efficiency_anomaly", "fieldtype": "Data", "width": 110},
            {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
        ]

    def validate(self):
        if not self.to_date:
            frappe.throw(_("To Date is required."))
        if getdate(self.to_date) < getdate(self.from_date):
            frappe.throw(_("To Date cannot be before From Date."))
        if date_diff(self.to_date, self.from_date) > 366:
            frappe.throw(_("Fleet report periods cannot exceed 366 days."))
        if self.vehicle and self.donor:
            vehicle_donor = frappe.db.get_value(
                "Vehicle", self.vehicle, "ugavi_donor"
            )
            if vehicle_donor and vehicle_donor != self.donor:
                frappe.throw(_("The selected vehicle belongs to a different donor."))

    def get_report_data(self):
        """Collect fleet utilization metrics for the given period."""
        vehicle_filters = {"name": self.vehicle} if self.vehicle else {}
        if self.donor:
            vehicle_filters["ugavi_donor"] = self.donor
        vehicles = frappe.get_all(
            "Vehicle",
            filters=vehicle_filters,
            fields=["name", "license_plate", "make", "model", "ugavi_status"],
        )
        data = []
        for v in vehicles:
            trip_filters = {"vehicle": v.name, "docstatus": 1}
            if self.donor:
                trip_filters["donor"] = self.donor
            if self.from_date and self.to_date:
                trip_filters["start_date"] = ("between", [self.from_date, self.to_date])
            elif self.from_date:
                trip_filters["start_date"] = (">=", self.from_date)
            elif self.to_date:
                trip_filters["start_date"] = ("<=", self.to_date)
            trips = frappe.get_all(
                "Trip Log",
                filters=trip_filters,
                fields=["distance", "start_date", "end_date"],
            )
            fuel_conditions = [
                "vehicle = %s",
                "date BETWEEN %s AND %s",
                "docstatus = 1",
            ]
            fuel_params = [v.name, self.from_date, self.to_date]
            if self.donor:
                fuel_conditions.append("donor = %s")
                fuel_params.append(self.donor)
            fuel = frappe.db.sql(f"""
                SELECT SUM(litres) as total_litres, SUM(total_cost) as total_cost
                FROM `tabFuel Log`
                WHERE {" AND ".join(fuel_conditions)}
            """, tuple(fuel_params), as_dict=True)[0]

            total_km = sum(t.distance or 0 for t in trips)
            total_hours = sum(
                frappe.utils.time_diff_in_hours(t.end_date, t.start_date)
                for t in trips
                if t.start_date and t.end_date
            )
            total_litres = fuel.total_litres or 0
            avg_kmpl = round(total_km / total_litres, 2) if total_litres > 0 else 0

            # Spare parts costs for this period
            spare_conditions = [
                "sp.vehicle = %s",
                "sp.docstatus = 1",
                "sp.issue_date BETWEEN %s AND %s",
            ]
            spare_params = [v.name, self.from_date, self.to_date]
            if self.donor:
                spare_conditions.append("sp.donor = %s")
                spare_params.append(self.donor)
            spare_parts = frappe.db.sql(f"""
                SELECT COALESCE(SUM(pi.amount), 0) as total_cost
                FROM `tabSpare Parts Issue` sp
                INNER JOIN `tabFleet Spare Part Item` pi ON pi.parent = sp.name
                WHERE {" AND ".join(spare_conditions)}
            """, tuple(spare_params), as_dict=True)[0]

            reconciliation_donor_clause = " AND donor = %s" if self.donor else ""
            reconciliation_params = [self.donor] if self.donor else []
            unallocated = frappe.db.sql(
                f"""SELECT COALESCE(SUM(remaining_qty), 0)
                    FROM `tabFleet Purchase Reconciliation`
                    WHERE status IN ('Open', 'Partially Allocated')
                    {reconciliation_donor_clause}""",
                tuple(reconciliation_params),
            )[0][0]

            # Fuel efficiency anomaly check
            anomaly_flag = ""
            if total_km > 0 and total_litres > 0:
                avg = total_km / total_litres
                donor_clause = " AND donor = %s" if self.donor else ""
                fleet_params = [self.from_date, self.to_date]
                if self.donor:
                    fleet_params.append(self.donor)
                fleet_stats = frappe.db.sql(f"""
                    SELECT SUM(litres) as fl, MAX(odometer) - MIN(odometer) as td
                    FROM `tabFuel Log`
                    WHERE docstatus = 1 AND date BETWEEN %s AND %s
                      AND odometer IS NOT NULL
                      {donor_clause}
                """, tuple(fleet_params), as_dict=True)
                if fleet_stats and fleet_stats[0].td and fleet_stats[0].fl:
                    fleet_avg = fleet_stats[0].td / fleet_stats[0].fl
                    deviation = abs(avg - fleet_avg) / fleet_avg * 100 if fleet_avg > 0 else 0
                    if deviation > 20:
                        anomaly_flag = f"⚠ {deviation:.0f}% off fleet avg"

            data.append({
                "vehicle": v.name,
                "make_model": f"{v.make or ''} {v.model or ''}".strip() or v.license_plate,
                "total_trips": len(trips),
                "total_distance": total_km,
                "total_hours": round(total_hours, 1),
                "fuel_used": round(total_litres, 1),
                "fuel_cost": fuel.total_cost or 0,
                "spare_parts_cost": spare_parts.total_cost or 0,
                "unallocated_purchases": unallocated,
                "avg_kmpl": avg_kmpl,
                "efficiency_anomaly": anomaly_flag,
                "status": v.ugavi_status or "Active",
            })
        return sorted(data, key=lambda x: x["total_distance"], reverse=True)

    def generate(self):
        self.generated_at = now_datetime()
        self.report_data = frappe.as_json(self.get_report_data())
        self.save()

    @staticmethod
    def get_dashboard_metrics():
        """Return fleet dashboard KPIs for the fleet workspace."""
        from frappe.utils import today, add_days

        total_vehicles = frappe.db.count("Vehicle", {"disabled": 0})
        active_allocations = frappe.db.count(
            "Vehicle Allocation",
            {"status": "Active"},
        )
        fuel_this_month = frappe.db.sql("""
            SELECT COALESCE(SUM(total_cost), 0)
            FROM `tabFuel Log`
            WHERE MONTH(date) = MONTH(CURDATE())
              AND YEAR(date) = YEAR(CURDATE())
              AND docstatus = 1
        """)[0][0] or 0

        # Vehicles due for service in the next 7 days
        service_due_soon = frappe.db.count(
            "Vehicle",
            {
                "disabled": 0,
                "ugavi_next_service_date": ("<=", add_days(today(), 7)),
            },
        )

        # Monthly cost trend (last 3 months)
        monthly_costs = frappe.db.sql("""
            SELECT
                DATE_FORMAT(date, '%%Y-%%m') as month,
                COALESCE(SUM(total_cost), 0) as cost
            FROM `tabFuel Log`
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
              AND docstatus = 1
            GROUP BY DATE_FORMAT(date, '%%Y-%%m')
            ORDER BY month
        """, as_dict=True)

        return {
            "total_vehicles": total_vehicles,
            "active_allocations": active_allocations,
            "fuel_cost_this_month": fuel_this_month,
            "service_due_soon": service_due_soon,
            "monthly_fuel_costs": monthly_costs,
        }

    @staticmethod
    def get_maintenance_schedule():
        """Return upcoming maintenance events sorted by service date."""
        from frappe.utils import today

        vehicles = frappe.get_all(
            "Vehicle",
            filters={
                "disabled": 0,
                "ugavi_next_service_date": (">=", today()),
            },
            fields=[
                "name", "license_plate", "make", "model",
                "ugavi_next_service_date", "ugavi_status",
                "last_odometer",
            ],
            order_by="ugavi_next_service_date",
        )
        for v in vehicles:
            days_until = (
                frappe.utils.getdate(v.ugavi_next_service_date)
                - frappe.utils.getdate(today())
            ).days
            v["days_until_service"] = days_until

        return vehicles