# Corporate Travel Expense Policy Assistant

A reliable, lightweight AI assistant that answers employee questions about corporate travel expense policies. Built with an offline-first architecture, strict row-level citations, explicit out-of-scope guardrails, and automated deduplication.

> **Zero-Friction Default:** Runs out-of-the-box with **zero API keys, zero paid accounts, and zero model downloads**.

---

## ⚡ Quickstart

### 1. Install & Run (No API Key Needed)

```bash
# 1. Clone and navigate into the project
git clone https://github.com/Naitikmp/AI-assignment-aventus.git
cd AI-assignment-aventus

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ask a policy question directly
python main.py "What is the daily meal limit in UAE?"

# 4. Or launch interactive chat mode
python main.py
```

### 2. Docker Alternative (Optional)

```bash
docker build -t policy-agent .
docker run --rm policy-agent "What is the hotel allowance in London?"
```

---

## 🧪 Running Tests

The test suite validates data ingestion, duplicate purging, flight duration thresholds, and out-of-scope refusals:

```bash
pytest -v
```

All 18 automated tests run in `< 1` second.

---

## 🛠️ CLI Usage & Options

The CLI (`main.py`) supports both single-shot queries and an interactive session:

```bash
# Single question
python main.py "Can I expense a taxi in Dubai?"

# Custom CSV policy dataset
python main.py --data path/to/custom_policy.csv "What is the hotel allowance in US?"

# Force a specific provider ('local', 'openrouter', or 'openai')
python main.py --provider local "Do I need receipts for incidentals?"
```

| Argument | Description | Default |
| :--- | :--- | :--- |
| `query` | The expense question to evaluate. If omitted, starts interactive chat mode. | *None* |
| `--data` | Path to the policy CSV dataset. | `data/travel_expense_policy.csv` |
| `--provider` | Active synthesis engine (`local`, `openrouter`, `openai`). | `local` (or from `.env`) |

---

## 🎯 Core Features & Engineering Highlights

1. **Strict Grounding & Row Citations**  
   Every response is backed by exact CSV row citations (e.g. `[Row 4] Meals (United Arab Emirates): $90.00 USD`). The assistant never invents or assumes unstated rates.

2. **Explicit Out-of-Scope Guardrails**  
   If a question falls outside policy coverage, the assistant explicitly identifies the reason and refuses to speculate:
   - **Unsupported categories:** *Car rental*, *gym memberships*, *laundry*.
   - **Unsupported regions:** *Meals in Germany*.
   - **Regional service restrictions:** *Taxi in Dubai* (policy only reimburses taxis in the UK).

3. **Ingestion Hygiene & Deduplication**  
   The source dataset includes a duplicate entry (`Row 14: UK Meals`). The ingestion loader (`PolicyLoader`) applies business-key deduplication, automatically purging duplicates while logging stats.

4. **Offline by Default, Pluggable for Cloud LLMs**  
   Operates deterministically in `local` mode by default. Optional cloud providers can be activated via environment variables with an automatic graceful fallback to local mode if credentials fail.

---

## 🤖 Optional: Cloud LLM Integration

To enable cloud model synthesis instead of the local deterministic engine:

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Configure your preferred provider in `.env`:

   **OpenRouter (Supports free open-source models):**
   ```env
   LLM_PROVIDER=openrouter
   OPENROUTER_API_KEY=your_openrouter_api_key
   OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free
   ```

   **OpenAI:**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o-mini
   ```

*(If credentials are missing or invalid, the system automatically falls back to `local` mode to prevent runtime crashes.)*

---

## 📊 Policy Reference Data (`data/travel_expense_policy.csv`)

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

---

## 🏗️ Architecture

```
User Query (CLI / REPL)
       │
       ▼
┌───────────────────────────────┐
│       PolicyAssistant         │
│     (Workflow Controller)     │
└──────────────┬────────────────┘
               │
        ┌──────┴────────┐
        ▼               ▼
┌──────────────┐ ┌──────────────┐
│ PolicyIndex  │ │ PolicyLoader │
│ (Retrieval & │ │ (Deduplicate │
│  Guardrail)  │ │  & Validate) │
└──────┬───────┘ └──────────────┘
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[Status: COVERED]                        [Status: OUT_OF_SCOPE]
       │                                         │
       ▼                                         ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│       ProviderFactory        │        │   Explicit Policy Refusal    │
│  (Local / OpenRouter/ OpenAI)│        │  (Clear boundary statement)  │
└──────────────┬───────────────┘        └──────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Grounded Response Generator  │
│  (With Verifiable Citations) │
└──────────────────────────────┘
```

---

## 📁 Project Structure

```
.
├── data/
│   └── travel_expense_policy.csv        # Canonical policy dataset (12 rules + duplicate row 14)
├── src/
│   └── policy_agent/
│       ├── __init__.py                  # Public package exports
│       ├── config.py                    # Environment & configuration loader
│       ├── schemas.py                   # Pydantic data models & status enums
│       ├── ingestion.py                 # CSV ingestion & deduplication engine
│       ├── policy_index.py              # Search index, entity synonyms & guardrails
│       ├── workflow.py                  # High-level assistant orchestrator
│       └── providers/
│           ├── __init__.py
│           ├── base.py                  # Abstract base provider interface
│           ├── local_engine.py          # Deterministic grounded offline engine
│           ├── openrouter_provider.py   # OpenRouter integration (supports free models)
│           ├── openai_provider.py       # OpenAI integration
│           └── factory.py               # Provider factory with automatic fallback
├── tests/
│   ├── conftest.py                      # Shared test fixtures
│   ├── test_ingestion.py                # CSV loading & duplicate purge tests
│   ├── test_policy_index.py             # Rule matching & flight threshold tests
│   ├── test_out_of_scope.py             # Guardrail refusal tests
│   └── test_end_to_end.py               # End-to-end integration & citation tests
├── main.py                              # Interactive & one-shot CLI entrypoint
├── requirements.txt                     # Pinned project dependencies
├── pyproject.toml                       # Python package configuration
├── Dockerfile                           # Container definition
├── .dockerignore                        # Docker build ignore rules
├── .env.example                         # Environment configuration template
├── .gitignore                           # Git hygiene rules
├── README.md                            # Project documentation
├── SUBMISSION_NOTE.md                   # Assessment submission summary & roadmap
└── Technical_Assessment.pdf             # Original assessment specification
```
