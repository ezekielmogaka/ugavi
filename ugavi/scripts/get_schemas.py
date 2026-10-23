import frappe

def run():
    doctypes = [
        "Asset Register", "Vehicle", "Vehicle Allocation", "Fuel Log", "Trip Log",
        "Delegation of Authority", "Donor Profile", "Donor Warehouse",
        "Purchase Requisition", "Tender", "Ugavi Contract", "Ugavi Supplier Evaluation",
        "Supplier Prequalification", "Segregation of Duties", "Waiver",
        "Budget Encumbrance", "Stock Ledger", "Monthly Stock Report", "Inter-Donor Transfer"
    ]
    for dt in doctypes:
        try:
            meta = frappe.get_meta(dt)
            print(f"=== {dt} ===")
            for f in meta.fields:
                skip = {"name","owner","creation","modified","modified_by","docstatus","idx","parent","parentfield","parenttype","_assign","_comments","_liked_by","_user_tags"}
                if f.fieldname in skip:
                    continue
                t = f"{f.fieldname}:{f.fieldtype}"
                if f.reqd:
                    t += "(reqd)"
                if f.fieldtype in ("Table", "Table MultiSelect"):
                    t += f"[table:{f.options}]"
                if f.options and f.fieldtype == "Link":
                    t += f"[link:{f.options}]"
                print(f"  {t}")
        except Exception as e:
            print(f"=== {dt} === ERROR: {e}")
