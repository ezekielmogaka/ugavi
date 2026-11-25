import frappe


def get_context(context):
    context.no_cache = True
    context.full_width = True
    context.now_year = frappe.utils.now_datetime().year
    context.title = "LOKADO"
    context.metatags = {
        "description": (
            "LOKADO is a community-led organization advancing peace, resilient "
            "livelihoods and accountable development across Turkana County."
        )
    }
