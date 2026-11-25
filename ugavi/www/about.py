import frappe


def get_context(context):
    context.full_width = True
    context.title = "Who we are — LOKADO"
    context.now_year = frappe.utils.now_datetime().year
    context.metatags = {"description": "LOKADO's story, vision, values and community-led mission in Turkana County."}
