import frappe


def get_context(context):
    context.full_width = True
    context.title = "Impact & accountability — LOKADO"
    context.now_year = frappe.utils.now_datetime().year
    context.metatags = {"description": "How LOKADO uses community feedback, monitoring and traceable operations for accountable programme impact."}
