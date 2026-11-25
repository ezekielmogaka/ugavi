import frappe


def get_context(context):
    context.full_width = True
    context.title = "Our programmes — LOKADO"
    context.now_year = frappe.utils.now_datetime().year
    context.metatags = {"description": "Explore LOKADO programmes in peacebuilding, livelihoods, WASH, climate resilience, protection and institutional strengthening."}
