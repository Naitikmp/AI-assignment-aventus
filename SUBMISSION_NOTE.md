# Technical Assessment Submission Note

**Role:** Junior AI Engineer  
**Candidate:** Naitik Patel  
**Submission Date:** September 2026  

---

## 1. Key Engineering Highlights

### Out-of-the-Box Zero-Friction Execution
The solution is architected to run immediately without requiring any API keys, third-party accounts, paid services, or model downloads. The default `LocalPolicyProvider` evaluates queries against the policy dataset deterministically, delivering zero-latency, citation-backed answers.

### Strict Grounding & Explicit Out-of-Scope Enforcement
In corporate expense compliance, hallucination is unacceptable. The assistant includes an explicit guardrail layer:
- If an expense category or region is covered (e.g. UAE meals at $90 USD/day, UK hotel at $220 USD/night), it states the exact policy rules with citations.
- If a query is outside policy coverage (e.g. *Taxi in Dubai* when taxis are only defined for the UK; *Car Rental*; or unsupported regions like Germany), the engine explicitly identifies that the expense is not covered and defines the valid boundaries.

### Ingestion Hygiene & Deduplication
The policy dataset contains a deliberate duplicate row (row 14: UK Meals). The ingestion engine (`PolicyLoader`) applies business-identity deduplication, dropping redundant records and logging the action, with automated tests confirming that only clean, unique policy records enter the index.

### Modular Architecture (Provider Abstraction & Factory Pattern)
The core workflow decouples policy evaluation from response generation:
- **Factory Pattern (`ProviderFactory`):** Detects environment configuration and routes to `LocalPolicyProvider`, `OpenRouterProvider` (supporting free open-source models), or `OpenAIProvider`.
- **Graceful Fallback:** If cloud credentials are not supplied or fail to initialize, the system automatically defaults to `local` mode without interrupting execution.

### Comprehensive Test Automation
A full `pytest` suite tests ingestion, duplicate filtering, regional rule matching, flight duration threshold logic (< 6 hrs vs. > 6 hrs), and out-of-scope refusals.

---

## 2. What I Would Implement With Additional Time

With additional time, I would extend this solution along three practical paths:

1. **Receipt Parsing & Automated Pre-Audit (Multimodal Document Intelligence):**
   - Add OCR and receipt extraction (using multimodal vision models or document AI) so employees can upload receipt photos or PDF invoices to extract amounts, dates, and categories, automatically auditing them against daily policy limits prior to claim submission.

2. **Scaling Retrieval for Multi-Document Policy Handbooks (Hybrid Search):**
   - If policy documents expand beyond structured CSV tables into multi-page unstructured PDF handbooks and country addendums, transition the retrieval layer to hybrid search (combining BM25 lexical matching with dense semantic embeddings and metadata filtering) to preserve precision and row-level traceability at scale.

3. **Collaboration Platform Integration (Microsoft Teams / Slack Bot):**
   - Expose the agent via a lightweight FastAPI REST endpoint and connect it as a bot in Microsoft Teams or Slack, enabling employees to check policy allowances directly from their day-to-day workflow.
