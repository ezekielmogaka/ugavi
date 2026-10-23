# API Reference — Ugavi 0.1.0

All endpoints are accessible via Frappe REST API: `POST /api/method/<path>`

## Health & Monitoring

### Health Check
```
GET /api/method/ugavi.scripts.health_check.get_health
```
Returns: `{"status": "healthy", "db": "connected", "cache": "connected", "scheduler": "active"}`

### Hash Chain Verification
```
POST /api/method/ugavi.governance.services.hash_chain.verify_chain
{"doctype": "Tender", "docname": "TENDER-001"}
```
Returns: `{"intact": true, "total_entries": 15, "broken_at": null}`

---

## Procurement

### Create Purchase Requisition
```
POST /api/method/frappe.client.insert
{
 "doc": {
  "doctype": "Purchase Requisition",
  "requisition_title": "...",
  "donor": "DONOR-001",
  "requisition_date": "2026-10-19",
  "status": "Draft"
 }
}
```

### Submit Bid (Supplier Portal)
```
POST /api/method/ugavi.procurement.portal.supplier_portal.submit_bid
{
  "tender": "TND-2026-0001",
  "bid_amount": 50000.00,
  "bid_currency": "KES",
  "delivery_days": 14,
  "technical_proposal": "/private/files/proposal.pdf"
}
```

### Submit Prequalification
```
POST /api/method/ugavi.procurement.portal.supplier_portal.submit_prequalification
{
  "category": "Construction Materials",
  "expiry_date": "2027-10-22",
  "documents": "[{\"document_type\":\"Tax Compliance\",\"attachment\":\"/private/files/tax.pdf\"}]"
}
```

### Update Supplier Profile
```
POST /api/method/ugavi.procurement.portal.supplier_portal.update_supplier_profile
{
  "mobile_no": "+254700000000",
  "email_id": "supplier@example.org",
  "website": "https://example.org",
  "tax_id": "P000000000A"
}
```

### Submit Clarification
```
POST /api/method/ugavi.procurement.portal.supplier_portal.submit_clarification
{"tender": "TND-2026-0001", "question": "Please confirm the delivery location."}
```

### Submit Tender Complaint
```
POST /api/method/ugavi.procurement.portal.supplier_portal.submit_tender_complaint
{
  "tender": "TND-2026-0001",
  "grounds": "The published evaluation did not apply criterion 3 as stated.",
  "supporting_document": "/private/files/complaint-evidence.pdf"
}
```

Only a bidder linked to the authenticated supplier may submit during an active
Standstill Period. A supplier may not create a second unresolved complaint for
the same tender.

### Submit Supplier Invoice
```
POST /api/method/ugavi.procurement.portal.supplier_portal.submit_supplier_invoice
{
  "purchase_receipt": "MAT-PRE-2026-00001",
  "supplier_invoice_number": "INV-4582",
  "supplier_invoice_date": "2026-10-22",
  "invoice_file": "/private/files/invoice-4582.pdf"
}
```

The endpoint creates a draft ERPNext Purchase Invoice using the native
Purchase Receipt mapper. Quantities, rates, purchase-order links and receipt
links are server-derived; the attachment must be private and owned by the
authenticated supplier user.

### Acknowledge Purchase Order
```
POST /api/method/ugavi.procurement.portal.supplier_portal.acknowledge_purchase_order
{"purchase_order": "PUR-ORD-2026-00001"}
```

### Mark Supplier Notification Read
```
POST /api/method/ugavi.procurement.portal.supplier_portal.mark_notification_read
{"notification": "abc123"}
```

Supplier portal methods use the authenticated session to resolve the Supplier. They never accept a supplier identifier from the caller. File URLs must identify private files owned by the current user.

---

## Sealed-Bid Crypto

### Generate Keypair (Admin only)
```
POST /api/method/ugavi.procurement.services.sealed_bid.generate_tender_keypair
{"tender": "TENDER-001"}
```

### Reconstruct Key (3-of-3 officers)
```
POST /api/method/ugavi.procurement.services.sealed_bid.reconstruct_key
{"tender": "TENDER-001", "share_1": "...", "share_2": "...", "share_3": "..."}
```

### Decrypt Bid
```
POST /api/method/ugavi.procurement.services.sealed_bid.decrypt_bid
{"bid": "BID-001", "reconstructed_key": "..."}
```

---

## Asset Management

### Register Asset
```
POST /api/method/frappe.client.insert
{
 "doc": {
  "doctype": "Asset Register",
  "asset_name": "Vehicle Toyota Land Cruiser",
  "donor": "DONOR-001",
  "asset_category": "Vehicle",
  "purchase_cost": 45000,
  "location": "Nairobi HQ"
 }
}
```

### Record Asset Movement
```
POST /api/method/ugavi.ugavi_assets.doctype.ugavi_asset_movement.ugavi_asset_movement.confirm
{"asset": "ASSET-001", "from_location": "Warehouse A", "to_location": "Warehouse B", "donor": "DONOR-001"}
```

---

## Fleet

### Log Trip
```
POST /api/method/frappe.client.insert
{
 "doc": {
  "doctype": "Trip Log",
  "vehicle": "VEH-001",
  "start_odometer": 50000,
  "end_odometer": 50250,
  "destination": "Mombasa",
  "purpose": "Delivery"
 }
}
```

---

## Feature Flags

### Check Flag
```
GET /api/method/ugavi.governance.services.feature_flags.is_enabled?flag_name=rate_limiting
```
Returns: `true` or `false`

### List All Flags
```
GET /api/method/ugavi.governance.services.feature_flags.list_flags
```
Returns: `{"rate_limiting": true, "sealed_bid_key_rotation": false, ...}`

### Toggle Flag (Admin)
```
POST /api/method/ugavi.governance.services.feature_flags.enable
{"flag_name": "sealed_bid_key_rotation"}
```

---

## Authentication

All API calls require Frappe authentication:
- **Header**: `Authorization: token <api_key>:<api_secret>`
- **Alternatively**: Session cookie from `POST /api/method/login`