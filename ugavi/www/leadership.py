import frappe


def get_context(context):
    context.full_width = True
    context.title = "Leadership — LOKADO"
    context.now_year = frappe.utils.now_datetime().year
    context.metatags = {
        "description": "Meet LOKADO's public leadership team in Turkana County, Kenya."
    }
