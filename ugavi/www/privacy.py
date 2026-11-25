import frappe


def get_context(context):
    context.full_width = True
    context.title = "Privacy & data use — LOKADO"
    context.now_year = frappe.utils.now_datetime().year
    context.metatags = {
        "description": "Privacy and data-use summary for the LOKADO public website and Ugavi supplier portal."
    }
