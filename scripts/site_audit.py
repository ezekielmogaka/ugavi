import frappe
frappe.init(site='ugavi.localhost')
frappe.connect()

print("=== Company ===")
for c in frappe.get_all('Company', fields=['name', 'default_currency', 'country']):
    print(f"  {c.name} | {c.default_currency} | {c.country}")

print("\n=== Fiscal Year ===")
for fy in frappe.get_all('Fiscal Year', fields=['name', 'year_start_date', 'year_end_date']):
    print(f"  {fy.name}: {fy.year_start_date} to {fy.year_end_date}")

print(f"\n=== Accounts: {frappe.db.count('Account')} ===")

print("\n=== Currencies ===")
for c in frappe.get_all('Currency', filters={'enabled': 1}, fields=['name'], limit=8):
    print(f"  {c.name}")

print("\n=== Roles ===")
for r in frappe.get_all('Role', fields=['name'], limit=20):
    print(f"  {r.name}")

print(f"\n=== Warehouses: {frappe.db.count('Warehouse')} ===")
for w in frappe.get_all('Warehouse', fields=['name', 'warehouse_name', 'company'], limit=10):
    print(f"  {w.name} | {w.warehouse_name} | {w.company}")

print("\n=== Ugavi DocTypes ===")
for dt in frappe.get_all('DocType', filters={'module': ('in', ['Procurement','Tendering','Compliance','Governance','Logistics','Fleet','Assets'])}, fields=['name', 'module'], limit=50):
    print(f"  [{dt.module}] {dt.name}")

print(f"\n=== Items: {frappe.db.count('Item')}, Suppliers: {frappe.db.count('Supplier')} ===")

print("\n=== Donor Profiles ===")
for d in frappe.get_all('Donor Profile', fields=['donor_name', 'donor_code']):
    print(f"  {d.donor_code}: {d.donor_name}")

print("\n=== Ugavi Procurement Settings ===")
try:
    s = frappe.get_single('Ugavi Procurement Settings')
    print(f"  direct_threshold: {s.direct_threshold}")
    print(f"  restricted_threshold: {s.restricted_threshold}")
    print(f"  open_threshold: {s.open_threshold}")
    print(f"  sealed_bid_enabled: {s.sealed_bid_enabled}")
    print(f"  default_currency: {s.default_currency}")
except Exception as e:
    print(f"  Error: {e}")

frappe.destroy()