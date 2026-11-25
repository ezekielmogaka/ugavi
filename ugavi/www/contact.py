import frappe


def get_context(context):
    context.full_width = True
    context.title = "Contact LOKADO"
    context.now_year = frappe.utils.now_datetime().year
    context.metatags = {"description": "Contact LOKADO for partnerships, programme, supplier and field coordination enquiries in Turkana County."}
