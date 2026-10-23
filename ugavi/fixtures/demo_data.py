"""Fixtures — JSON-based demo data for Ugavi."""
import frappe


def run():
    """Seed the system with initial demo data.
    
    Usage: bench execute ugavi.fixtures.demo_data.run
    """
    _seed_roles()
    _seed_users()
    _seed_donors()
    _seed_settings()


def _seed_roles():
    roles = [
        "Procurement Officer",
        "Approver Level 1",
        "Approver Level 2",
        "Bid Opening Officer",
        "Evaluation Committee",
        "Fleet Manager",
        "Asset Manager",
        "Logistics Officer",
    ]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert()
            print(f"  Created role: {role}")


def _seed_users():
    """Create demo users for testing."""
    users = [
        ("procurement@ugavi.demo", "Procurement Officer", "Procurement Officer"),
        ("approver1@ugavi.demo", "Approver One", "Approver Level 1"),
        ("approver2@ugavi.demo", "Approver Two", "Approver Level 2"),
        ("opening1@ugavi.demo", "Opening Officer A", "Bid Opening Officer"),
        ("opening2@ugavi.demo", "Opening Officer B", "Bid Opening Officer"),
        ("opening3@ugavi.demo", "Opening Officer C", "Bid Opening Officer"),
        ("logistics@ugavi.demo", "Logistics Officer", "Logistics Officer"),
    ]
    for email, full_name, role_name in users:
        if not frappe.db.exists("User", email):
            user = frappe.get_doc({
                "doctype": "User",
                "email": email,
                "first_name": full_name,
                "roles": [{"role": role_name}],
                "send_welcome_email": 0,
            })
            user.insert(ignore_permissions=True)
            print(f"  Created user: {email} ({role_name})")


def _seed_donors():
    """Create sample donor profiles."""
    donors = [
        ("USAID", "United States Agency for International Development",
         "usaid@demo.org", "Donor-funded health supply chain"),
        ("Global Fund", "The Global Fund to Fight AIDS, TB and Malaria",
         "globalfund@demo.org", "Health systems strengthening"),
        ("UNICEF", "United Nations Children's Fund",
         "unicef@demo.org", "Maternal and child health"),
    ]
    for name, full_name, email, description in donors:
        if not frappe.db.exists("Donor Profile", name):
            frappe.get_doc({
                "doctype": "Donor Profile",
                "donor_name": name,
                "full_name": full_name,
                "contact_email": email,
                "description": description,
                "status": "Active",
            }).insert()
            print(f"  Created donor: {name}")


def _seed_settings():
    """Create default procurement settings."""
    if not frappe.db.exists("Ugavi Procurement Settings", "Ugavi Procurement Settings"):
        frappe.get_doc({
            "doctype": "Ugavi Procurement Settings",
            "direct_threshold": 200000,
            "restricted_threshold": 500000,
            "default_currency": "KES",
            "auto_close_tenders_days": 30,
            "prequalification_validity_days": 365,
        }).insert()
        print("  Created ugavi procurement settings")