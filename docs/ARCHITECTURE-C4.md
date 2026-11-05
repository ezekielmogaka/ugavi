# C4 Architecture — Ugavi 0.1.0

## Level 1: System Context

```mermaid
C4Context
    title System Context — Ugavi SCM on ERPNext/Frappe v16

    Person(procurement_officer, "Procurement Officer", "Creates PRs, publishes tenders, opens bids")
    Person(supplier, "Supplier", "Submits bids and PQ documents via portal")
    Person(logistics_officer, "Logistics Officer", "Manages stock, transfers, reports")
    Person(fleet_manager, "Fleet Manager", "Manages vehicles, trips, fuel")
    Person(approver, "Approver", "Approves PRs, waivers, transfers per DoA")

    System(ugavi, "Ugavi SCM", "Procurement, tendering, logistics, fleet, governance")
    System(erpnext, "ERPNext 16", "Finance, inventory, assets, HR")
    System(kra_etims, "KRA eTIMS", "Tax invoice management system")
    
    BiRel(procurement_officer, ugavi, "Manage procurement")
    BiRel(supplier, ugavi, "Submit bids")
    BiRel(logistics_officer, ugavi, "Manage stock")
    BiRel(fleet_manager, ugavi, "Manage fleet")
    BiRel(approver, ugavi, "Approve")
    Rel(ugavi, erpnext, "Extends via hooks", "Frappe API")
    Rel(ugavi, kra_etims, "Submit invoices", "REST (scaffold)")
```

## Level 2: Container

```mermaid
C4Container
    title Container Diagram — Ugavi

    Person(user, "User", "Staff or supplier")

    System_Boundary(platform, "Frappe Bench") {
        Container(nginx, "Nginx", "Reverse proxy, TLS, security headers", "Serves static + proxies")
        Container(frappe_app, "Frappe App", "Python 3.14", "Ugavi + ERPNext + Frappe")
        Container(mariadb, "MariaDB 11.8", "Relational DB", "Donor-segregated data")
        Container(valkey, "Valkey 9", "In-Memory", "Cache, queue, rate limiter")
        Container(worker, "Background Worker", "Python", "Scheduled jobs, email, reports")
    }

    Rel(user, nginx, "HTTPS", "443")
    Rel(nginx, frappe_app, "Proxy", "8000")
    Rel(frappe_app, mariadb, "SQL", "3306")
    Rel(frappe_app, valkey, "Cache/Queue", "6379")
    Rel(worker, mariadb, "SQL", "3306")
    Rel(worker, valkey, "Queue", "6379")
```

## Level 3: Component — Ugavi App

```mermaid
C4Component
    title Component Diagram — Ugavi App Structure

    Container_Boundary(ugavi_app, "Ugavi App") {
        Component(procurement, "Procurement", "Python", "PR, PO, Contracts, Waivers")
        Component(tendering, "Tendering", "Python", "Tenders, Bids, Sealed-Bid Crypto")
        Component(evaluation, "Evaluation", "Python", "COI, Scoring, Bid Summary, Standstill")
        Component(logistics, "Logistics", "Python", "Stock Ledger, Donor Warehouse, Transfers")
        Component(assets, "Assets", "Python", "Asset Register, Movement, Disposal")
        Component(fleet, "Fleet", "Python", "Vehicle, Trip, Fuel, Spares")
        Component(governance, "Governance", "Python", "Hash Chain, Rate Limiter, Metrics, Feature Flags")
        Component(integrations, "Integrations", "Python", "eTIMS, SMS, KRA PIN")
        Component(portal, "Supplier Portal", "Python + HTML", "Bid submission, PQ, Dashboard")
        Component(ui, "UI Theme", "CSS", "Design tokens, chips, timeline, skeleton")
    }

    Rel(procurement, tendering, "Publishes tenders from PRs")
    Rel(tendering, evaluation, "Bids → evaluation")
    Rel(tendering, governance, "Hash chain + rate limit")
    Rel(procurement, governance, "Feature flags + audit")
    Rel(logistics, governance, "Donor ledger integrity")
    Rel(portal, tendering, "Bid submission")
    Rel(portal, procurement, "PQ submission")
```

## Key Design Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| Single tenant, donor-as-dimension | Simplest ops; donor segregation via code | ADR-001 |
| RSA-4096 + AES-256-GCM sealed bids | Industry standard; SSS 3-of-3 key split | ADR-002 |
| AI features off-by-default, no sealed-bid data | Prevents data leakage; adapter pattern | ADR-003 |
| Frappe UI (Vue 3 + Tailwind) for Desk | Upgrade-safe; no separate frontend | ADR-005 |
| Zero core ERPNext patches | Guarantees upgrade safety; all via hooks | UG1/UG2 |

*Generated 2026-10-19. Diagrams in Mermaid format, rendered in CI.*