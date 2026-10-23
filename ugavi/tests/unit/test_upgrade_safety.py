"""Upgrade-safety contract tests for ERPNext extension boundaries."""

import inspect
import unittest
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.utils import add_days, today


class TestUpgradeSafety(unittest.TestCase):
    def test_no_core_override_hooks_or_doctype_collisions(self):
        from ugavi.scripts.check_upstream_compatibility import get_report

        report = get_report()
        self.assertTrue(report["compatible"], report["issues"])

    def test_supplier_portal_uses_shared_tokens(self):
        from ugavi import hooks

        self.assertIn(
            "/assets/ugavi/css/ugavi-tokens.css",
            hooks.web_include_css,
        )
        self.assertIn(
            "/assets/ugavi/css/ugavi-components.css",
            hooks.web_include_css,
        )

    def test_supplier_portal_commands_do_not_accept_arbitrary_fields(self):
        from ugavi.procurement.portal import supplier_portal

        commands = (
            supplier_portal.update_supplier_profile,
            supplier_portal.submit_prequalification,
            supplier_portal.submit_bid,
            supplier_portal.submit_clarification,
            supplier_portal.submit_tender_complaint,
            supplier_portal.submit_supplier_invoice,
            supplier_portal.acknowledge_purchase_order,
            supplier_portal.mark_notification_read,
        )
        for command in commands:
            parameters = inspect.signature(command).parameters.values()
            self.assertNotIn(
                inspect.Parameter.VAR_KEYWORD,
                {item.kind for item in parameters},
                command.__name__,
            )

    def test_supplier_journey_uses_both_open_tender_states(self):
        from ugavi.procurement.portal.supplier_portal import OPEN_TENDER_STATUSES

        self.assertEqual(OPEN_TENDER_STATUSES, ("Published", "Bids Received"))

    def test_mvp2_complaint_controller_uses_conventional_discovery(self):
        from ugavi.tendering.doctype.tender_complaint.tender_complaint import (
            TenderComplaint,
        )

        self.assertEqual(TenderComplaint.__name__, "TenderComplaint")

    def test_mvp2_uses_native_erpnext_lifecycle_hooks(self):
        from ugavi import hooks

        self.assertIn("Purchase Invoice", hooks.doc_events)
        self.assertIn("Purchase Order", hooks.doc_events)
        self.assertEqual(
            hooks.doc_events["Purchase Receipt"]["validate"],
            "ugavi.procurement.events.validate_purchase_receipt",
        )

    def test_asset_qr_print_does_not_call_third_party(self):
        template = Path(
            frappe.get_app_path(
                "ugavi",
                "ugavi_assets",
                "doctype",
                "asset_register",
                "asset_qr_tag.html",
            )
        ).read_text()
        self.assertNotIn("api.qrserver.com", template)
        self.assertIn("doc.get_qr_data_uri()", template)

    def test_supplier_home_page_hook_is_registered(self):
        from ugavi import hooks

        self.assertEqual(
            hooks.get_website_user_home_page,
            "ugavi.procurement.portal.supplier_portal.get_home_page",
        )


class TestTenderComplaintBoundary(unittest.TestCase):
    def _complaint(self):
        return frappe.get_doc({
            "doctype": "Tender Complaint",
            "tender": "TND-TEST",
            "standstill_period": "SSP-TEST",
            "supplier": "Supplier TEST",
            "submitted_by": "supplier@example.com",
            "grounds": "Evaluation criterion was not applied.",
            "status": "Submitted",
        })

    def test_bidder_with_active_standstill_is_allowed(self):
        complaint = self._complaint()
        standstill = frappe._dict({
            "tender": "TND-TEST",
            "status": "Active",
            "end_date": add_days(today(), 2),
        })
        with (
            patch("frappe.db.get_value", return_value=standstill),
            patch("frappe.db.exists", return_value=True),
        ):
            complaint._validate_submission_window()

    def test_expired_standstill_is_rejected(self):
        complaint = self._complaint()
        standstill = frappe._dict({
            "tender": "TND-TEST",
            "status": "Active",
            "end_date": add_days(today(), -1),
        })
        with (
            patch("frappe.db.get_value", return_value=standstill),
            patch("frappe.db.exists", return_value=True),
            self.assertRaises(frappe.ValidationError),
        ):
            complaint._validate_submission_window()

    def test_non_bidder_is_rejected(self):
        complaint = self._complaint()
        standstill = frappe._dict({
            "tender": "TND-TEST",
            "status": "Active",
            "end_date": add_days(today(), 2),
        })
        with (
            patch("frappe.db.get_value", return_value=standstill),
            patch("frappe.db.exists", return_value=False),
            self.assertRaises(frappe.ValidationError),
        ):
            complaint._validate_submission_window()

    def test_resolution_cannot_skip_review(self):
        complaint = self._complaint()
        complaint.status = "Upheld"
        previous = frappe._dict({"status": "Submitted"})
        with (
            patch.object(complaint, "get_doc_before_save", return_value=previous),
            self.assertRaises(frappe.ValidationError),
        ):
            complaint._validate_status_transition()

    def test_review_panel_rejects_conflicted_member(self):
        complaint = self._complaint()
        complaint.status = "Under Review"
        complaint.append(
            "review_panel",
            {"user": "a@example.com", "panel_role": "Chairperson"},
        )
        complaint.append(
            "review_panel",
            {
                "user": "b@example.com",
                "panel_role": "Secretary",
                "has_conflict": 1,
            },
        )
        complaint.append(
            "review_panel",
            {"user": "c@example.com", "panel_role": "Member"},
        )
        with self.assertRaises(frappe.ValidationError):
            complaint._validate_review_panel()


class TestMVP2ControlBoundaries(unittest.TestCase):
    def test_legal_hold_blocks_deletion(self):
        from ugavi.governance.services.retention import enforce_record_disposal

        doc = frappe._dict({"doctype": "Tender", "name": "TND-TEST"})
        with (
            patch("frappe.db.exists", return_value=True),
            self.assertRaises(frappe.ValidationError),
        ):
            enforce_record_disposal(doc)

    def test_etims_never_returns_synthetic_acknowledgement(self):
        from ugavi.integrations.etims_client import ETIMSClient

        client = object.__new__(ETIMSClient)
        with self.assertRaises(frappe.ValidationError):
            client.submit_invoice("TEST-INVOICE")

    def test_tenant_manifest_rejects_shared_stack_identity(self):
        from ugavi.scripts.validate_tenant_manifest import validate

        tenant = {
            "tenant_id": "lokado",
            "site_name": "scm.lokado.example",
            "compose_project": "ugavi-lokado",
            "http_port": 8443,
            "primary_region": "ke-nairobi-primary",
            "dr_region": "ke-nairobi-dr",
        }
        duplicate = dict(tenant, tenant_id="another")
        errors = validate({"tenants": [tenant, duplicate]})
        self.assertTrue(any("site_name must be unique" in error for error in errors))
