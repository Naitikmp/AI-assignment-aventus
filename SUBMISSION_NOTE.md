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

### Enterprise Design Patterns (Strategy & Factory)
The core workflow decouples policy evaluation from LLM synthesis:
- **Factory Pattern (`ProviderFactory`):** Detects environment configuration and routes to `LocalPolicyProvider`, `AzureOpenAIProvider` (enterprise Microsoft AI stack), or `OpenAIProvider`.
- **Graceful Fallback:** If cloud credentials are misconfigured, the system automatically falls back to `local` mode without interrupting the user.

### Comprehensive Test Automation
A full `pytest` suite tests ingestion, duplicate filtering, regional rule matching, flight duration threshold logic (< 6 hrs vs. > 6 hrs), and out-of-scope refusals.

---

## 2. What I Would Implement With Additional Time

Given additional time, I would expand this foundation into a full enterprise expense intelligence platform:

1. **Microsoft Ecosystem Integration (Copilot Studio & Teams):**
   - Package the policy engine into a Microsoft Copilot Studio Action via a REST API (FastAPI) and Power Automate flow, allowing employees to query policy directly within Microsoft Teams.

2. **Enterprise Scale with Azure AI Search (RAG at Scale):**
   - For scaling across thousands of complex policy documents, employee handbooks, and country-specific tax addendums, replace the in-memory index with Azure AI Search utilizing hybrid search (BM25 keyword search + dense vector embeddings with semantic re-ranking).

3. **Multimodal Receipt Validation (Azure Document Intelligence):**
   - Integrate multimodal receipt parsing (using Azure AI Document Intelligence or GPT-4o Vision) so employees can upload a hotel bill or meal receipt, extract line items, and have the system automatically audit the receipt against daily limits before submission.

4. **Human-in-the-Loop (HITL) Exception Management:**
   - Add automated workflow routing to allow employees to submit exception requests (e.g., booking a hotel exceeding the $300 limit due to a conference) to a department manager for approval.
