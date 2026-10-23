# ADR-005: Integration — Custom DocTypes → Standard ERPNext Purchase Flow

**Status:** Accepted
**Date:** 2026-10-21
**Deciders:** Ugavi team (independent QA recommendation)

## Context
Ugavi has custom Tender, Bid, Sealed Bid Key, Bid Opening Record DocTypes that do not exist in standard ERPNext. After bid opening and evaluation, the awarded tender must create a standard Purchase Order for downstream ERPNext workflows (receiving, invoicing, payment).

## Decision
**Custom Tender/Bid DocTypes for the sealed phase. After opening and award, create standard ERPNext Request for Quotation (RFQ) and Supplier Quotation as the integration bridge.**

### Flow
```
PR → Tender(ugavi) → Bid(ugavi, encrypted) → Opening(ugavi) → Evaluation
  → Award → RFQ(ERPNext standard) → Supplier Quotation(ERPNext)
    → Purchase Order(ERPNext) → Receiving → Invoice → Payment
```

### Why RFQ not direct PO
ERPNext's standard procurement flow is: Purchase Requisition → RFQ → Supplier Quotation → Purchase Order. Creating RFQ/Supplier Quotation after award:
1. Provides an audit trail in standard ERPNext format
2. Enables standard reports and analytics
3. Does not require modifying ERPNext core DocTypes (upgrade-safe)
4. The `Tender.award()` method already creates a Purchase Order; we enhance it to create RFQ first

[verified: ERPNext Purchase Order, Request for Quotation, Supplier Quotation DocTypes exist in installed version]

## Upgrade Safety
- No core ERPNext DocType modifications
- Custom DocTypes are in `ugavi` namespace
- Integration via standard ERPNext API: `frappe.get_doc({"doctype": "Request for Quotation", ...}).insert()`
- The `override_doctype_class` hook only overrides Purchase Requisition (existing), not Purchase Order, RFQ, or Supplier Quotation

## Evidence
- [code] Tender.award() at tendering/doctype/tender/tender.py:70-95 already creates PO
- [verified] ERPNext has Request for Quotation, Supplier Quotation, Purchase Order DocTypes
- [verified] hooks.py override_doctype_class only overrides Purchase Requisition