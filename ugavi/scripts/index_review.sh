#!/bin/bash
# Index Review Script — verify optimal indexes for donor-segregated queries (GA-050)
# Usage: bench execute ugavi.scripts.index_review.review_indexes

echo "==> Ugavi Index Review ==="
echo ""

# Check if bench is available
if command -v bench &> /dev/null; then
    SITE=$(bench site 2>/dev/null || echo "site1.local")
else
    echo "bench not found — run from frappe-bench directory"
    exit 1
fi

echo "Site: $SITE"
echo ""

# Critical indexes for donor-segregated queries
echo "--- Critical Donor-Segregated Indexes ---"
INDICES=(
    "Purchase Requisition:donor:Donor filter on PR queries"
    "Purchase Requisition:status:PR status filtering"
    "Tender:status:Tender status filtering (Published, Closed)"
    "Bid:tender:Bid lookup by tender"
    "Bid:supplier:Supplier bid history"
    "Bid:status:Bid status filtering"
    "Stock Ledger:donor:Donor stock balance queries"
    "Stock Ledger:item_code:Item stock queries"
    "Stock Ledger:warehouse:Warehouse stock filtering"
    "Donor Warehouse:donor:Donor warehouse lookup"
    "Asset Register:donor:Donor asset queries"
    "Vehicle:status:Vehicle status filtering"
    "Trip Log:vehicle:Vehicle trip history"
    "Fuel Log:vehicle:Vehicle fuel efficiency queries"
    "Supplier Prequalification:supplier:Supplier PQ status"
    "Sealed Bid Key:tender:Tender key lookup"
    "Audit Log:reference_doctype:Audit log queries"
    "Audit Log:reference_name:Audit log by document"
)

for idx in "${INDICES[@]}"; do
    IFS=':' read -r doctype field desc <<< "$idx"
    echo -n "  $doctype.$field: "
    
    # Check if index exists via MariaDB
    TABLE="tab$(echo "$doctype" | sed 's/ //g')"
    HAS_INDEX=$(bench --site "$SITE" execute frappe.db.sql --kwargs "{'query':'SHOW INDEX FROM \\`$TABLE\\` WHERE Column_name = \\'$field\\''}" 2>/dev/null | wc -l)
    
    if [ "$HAS_INDEX" -gt 2 ]; then
        echo "✅ Present ($desc)"
    else
        echo "⚠️  MISSING — $desc"
        echo "      Add via: bench --site $SITE execute frappe.db.sql --kwargs \"{'query':'CREATE INDEX idx_${TABLE}_${field} ON \\`$TABLE\\`($field)'}\""
    fi
done

echo ""
echo "--- Composite Index Check ---"
# Check composite index for Stock Ledger (donor + item_code + warehouse)
COMPOSITE=$(bench --site "$SITE" execute frappe.db.sql --kwargs "{'query':'SHOW INDEX FROM \\`tabStock Ledger\\` WHERE Column_name = \\'donor\\' AND Seq_in_index = 1'}" 2>/dev/null | wc -l)
if [ "$COMPOSITE" -gt 2 ]; then
    echo "  ✅ Stock Ledger donor composite index present"
else
    echo "  ⚠️  Missing composite index on Stock Ledger (donor, item_code, warehouse)"
fi

echo ""
echo "==> Index review complete."