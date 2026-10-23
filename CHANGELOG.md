# Changelog

All notable changes to Ugavi are documented in this file.

## [0.1.0] — 2026-10-21

### Added — LOKADO Demo (First Customer)
- **LOKADO Seed Script** (`ugavi/scripts/seed_lokado.py`): 868 lines, 19 functions, idempotent, production-guarded
- **LOKADO Demo Tour** (`docs/demo/LOKADO-DEMO-TOUR.md`): 10-scene, 25-30 min walkthrough
- **Customer-specific data**: 15 users (real Turkana names), 6 donors (IOM, USAID, Concern, Japan, EU, Own Funds)
- **12 suppliers**: including Nadirkonyen Women's Group (Kakuma community-based collective)
- **15 items**: Galla goats, WASH tanks, construction materials, hygiene kits, motorcycles
- **6 warehouses**: Lodwar, Kakuma, Lokichoggio, Oropoi, Kitale Transit
- **Full procurement workflow**: 6 PRs, 5 tenders, 15 bids, 1 award, 1 contract with milestones
- **Governance**: DoA, SoD, Waiver, Audit, supplier prequalification (9 active, 1 expired, 1 suspended)
- **Logistics**: Donor-warehouse links, 2 stock reports, 1 inter-donor transfer (IOM → Concern, flood emergency)
- **Makefile target**: `make seed-lokado`

### Added — Phase A-E
- **Procurement**: Purchase Requisition, Supplier Prequalification, Tender, Bid, Bid Opening Record
- **Sealed-Bid Crypto**: Shamir's Secret Sharing (3-of-3) + RSA-4096 envelope + AES-256-GCM
- **Logistics**: Donor Warehouse, Stock Ledger, Inter-Donor Transfer, Monthly Stock Report
- **Assets**: Asset Register, Asset Movement, Asset Disposal, Asset Verification
- **Fleet**: Vehicle, Vehicle Allocation, Trip Log, Fuel Log, Spare Parts Issue
- **Governance**: DoA matrix, hash-chain audit logs, rate limiter, feature flags
- **UI**: 5 JS client scripts, 6 role-based workspaces, 3 dashboards, supplier portal
- **Print Formats**: Purchase Requisition, Tender, Bid
- **Tests**: 27 tests (12 integration + 15 unit), 3 e2e workflow tests, concurrency tests
- **Scheduler**: Weekly/monthly asset verification, vehicle service, supplier flagging, key rotation
- **Monitoring**: Health check endpoint, structured JSON logging
- **ADR**: 6 architectural decisions (multi-tenancy, sealed-bid crypto, AI features, rules engine, UI strategy, DoA)
- **Fixtures**: Generic demo data seed + LOKADO customer-specific seed
- **Security**: Threat model, OWASP ASVS mapping, pen-test checklist
- **CI/CD**: GitHub Actions pipeline (lint, test, e2e, security scan, SBOM, container scan, docs check, load test)
- **Non-Functional Requirements**: 24 NFRs documented (performance, security, availability, maintainability, compliance, demo)

### Known Limitations
- No offline/PWA support (documented in mobile-offline-evaluation.md)
- No i18n translations beyond English (Swahili/French planned)
- No eTIMS integration (Kenya tax compliance requires eTIMS API — planned v0.2)
- No SSO/SAML integration (planned v0.3)
- No load testing or chaos engineering performed

### Upcoming (v0.2)
- eTIMS tax integration
- Supplier mobile portal
- Swahili translations
- Load testing with k6
- CI/CD pipeline with security scanning

---

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Ugavi follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).