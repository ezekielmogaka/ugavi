"""Seed check — verify matrix coverage & schema validity."""
import frappe


def run():
    errors = []
    counts = {}

    # Check each module's record counts match expectations
    checks = [
        ("Donor Profile", 5),
        ("Supplier", 30),
        ("Supplier Prequalification", 30),
        ("Vehicle", 5),
        ("Vehicle Allocation", 4),
        ("Fuel Log", 6),
        ("Trip Log", 3),
        ("Asset Register", 5),
        ("Ugavi Asset Movement", 2),
        ("Asset Disposal", 1),
        ("Delegation of Authority", 5),
        ("Waiver", 1),
        ("Segregation of Duties", 3),
        ("Audit Log", 1),
        ("Purchase Requisition", 6),
        ("Tender", 6),
        ("Bid", 3),
        ("Bid Opening Record", 1),
        ("Ugavi Contract", 1),
        ("Ugavi Supplier Evaluation", 2),
        ("Donor Warehouse", 6),
        ("Monthly Stock Report", 4),
        ("Inter Donor Transfer", 1),
    ]

    for dt, expected in checks:
        actual = frappe.db.count(dt)
        counts[dt] = actual
        if actual < expected:
            errors.append(f"{dt}: expected >= {expected}, got {actual}")

    # Check specific values
    tender_values = [v[0] for v in frappe.db.get_values("Tender", filters={}, fieldname="estimated_value", pluck="estimated_value")]
    expected_values = {150000, 350000, 499000, 499500, 500000, 800000}
    found = set(tender_values)
    if not expected_values.issubset(found):
        errors.append(f"Tender values missing: {expected_values - found}")

    # Print result
    print(f"\n{'='*50}")
    print("SEED CHECK RESULTS")
    print(f"{'='*50}")
    for dt, count in sorted(counts.items()):
        status = "✅" if dt not in [e.split(":")[0] for e in errors] else "❌"
        print(f"  {status} {dt}: {count}")
    print()

    # Tender matrix
    print("Tender Value Matrix:")
    for v in tender_values:
        print(f"  {v:,} KES")
    print()

    if errors:
        print(f"FAILURES ({len(errors)}):")
        for e in errors:
            print(f"  ❌ {e}")
        return 1
    else:
        print("✅ All checks passed")
        return 0