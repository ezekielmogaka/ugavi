# ADR-003: AI-Assisted Features — Declined for MVP

**Status:** Accepted  
**Date:** 2026-10-19  
**Deciders:** Ugavi team (AI-assisted analysis)

## Context

The requirements scope mentions optional AI-assisted features:
- Summarizing evaluation comparisons
- Searching over procurement documents
- Potential: anomaly detection in bids

## Decision

**Decline all AI-assisted features for MVP.**

### Reasons:
1. **Sealed-bid boundary is non-negotiable**: Any AI summarization of evaluation data could expose bidder identities or pricing before formal opening. Even post-opening, donor confidentiality requirements may prohibit sending procurement data to external model providers.
2. **Human approval remains mandatory**: AI assistance would only assist, not replace, human evaluation. The cost-benefit of building, testing, and auditing an AI adapter (with proper data sanitization) does not justify the value at MVP stage.
3. **Provider independence**: If adopted later, AI must be behind an adapter pattern (like SMS and eTIMS), off by default, and fully audited.
4. **Regulatory uncertainty**: Kenya's data protection landscape (Data Protection Act 2019) and donor agreements (USAID, EU, etc.) may impose restrictions on AI processing of procurement data.

## Future Path

If AI features are requested in production:
1. Implement an adapter pattern in `ugavi/integrations/ai/` with provider abstraction
2. Hard constraints:
   - No sealed-bid data leaves tenant boundary before opening
   - No confidential bid data reaches external model before authorization
   - Human approval always required
   - Off by default
   - Fully audited with data lineage tracking
3. Consider local/self-hosted models (e.g., Ollama, llama.cpp) to avoid data exfiltration risk

## Consequences

- **Positive:** No privacy/security risk from AI data leakage. Faster MVP delivery. Cleaner audit posture.
- **Negative:** Missed opportunity for evaluation efficiency. May need to revisit if competitors offer AI features.
- **Risk:** Low — decision is reversible. Adapter pattern committed in architecture.

## References
- `[assumption: Kenya Data Protection Act 2019 applies to procurement data processing]`
- `[verified: ugavi/integrations/ — SMS adapter pattern can be replicated for AI]`