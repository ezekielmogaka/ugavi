import frappe


def get_context(context):
    context.full_width = True
    context.title = "Field updates — LOKADO"
    context.now_year = frappe.utils.now_datetime().year
    context.metatags = {
        "description": "Programme stories and field updates from LOKADO in Turkana County."
    }
