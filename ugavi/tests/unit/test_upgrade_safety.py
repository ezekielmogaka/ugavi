"""Upgrade-safety contract tests for ERPNext extension boundaries."""

import inspect
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import frappe
from frappe.utils import add_days, today


class TestPortalThemeSetup(unittest.TestCase):
    def test_desk_and_public_surfaces_share_lokado_brand_tokens(self):
        from ugavi.scripts import setup_config

        settings = MagicMock(
            brand_color="#142D4E",
            accent_color="#D6A85F",
            company_name="LOKADO",
            enable_command_palette=1,
            enable_smart_home=1,
            default_theme_mode="Light",
            base_font_size="Default",
            default_density="Comfortable",
            corner_radius=8,
        )
        with patch.object(setup_config, "frappe") as framework:
            framework.db.exists.return_value = True
            framework.get_single.return_value = settings
            setup_config._configure_desk_theme()

        self.assertEqual(settings.brand_color, "#18388F")
        self.assertEqual(settings.accent_color, "#2D7D3A")
        settings.save.assert_called_once_with(ignore_permissions=True)

    def test_website_home_and_navigation_are_configured_natively(self):
        from ugavi.scripts import setup_config

        website = MagicMock(app_name="Frappe", home_page=None, top_bar_items=[])
        navbar = MagicMock(app_logo=None)
        contact = MagicMock(
            is_disabled=1,
            forward_to_email=None,
            send_acknowledgement_email=None,
            query_options=None,
        )
        with patch.object(setup_config, "frappe") as framework:
            framework.db.exists.return_value = True
            framework.get_single.side_effect = {
                "Navbar Settings": navbar,
                "Website Settings": website,
                "Contact Us Settings": contact,
            }.__getitem__
            setup_config._configure_navbar_branding()

        self.assertEqual(website.app_name, "LOKADO")
        self.assertEqual(website.home_page, "index")
        self.assertEqual(website.append.call_count, 8)
        website.save.assert_called_once_with(ignore_permissions=True)
        self.assertEqual(contact.is_disabled, 0)
        self.assertEqual(contact.forward_to_email, "info@lokado.org")
        contact.save.assert_called_once_with(ignore_permissions=True)

    def test_public_site_pages_use_app_owned_frappe_templates(self):
        app_root = Path(__file__).resolve().parents[2]
        for route in (
            "index",
            "about",
            "leadership",
            "programmes",
            "updates",
            "impact",
            "contact",
            "privacy",
        ):
            template = (app_root / "www" / f"{route}.html").read_text()
            controller = app_root / "www" / f"{route}.py"
            self.assertIn('extends "templates/lokado_web_base.html"', template)
            self.assertTrue(controller.exists(), route)
        self.assertIn(
            'extends "www/index.html"',
            (app_root / "www" / "website.html").read_text(),
        )
        home = (app_root / "www" / "index.html").read_text()
        self.assertIn('class="lokado-partner-list"', home)
        self.assertEqual(home.count("/assets/ugavi/images/partners/"), 9)

    def test_supplier_portal_uses_colocated_frappe_page_assets(self):
        portal_root = (
            Path(__file__).resolve().parents[2]
            / "www"
            / "supplier"
        )
        template = (portal_root / "dashboard.html").read_text()

        self.assertIn('extends "templates/lokado_web_base.html"', template)
        self.assertIn("ugavi-portal--v2", template)
        self.assertTrue((portal_root / "dashboard.css").exists())

    def test_public_pages_bridge_published_solvronix_tokens_only(self):
        from ugavi import hooks

        self.assertIn(
            "/assets/ugavi/js/lokado_theme_bridge.js",
            hooks.web_include_js,
        )
        bridge = (
            Path(__file__).resolve().parents[2]
            / "public"
            / "js"
            / "lokado_theme_bridge.js"
        ).read_text()
        self.assertIn("solvronix_desk.api.get_theme_css", bridge)
        self.assertNotIn("solvronix_desk/css/solvronix_desk.css", bridge)
        self.assertIn("sessionStorage.getItem", bridge)
        self.assertIn("sessionStorage.setItem", bridge)

    def test_only_solvronix_desk_is_installed_from_the_ecosystem(self):
        import solvronix_desk

        installed = set(frappe.get_installed_apps())
        self.assertEqual(solvronix_desk.__version__, "3.2.0")
        self.assertIn("solvronix_desk", installed)
        self.assertNotIn("solvronix_pilot_connector", installed)
        self.assertNotIn("edvronix", installed)

    def test_supplier_identity_conflict_fails_closed(self):
        from ugavi.procurement.portal import supplier_portal

        with patch.object(supplier_portal, "frappe") as framework:
            framework.db.get_value.return_value = "CONTACT-1"
            framework.get_all.side_effect = [
                ["Supplier A"],
                ["Supplier B"],
            ]
            framework.throw.side_effect = frappe.ValidationError("ambiguous identity")
            with self.assertRaisesRegex(frappe.ValidationError, "ambiguous identity"):
                supplier_portal._get_supplier_for_user("supplier@example.com")

    def test_supplier_workspace_exposes_session_controls(self):
        portal = (
            Path(__file__).resolve().parents[2]
            / "www"
            / "supplier"
            / "dashboard.html"
        ).read_text()

        self.assertIn("data-supplier-logout", portal)
        self.assertIn('role="tablist"', portal)
        self.assertIn('data-portal-view="overview"', portal)

    def test_colors_exist_before_theme_save_and_activation(self):
        from ugavi.scripts import setup_config

        settings = MagicMock(website_theme="Standard")
        theme = MagicMock(name="theme")
        theme.name = "LOKADO Portal"
        colors = set()

        def exists(doctype, name):
            return doctype == "DocType" or (doctype == "Color" and name in colors)

        def get_doc(data):
            if data["doctype"] == "Color":
                color = MagicMock()
                color.insert.side_effect = lambda **kwargs: colors.add(data["name"])
                return color
            self.assertEqual(data["custom"], 1)
            return theme

        def save(**kwargs):
            self.assertEqual(len(colors), 5)
            settings.save.assert_not_called()

        theme.save.side_effect = save
        with patch.object(setup_config, "frappe") as framework:
            framework.db.exists.side_effect = exists
            framework.get_doc.side_effect = get_doc
            framework.get_single.return_value = settings
            setup_config._configure_portal_theme()

        theme.save.assert_called_once_with(ignore_permissions=True)
        self.assertEqual(settings.website_theme, theme.name)
        settings.save.assert_called_once_with(ignore_permissions=True)

    def test_theme_save_failure_does_not_activate_missing_theme(self):
        from ugavi.scripts import setup_config

        with patch.object(setup_config, "frappe") as framework:
            framework.db.exists.return_value = True
            framework.get_doc.return_value.save.side_effect = ValueError("Compile failed")
            with self.assertRaisesRegex(ValueError, "Compile failed"):
                setup_config._configure_portal_theme()
            framework.get_single.assert_not_called()
            framework.db.set_single_value.assert_not_called()

    def test_existing_active_theme_is_preserved(self):
        from ugavi.scripts import setup_config

        with patch.object(setup_config, "frappe") as framework:
            framework.db.exists.return_value = True
            settings = MagicMock(website_theme="Customer Theme")
            framework.get_single.return_value = settings
            setup_config._configure_portal_theme()
            self.assertEqual(settings.website_theme, "Customer Theme")
            settings.save.assert_not_called()

    def test_migration_repairs_only_missing_active_lokado_theme(self):
        from ugavi.scripts import setup_config

        for active, exists, expected in (
            ("LOKADO Portal", False, True),
            ("LOKADO Portal", True, False),
            ("Customer Theme", False, False),
            ("Standard", False, False),
            (None, False, False),
        ):
            with (
                self.subTest(active=active, exists=exists),
                patch.object(setup_config, "frappe") as framework,
                patch.object(setup_config, "_configure_portal_theme") as configure,
            ):
                framework.db.get_single_value.return_value = active
                framework.db.exists.return_value = exists
                setup_config.repair_portal_theme_before_migrate()
                self.assertEqual(configure.called, expected)


class TestUpgradeSafety(unittest.TestCase):
    def test_logistics_workspace_opens_stock_ledger_as_report(self):
        workspace_path = (
            Path(__file__).resolve().parents[2]
            / "logistics"
            / "workspace"
            / "ugavi-logistics"
            / "ugavi-logistics.json"
        )
        workspace = json.loads(workspace_path.read_text())
        stock_ledger = next(
            link
            for link in workspace["links"]
            if link.get("label") == "Stock Ledger"
        )

        self.assertEqual(stock_ledger["link_to"], "Stock Ledger")
        self.assertEqual(stock_ledger["link_type"], "Report")
        self.assertEqual(stock_ledger["is_query_report"], 1)

    def test_existing_logistics_workspace_link_is_repaired(self):
        from ugavi.scripts import setup_config

        link = MagicMock(
            label="Stock Ledger",
            link_type="DocType",
            link_to="Stock Ledger",
            is_query_report=0,
        )
        link.name = "workspace-link-stock-ledger"
        workspace = MagicMock(links=[link])
        with patch.object(setup_config, "frappe") as framework:
            framework.get_doc.return_value = workspace
            setup_config.configure_workspace_links()

        framework.db.set_value.assert_called_once_with(
            "Workspace Link",
            "workspace-link-stock-ledger",
            {
                "link_type": "Report",
                "link_to": "Stock Ledger",
                "is_query_report": 1,
            },
            update_modified=False,
        )
        framework.clear_cache.assert_called_once_with(doctype="Workspace")

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

    def test_purchase_requisition_uses_single_canonical_client_script(self):
        from ugavi import hooks

        script = (
            Path(__file__).resolve().parents[2]
            / "procurement"
            / "doctype"
            / "purchase_requisition"
            / "purchase_requisition.js"
        ).read_text()

        self.assertNotIn("Purchase Requisition", hooks.doctype_js)
        self.assertIn("Submit for Approval", script)
        self.assertIn("submit_for_approval", script)
        self.assertIn("frm.call('create_tender')", script)
        self.assertNotIn(
            "purchase_requisition.create_tender",
            script,
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
