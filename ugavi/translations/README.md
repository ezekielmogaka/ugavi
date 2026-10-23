# i18n Translation Scaffold

# Ugavi supports localization for all user-facing strings using
# Frappe's standard translation framework.

# Translation files are stored in:
#   ugavi/translations/<lang>.csv

# To generate translation strings for a new language:
#   1. bench console
#   2. frappe.get_doc({"doctype": "Translation", "source_text": "Purchase Requisition",
#       "translated_text": "Demande d'Achat", "language": "fr"}).insert()

# Supported languages for MVP:
#   en — English (default)
#   sw — Swahili (planned)
#   fr — French (planned)

# RTL languages are not in scope for MVP (GA-038 accepted).