"""Tender — lifecycle management with sealed-bid support."""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

from ugavi.procurement.portal.supplier_portal import notify_supplier_users


class Tender(Document):
    """Tender with publishing, sealed bids, and award workflow."""

    def validate(self):
        self._validate_officers()
        self._validate_deadline()

    def _validate_officers(self):
        officers = [
            self.opening_officer_1,
            self.opening_officer_2,
            self.opening_officer_3,
        ]
        # Only validate if all officers are set
        if (
            any(officers)
            and not all(officers)
            and self.procurement_method in ("Restricted Tender", "Open Tender")
        ):
            frappe.throw("All 3 Bid Opening Officers must be assigned for sealed-bid tenders")
        if all(officers):
            if len(set(officers)) != 3:
                frappe.throw("Bid Opening Officers must be 3 distinct users")
            for officer in officers:
                roles = frappe.get_roles(officer)
                if "Evaluation Committee" in roles:
                    frappe.throw(
                        _("Opening officer {0} cannot also serve on the evaluation committee").format(
                            officer
                        )
                    )

    def _validate_deadline(self):
        if (
            self.submission_deadline
            and self.publish_date
            and get_datetime(self.submission_deadline) <= get_datetime(self.publish_date)
        ):
            frappe.throw("Submission deadline must be after publish date")

    @frappe.whitelist()
    def publish(self):
        """Publish the tender and generate encryption keys if needed."""
        if self.status != "Draft":
            frappe.throw("Only draft tenders can be published")
        if self.procurement_method in ("Restricted Tender", "Open Tender"):
            officers = [
                self.opening_officer_1,
                self.opening_officer_2,
                self.opening_officer_3,
            ]
            if not all(officers) or len(set(officers)) != 3:
                frappe.throw(_("Three distinct opening officers are required"))

        # Verify bid security officers if required
        if (
            self.bid_security_required
            and self.bid_security_required > 0
            and not self.opening_officer_1
        ):
            frappe.throw("At least Officer 1 must be set when bid security is required")

        self.publish_date = now_datetime()

        # Generate sealed-bid keypair for restricted/open tenders
        if self.procurement_method in ("Restricted Tender", "Open Tender"):
            self._generate_keys()

        self.status = "Published"
        self.save()

    def _generate_keys(self):
        from ugavi.procurement.services.sealed_bid import generate_and_distribute_keys
        result = generate_and_distribute_keys(
            tender=self.name,
            officers=[
                self.opening_officer_1,
                self.opening_officer_2,
                self.opening_officer_3,
            ],
        )
        self.public_key = result["public_key_pem"]
        self.key_generated_at = now_datetime()

    def _store_private_key(self, private_pem):
        """DEPRECATED — key is now split at generation, never stored in DB."""
        frappe.throw(
            "Private keys must never be stored in the database. "
            "Use generate_and_distribute_keys instead."
        )

    def _require_procurement_role(self):
        if not {"Procurement Officer", "System Manager"}.intersection(frappe.get_roles()):
            frappe.throw(_("Only a Procurement Officer can perform this action."), frappe.PermissionError)

    @frappe.whitelist()
    def get_award_recommendation(self) -> dict:
        """Approved recommendation and standstill state used by the Desk actions."""
        from ugavi.tendering.services.evaluation import approved_recommendation

        recommendation = approved_recommendation(self.name) or {}
        standstill = frappe.db.get_value(
            "Standstill Period",
            {"tender": self.name},
            ["name", "status", "resolution", "end_date"],
            order_by="creation desc",
            as_dict=True,
        ) or {}
        return {"recommendation": recommendation, "standstill": standstill}

    @frappe.whitelist()
    def start_standstill(self):
        """Issue the intended-award notice and open the complaint window."""
        from ugavi.tendering.doctype.standstill_period.standstill_period import (
            initiate_standstill,
        )
        from ugavi.tendering.services.evaluation import (
            approved_recommendation,
            assert_recommendation_supported,
        )

        self._require_procurement_role()
        if self.status != "Under Evaluation":
            frappe.throw(_("A standstill can only start while the tender is Under Evaluation."))
        recommendation = approved_recommendation(self.name)
        if not recommendation:
            frappe.throw(_("An approved Bid Evaluation Summary is required before the standstill."))
        assert_recommendation_supported(
            self.name, recommendation.recommended_bidder, recommendation.recommended_amount
        )
        standstill = initiate_standstill(self.name, recommendation.recommended_bidder)
        self.status = "Standstill Period"
        self.save()
        return standstill

    @frappe.whitelist()
    def confirm_standstill(self):
        """Confirm the intended award once the standstill has ended without open complaints."""
        from ugavi.tendering.doctype.standstill_period.standstill_period import (
            resolve_standstill,
        )

        self._require_procurement_role()
        if self.status != "Standstill Period":
            frappe.throw(_("The tender is not in a standstill period."))
        return resolve_standstill(self.name, "Award Confirmed")

    @frappe.whitelist()
    def award(self, supplier: str, amount: float):
        """Award the confirmed recommendation and issue the Purchase Order."""
        from ugavi.tendering.services.evaluation import (
            approved_recommendation,
            assert_recommendation_supported,
        )

        self._require_procurement_role()
        if self.status != "Standstill Period":
            frappe.throw(_("Tender must complete its standstill period before award."))
        standstill = frappe.db.get_value(
            "Standstill Period",
            {"tender": self.name},
            ["status", "resolution"],
            order_by="creation desc",
            as_dict=True,
        )
        if (
            not standstill
            or standstill.status != "Resolved"
            or standstill.resolution != "Award Confirmed"
        ):
            frappe.throw(
                _("The award requires a completed standstill with no unresolved complaint.")
            )
        recommendation = approved_recommendation(self.name)
        if not recommendation or recommendation.recommended_bidder != supplier:
            frappe.throw(_("Only the approved recommended bidder can be awarded."))
        amount = float(amount)
        if abs(amount - float(recommendation.recommended_amount or 0)) > 0.01:
            frappe.throw(_("Award amount must match the approved recommendation."))
        bid = assert_recommendation_supported(self.name, supplier, amount)

        requisition = frappe.get_doc("Purchase Requisition", self.purchase_requisition)
        settings = frappe.get_single("Ugavi Procurement Settings")
        schedule_date = frappe.utils.add_days(None, 30)
        po = frappe.get_doc(
            {
                "doctype": "Purchase Order",
                "supplier": supplier,
                "company": settings.default_company,
                "ugavi_pr": requisition.name,
                "ugavi_tender": self.name,
                "ugavi_donor": self.donor,
                "ugavi_procurement_method": self.procurement_method,
                "transaction_date": now_datetime().date(),
                "schedule_date": schedule_date,
            }
        )
        for item, rate in zip(requisition.items, _award_rates(requisition.items, amount)):
            po.append(
                "items",
                {
                    "item_code": item.item_code,
                    "qty": item.quantity,
                    "rate": rate,
                    "uom": item.uom,
                    "schedule_date": schedule_date,
                },
            )
        po.insert()
        po.submit()
        contract_name = frappe.db.get_value(
            "Ugavi Contract", {"purchase_order": po.name}, "name"
        )
        if contract_name:
            frappe.db.set_value(
                "Ugavi Contract", contract_name, "tender", self.name, update_modified=False
            )

        frappe.get_doc("Bid", bid["bid"]).db_set("status", "Accepted")
        self.awarded_supplier = supplier
        self.award_amount = amount
        self.purchase_order = po.name
        self.status = "Awarded"
        self.save()
        notify_supplier_users(
            supplier,
            _("Tender award issued"),
            _("Your organization was awarded tender {0}. Purchase order: {1}.").format(
                self.name, po.name
            ),
            "Tender",
            self.name,
        )
        frappe.msgprint(
            _("Purchase Order {0} and Contract {1} created").format(po.name, contract_name or "-")
        )
        return {"purchase_order": po.name, "contract": contract_name}

    @frappe.whitelist()
    def close(self):
        """Close the tender."""
        self.status = "Closed"
        self.save()

    @frappe.whitelist()
    def issue_addendum(self, title: str, description: str, extends_deadline: bool = False,
                       new_deadline: str | None = None, attachment: str | None = None):
        """Add an addendum to the tender and optionally extend submission deadline."""
        if self.status not in {"Published", "Bids Received"}:
            frappe.throw(_("Addenda may only be issued for an open tender."))
        if get_datetime(self.submission_deadline) <= now_datetime():
            frappe.throw(_("An addendum cannot be issued after the submission deadline."))
        if extends_deadline and (
            not new_deadline
            or get_datetime(new_deadline) <= get_datetime(self.submission_deadline)
        ):
            frappe.throw(_("The revised deadline must be later than the current deadline."))
        next_num = len(self.addenda) + 1
        self.append("addenda", {
            "addendum_number": next_num,
            "title": title,
            "issue_date": now_datetime().date(),
            "description": description,
            "attachment": attachment,
            "extends_deadline": 1 if extends_deadline else 0,
            "new_deadline": new_deadline,
            "issued_by": frappe.session.user,
            "issued_at": now_datetime(),
        })
        if extends_deadline and new_deadline:
            self.submission_deadline = new_deadline
            frappe.msgprint(_("Submission deadline extended to {0}").format(new_deadline))
        self.save()
        suppliers = frappe.get_all(
            "Bid", filters={"tender": self.name}, pluck="supplier"
        )
        for supplier in set(suppliers):
            notify_supplier_users(
                supplier,
                _("Tender addendum issued"),
                _("Addendum {0} was issued for tender {1}.").format(
                    next_num, self.name
                ),
                "Tender",
                self.name,
            )
        return next_num

    @frappe.whitelist()
    def apply_document_template(self, template: str) -> int:
        if self.status != "Draft":
            frappe.throw(_("Document templates may only be applied in Draft."))
        source = frappe.get_doc("Tender Document Template", template)
        if source.status != "Active":
            frappe.throw(_("Only an active tender document template may be used."))
        self.append(
            "tender_documents",
            {
                "document_name": source.template_name,
                "document_type": source.document_type,
                "attachment": source.attachment,
                "description": source.description,
                "document_version": source.version,
                "source_template": source.name,
            },
        )
        self.save()
        return len(self.tender_documents)

    @frappe.whitelist()
    def verify_bid_security(self, bid_name: str) -> bool:
        """Check if a bid has a valid bid security that meets the tender requirement."""
        if not self.bid_security_required or self.bid_security_required <= 0:
            return True  # No security required
        bid_sec = frappe.db.get_value("Bid Security",
                                       {"bid": bid_name, "tender": self.name},
                                       ["name", "security_amount", "status", "verification_status", "valid_until"], as_dict=True)
        if not bid_sec:
            frappe.throw(_("Bid {0} has no bid security on file").format(bid_name))
        if bid_sec.status != "Held":
            frappe.throw(_("Bid security {0} is not in Held status ({1})").format(
                bid_sec.name, bid_sec.status))
        if bid_sec.verification_status != "Verified":
            frappe.throw(
                _("Bid security {0} has not been independently verified.").format(
                    bid_sec.name
                )
            )
        if not bid_sec.valid_until or frappe.utils.getdate(
            bid_sec.valid_until
        ) < frappe.utils.getdate(self.bid_opening_date or frappe.utils.today()):
            frappe.throw(_("Bid security {0} expires before bid opening.").format(bid_sec.name))
        if bid_sec.security_amount < self.bid_security_required:
            frappe.throw(_("Bid security {0} ({1}) is below minimum {2}").format(
                bid_sec.name, bid_sec.security_amount, self.bid_security_required))
        return True


def _award_rates(items, amount: float) -> list[float]:
    """Scale requisition estimates so the order totals the awarded bid amount."""
    estimate = sum(float(row.quantity or 0) * float(row.estimated_unit_price or 0) for row in items)
    if estimate <= 0:
        frappe.throw(_("The source requisition needs estimated prices to allocate the award."))
    factor = amount / estimate
    rates = [round(float(row.estimated_unit_price or 0) * factor, 2) for row in items]
    allocated = sum(float(row.quantity or 0) * rate for row, rate in zip(items[:-1], rates[:-1]))
    last_qty = float(items[-1].quantity or 0)
    if last_qty:
        rates[-1] = round((amount - allocated) / last_qty, 2)
    total = sum(float(row.quantity or 0) * rate for row, rate in zip(items, rates))
    if abs(total - amount) >= 0.01:
        frappe.throw(
            _(
                "The awarded amount {0} cannot be split into unit rates over the requisition "
                "quantities (closest total {1}). Record the bid's unit prices before awarding."
            ).format(frappe.format_value(amount, "Currency"), frappe.format_value(total, "Currency"))
        )
    return rates
