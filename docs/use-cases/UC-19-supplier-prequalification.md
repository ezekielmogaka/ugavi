# UC-19: Supplier Prequalification Renewal

**ID:** UC-19 | **Actor(s):** Supplier, Procurement Officer | **Phase:** Supplier Management
**Requirements:** SP1, SP2, SP3, SP4, SP5

## Preconditions
- Supplier registered in the system
- Previous prequalification expired or expiring within 30 days
- Supplier has cumulative performance score ≥ 60 (from scorecard)

## Main Flow
1. System auto-notifies supplier 30 days before PQ expiry
2. Supplier updates documents (tax compliance, registration, references) via portal
3. Procurement Officer reviews documents → validates KRA PIN → approves/rejects
4. System checks cumulative supplier score (SP4 scorecard):
   - Score ≥ 60 → renewal approved
   - Score < 60 → auto-suspension (SP5)
5. New PQ issued with 12-month expiry
6. Supplier portal updated with new PQ status

## Business Rules
- **SP3-R1:** Auto-suspend supplier if PQ expires without renewal
- **SP4-R1:** Scorecard auto-generated after final receipt on every PO
- **SP5-R1:** Cumulative score < 60 → suspension; < 40 → permanent disqualification