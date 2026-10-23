# Glossary — Ugavi

> **Ugavi** — Swahili for "supply" / "provision"

| Term | Definition |
|------|------------|
| **ADR** | Architecture Decision Record — documents a key architectural choice with rationale and trade-offs |
| **AES-256-GCM** | Advanced Encryption Standard with 256-bit key in Galois/Counter Mode — used for bid encryption |
| **Asset Register** | Record of all fixed assets (vehicles, equipment, buildings) with donor attribution |
| **Asset Verification** | Periodic physical count and condition check of assets |
| **Bid** | A supplier's priced offer for a tender — encrypted (sealed) until opening date |
| **Bid Opening Record (BOR)** | Official document recording the opening of sealed bids with 3-of-3 officers present |
| **Circuit Breaker** | Pattern that stops cascading failures when a downstream service fails |
| **Delegation of Authority (DoA)** | Matrix defining who can approve procurement at which value thresholds |
| **Donor** | Funding organization with segregated financial and stock tracking |
| **Donor Segregation** | Each procurement/stock document is tagged with a donor; cross-donor access is blocked |
| **eTIMS** | Kenya Revenue Authority electronic Tax Invoice Management System |
| **Feature Flag** | Runtime toggle to enable/disable functionality without deployment |
| **Frappe** | Open-source low-code web framework (Python/MariaDB) — Ugavi's platform |
| **Hash Chain** | Each audit log entry's hash includes the previous entry's hash, creating tamper-evident chain |
| **Inter-Donor Transfer** | Movement of stock from one donor's warehouse to another's (bilateral approval required) |
| **KRA PIN** | Kenya Revenue Authority Personal Identification Number — tax ID |
| **Print Format** | HTML template for generating PDF prints of documents |
| **Purchase Requisition (PR)** | Internal request to procure goods/services |
| **Rate Limiter** | Controls how many requests a user/IP can make in a time window |
| **RSA-4096** | Rivest-Shamir-Adleman public-key cryptosystem with 4096-bit key — envelope encryption |
| **SBOM** | Software Bill of Materials — inventory of all dependencies |
| **Sealed Bid** | Bid encrypted with public key; can only be decrypted by 3-of-3 key holders after opening date |
| **Shamir's Secret Sharing (SSS)** | Cryptographic algorithm that splits a secret into n shares, requiring k shares to reconstruct |
| **SSO** | Single Sign-On — authentication via central identity provider (SAML/OAuth) |
| **Stock Ledger** | Per-donor, per-item running balance of stock in/out movements |
| **Supplier Prequalification** | Vetting process to approve suppliers for restricted tenders |
| **Tender** | Public or restricted invitation for suppliers to submit bids |
| **Tender Opening Committee** | 3 designated officers who collectively hold key shares for bid decryption |
| **Threat Model** | Structured analysis of security threats and mitigations |
| **Trip Log** | Record of vehicle usage: start/end odometer, destination, purpose |
| **Workspace** | Role-specific Desk view showing relevant DocTypes, reports, and shortcuts |