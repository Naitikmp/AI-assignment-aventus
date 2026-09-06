# Corporate Travel Expense Policy Assistant

A focused, reliable AI assistant designed to answer corporate travel expense questions grounded strictly in organizational policy. Built with an offline-first architecture, explicit out-of-scope guardrails, data deduplication, and pluggable integration for Azure OpenAI and OpenAI.

---

## Key Features

- **Strict Grounding (Zero Hallucination):** Every answered query is verified against corporate policy records. Limits, room types, flight duration rules, and receipt requirements are cited with exact row references.
- **Out-of-Scope Policy Guardrail:** Automatically flags queries that fall outside corporate coverage (e.g., unsupported expense categories like car rental or personal expenses, or regions where specific services like taxis are not covered).
- **Data Ingestion & Deduplication:** Generic CSV parser that normalizes schema types, handles nullable limits, and cleans duplicate rows before indexing.
- **Deterministic Default Engine:** Operates instantly out-of-the-box with **zero external API keys, accounts, or model downloads required**.
- **Optional Cloud LLM Support:** Easily connects to **Azure OpenAI** or **OpenAI** when environment variables are supplied, with automatic fallback to local mode.
- **Interactive & Single-Shot CLI:** Formatted with terminal cards, status badges, and source citations.
- **Containerized:** Single-stage Docker support for reproducible deployment.

---

## Architecture

```
User Query (CLI / REPL)
       │
       ▼
┌───────────────────────────────┐
│       PolicyAssistant         │
│     (Workflow Controller)     │
└──────────────┬────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐ ┌──────────────┐
│ PolicyIndex  │ │ PolicyLoader │
│ (Retrieval & │ │ (Deduplicate │
│  Guardrail)  │ │  & Validate) │
└──────┬───────┘ └──────────────┘
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[Coverage Status: COVERED]           [Coverage Status: OUT_OF_SCOPE]
       │                                         │
       ▼                                         ▼
┌──────────────────────────────┐     ┌──────────────────────────────┐
│       ProviderFactory        │     │  Explicit Policy Refusal     │
│   (Local / Azure / OpenAI)   │     │  (Clear boundary statement)  │
└──────────────┬───────────────┘     └──────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Grounded Response Generator  │
│  (With Verifiable Citations) │
└──────────────────────────────┘
```

---

## Quickstart

### Option 1: Standard Python (Recommended)

Requires Python 3.10 or higher.

```bash
# 1. Clone the repository and navigate into the folder
cd travel-policy-agent

# 2. (Optional) Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run sample queries
python main.py "What is the daily meal limit in the United Arab Emirates?"
python main.py "Can I book business class for an 8-hour flight?"
python main.py "Can I expense a taxi in Dubai?"

# 5. Launch interactive chat mode
python main.py
```

### Option 2: Docker

```bash
# Build the Docker image
docker build -t policy-agent .

# Run a query in container
docker run --rm policy-agent "What is the hotel allowance in London?"
```

---

## Running Automated Tests

A comprehensive `pytest` test suite verifies data ingestion, deduplication, threshold matching, and out-of-scope guardrails:

```bash
pytest
```

To run with verbose output:
```bash
pytest -v
```

---

## Data Policy Reference (`travel_expense_policy.csv`)

| Category | Region | Daily Limit (USD) | Conditions / Notes |
| :--- | :--- | :--- | :--- |
| **Meals** | United Kingdom | $75.00 | Per day; includes tips |
| **Meals** | United States | $80.00 | Per day; includes tips |
| **Meals** | United Arab Emirates | $90.00 | Per day |
| **Meals** | India | $40.00 | Per day |
| **Hotel** | United Kingdom | $220.00 | Per night; standard room |
| **Hotel** | United States | $250.00 | Per night; standard room |
| **Hotel** | United Arab Emirates | $300.00 | Per night; standard room |
| **Hotel** | India | $120.00 | Per night; standard room |
| **Taxi** | United Kingdom | Actuals | Reimbursed at actuals; keep receipts |
| **Airfare** | Global | Rule | Economy only for flights under 6 hours |
| **Airfare** | Global | Rule | Business class permitted for flights over 6 hours |
| **Incidentals** | Global | $25.00 | Per day; no receipt required |

*Note: Ingestion automatically catches and purges duplicate rows (such as duplicate row 14) during load time.*

---

## Optional: Configuring Cloud LLM Providers

By default, the assistant runs in high-reliability **`local`** mode with deterministic synthesis. To enable cloud LLM synthesis:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure your desired provider:

**For Azure OpenAI (Enterprise Microsoft Stack):**
```env
LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**For standard OpenAI:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

*If credentials are missing or invalid, the assistant automatically falls back to `local` mode to prevent any runtime interruption.*

---

## Project Structure

```
.
├── data/
│   └── travel_expense_policy.csv        # Policy dataset
├── src/
│   └── policy_agent/
│       ├── __init__.py                  # Package exports
│       ├── config.py                    # Environment & provider settings
│       ├── schemas.py                   # Pydantic data models & status enums
│       ├── ingestion.py                 # CSV ingestion & deduplication engine
│       ├── policy_index.py              # Rule evaluation & guardrail index
│       ├── workflow.py                  # High-level assistant orchestrator
│       └── providers/
│           ├── __init__.py
│           ├── base.py                  # Base provider interface
│           ├── local_engine.py          # Deterministic grounded engine
│           ├── azure_openai.py          # Azure OpenAI integration
│           ├── openai_provider.py       # OpenAI integration
│           └── factory.py               # Provider factory
├── tests/
│   ├── conftest.py                      # Test fixtures
│   ├── test_ingestion.py                # Ingestion & deduplication tests
│   ├── test_policy_index.py             # Rule matching & threshold tests
│   ├── test_out_of_scope.py             # Guardrail & refusal tests
│   └── test_end_to_end.py               # Integration tests
├── main.py                              # Interactive & one-shot CLI
├── requirements.txt                     # Pinned dependencies
├── pyproject.toml                       # Python package configuration
├── Dockerfile                           # Container definition
├── .dockerignore                        # Docker ignore rules
├── .env.example                         # Environment configuration template
├── .gitignore                           # Git hygiene rules
├── README.md                            # Documentation
├── SUBMISSION_NOTE.md                   # Engineering highlights & roadmap
└── Technical_Assessment.pdf             # Original assessment specification
```
