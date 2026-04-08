# LLM Billing & Observability Platform

An enterprise-grade metered billing proxy for multi-tenant LLM applications. Acts as a transparent middleware layer that intercepts all LLM API calls, tracks token usage per client, calculates costs with configurable markups, enforces credit budgets, and provides AI-driven insights.

## Architecture

```
                                    ┌────────────────────────────┐
                                    │     Streamlit Dashboard    │
                                    │  (Admin + Client Panels)   │
                                    └─────────────┬──────────────┘
                                                  │
                                                  ▼
┌──────────────┐       ┌──────────────────────────────────────────────────────┐
│  Client App  │──────▶│                 FastAPI Backend                      │
│  (any LLM    │       │                                                      │
│   consumer)  │       │  /v1/chat/completions ──▶ Authenticate Tenant        │
└──────────────┘       │                              │                       │
                       │                         Check Credits                │
                       │                              │                       │
                       │                    Detect Provider (model name)      │
                       │                              │                       │
                       │              ┌───────────────┼───────────────┐       │
                       │              ▼               ▼               ▼       │
                       │         ┌─────────┐   ┌──────────┐   ┌────────┐     │
                       │         │ OpenAI  │   │Anthropic │   │ Gemini │     │
                       │         └────┬────┘   └────┬─────┘   └───┬────┘     │
                       │              └─────────────┼─────────────┘          │
                       │                            ▼                        │
                       │                  Extract Token Counts               │
                       │                  Calculate Cost + Markup            │
                       │                            │                        │
                       │              ┌─────────────┼──────────────┐         │
                       │              ▼             ▼              ▼         │
                       │         Return        Log Usage      Deduct        │
                       │         Response      Event (async)  Credits       │
                       │                                                     │
                       │  /tenants    ── Tenant CRUD + API key management    │
                       │  /usage      ── Usage analytics + breakdowns        │
                       │  /billing    ── Credit ledger + invoice previews    │
                       │  /ai         ── Anomaly detection + forecasting     │
                       └──────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
                                    ┌────────────────────────────┐
                                    │        PostgreSQL          │
                                    │  tenants | api_keys        │
                                    │  usage_events | credits    │
                                    └────────────────────────────┘
```

## Features

- **Transparent LLM Proxy** -- Clients point apps at the proxy instead of LLM providers directly; zero code changes needed
- **Multi-Provider Support** -- OpenAI (GPT-4o, o1), Anthropic (Claude Opus, Sonnet, Haiku), Google Gemini (2.0-Flash, 2.5-Flash, 2.5-Pro)
- **Token-Accurate Billing** -- Reads exact token counts from provider responses; no estimation
- **Model-Aware Pricing** -- Per-model rate cards with separate input/output token costs
- **Configurable Markups** -- Per-tenant margin percentage applied to all billed costs
- **Credit Budget Guards** -- Hard credit balance enforcement; blocks requests when balance <= 0
- **Immutable Audit Trail** -- Full credit ledger (topup/usage/adjustment/refund) for compliance
- **Anomaly Detection** -- Z-score statistical flagging of unusual spend days
- **Spend Forecasting** -- Linear regression projection for month-end totals
- **RAG Cost Advisor** -- ChromaDB-backed semantic retrieval + Gemini explanations for anomalies
- **Natural Language Querying** -- Ask questions like "which model cost the most last week?" in plain English
- **Admin Dashboard** -- Streamlit UI for tenant management, KPI monitoring, and invoice generation
- **Test Chatbot** -- Demo Streamlit app routing requests through the proxy end-to-end

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI 0.115.0 |
| **Database** | PostgreSQL + SQLAlchemy 2.0 |
| **HTTP Client** | httpx 0.27.2 (async) |
| **Authentication** | passlib[bcrypt] (API key hashing) |
| **Frontend** | Streamlit 1.40.0 |
| **Charts** | Plotly 5.24.1 + Pandas |
| **Embeddings** | SentenceTransformers 3.3.1 |
| **Vector Store** | ChromaDB 0.5.20 (RAG advisor) |
| **Caching** | Redis 5.2.0 |
| **Invoice PDF** | WeasyPrint 62.3 |
| **Testing** | pytest + pytest-asyncio |

## Project Structure

```
llm-billing-platform/
├── backend/
│   ├── main.py                     # FastAPI app, router registration, startup
│   ├── config.py                   # Env vars, model rate cards, provider detection
│   ├── auth.py                     # API key validation, admin auth
│   ├── database.py                 # SQLAlchemy engine + session management
│   ├── models/
│   │   ├── tenant.py               # Tenant + APIKey ORM models
│   │   ├── usage.py                # UsageEvent ledger model
│   │   └── billing.py              # CreditLedger model
│   ├── routers/
│   │   ├── proxy.py                # Core LLM proxy gateway (/v1/chat/completions)
│   │   ├── tenants.py              # Tenant CRUD + API key generation
│   │   ├── usage.py                # Usage analytics endpoints
│   │   ├── billing.py              # Credit management + invoice preview
│   │   └── ai.py                   # Anomaly detection, forecasting, NL query
│   ├── services/
│   │   ├── token_counter.py        # Provider-agnostic token count extraction
│   │   ├── cost_engine.py          # Token-to-USD conversion using rate cards
│   │   ├── budget_guard.py         # Credit balance checks + ledger writes
│   │   ├── usage_logger.py         # Async background usage event logging
│   │   ├── anomaly.py              # Z-score anomaly detection
│   │   ├── forecaster.py           # Linear regression spend forecasting
│   │   ├── rag_advisor.py          # ChromaDB RAG for cost spike explanations
│   │   ├── nl_query.py             # Natural language to SQL (Gemini-powered)
│   │   └── llm_client.py           # Async Gemini wrapper for internal features
│   └── tests/
│       ├── test_cost_engine.py     # Cost calculation tests
│       ├── test_anomaly.py         # Anomaly detection tests
│       └── test_proxy.py           # Proxy endpoint tests
│
├── frontend/
│   ├── app.py                      # Streamlit main page
│   ├── components/
│   │   ├── api_client.py           # FastAPI client wrapper
│   │   └── charts.py               # Reusable Plotly chart helpers
│   └── pages/
│       ├── 0_tenants.py            # Create tenants, manage API keys
│       ├── 1_overview.py           # Platform KPIs, spend trends, alerts
│       ├── 2_usage.py              # Raw usage events + model/day breakdowns
│       ├── 3_ai_insights.py        # Anomalies, forecast, RAG explanations
│       ├── 4_billing.py            # Credit balances, topups, invoices
│       └── 5_chat.py               # NL query interface
│
├── test-chatbot/
│   └── app.py                      # Demo client app routing through proxy
│
├── postman/
│   └── LLM_Billing_Platform.postman_collection.json
│
├── requirements.txt
├── .env.example
└── .gitignore
```

## Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Redis (optional, for credit balance caching)
- API keys for LLM providers you want to proxy (OpenAI, Anthropic, and/or Gemini)

## Setup

### 1. Install Dependencies

```bash
cd llm-billing-platform
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
DATABASE_URL=postgresql://billing:billing@localhost:5432/billing
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
ADMIN_SECRET_KEY=your-admin-key-here
REDIS_URL=redis://localhost:6379/0
```

### 3. Initialize the Database

Create the PostgreSQL database:

```bash
psql -U postgres -c "CREATE USER billing WITH PASSWORD 'billing';"
psql -U postgres -c "CREATE DATABASE billing OWNER billing;"
```

Initialize tables:

```bash
python -c "from backend.database import init_db; init_db()"
```

## Running the Application

### Start the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Health check: `GET http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### Start the Dashboard

```bash
cd frontend
streamlit run app.py
```

Opens at `http://localhost:8501`

### Run the Test Chatbot (Optional)

```bash
cd test-chatbot
streamlit run app.py
```

Routes requests through the proxy to verify the full pipeline: auth -> credit check -> proxy -> cost calculation -> logging.

## API Reference

### Proxy (Client-Facing)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/chat/completions` | Main proxy endpoint; accepts OpenAI-format requests |

### Tenant Management (Admin)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tenants` | List all tenants |
| POST | `/tenants` | Create tenant + auto-generate API key |
| GET | `/tenants/{id}/keys` | View API keys for a tenant |
| PUT | `/tenants/{id}` | Update tier or markup percentage |

### Usage Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/usage/platform-summary` | MTD spend, active tenants, API calls today |
| GET | `/usage/platform-daily` | Daily spend breakdown by tenant (30 days) |
| GET | `/usage/{tenant_id}/usage` | Raw usage events (filterable by date/model) |
| GET | `/usage/{tenant_id}/usage/by-model` | Spend breakdown per model |
| GET | `/usage/{tenant_id}/usage/by-day` | Daily spend time series |

### Billing & Credits

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/billing/{tenant_id}/credits` | Current balance + ledger history |
| POST | `/billing/{tenant_id}/credits/topup` | Add credits to a tenant |
| GET | `/billing/{tenant_id}/invoice/preview` | JSON invoice for a billing period |

### AI Insights

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ai/anomalies/{tenant_id}` | Flagged anomaly days with z-scores |
| GET | `/ai/forecast/{tenant_id}` | Month-end spend projection |
| POST | `/ai/explain` | RAG advisor explanation for an anomaly |
| POST | `/ai/query` | Natural language query on usage data |
| GET | `/ai/insights/{tenant_id}` | Combined anomalies + forecast |
| GET | `/ai/platform-anomalies` | Recent anomalies across all tenants |

## Data Models

### Tenants

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Tenant name |
| email | String | Contact email |
| tier | Enum | basic, pro, or enterprise |
| markup_pct | Float | Billing markup percentage (default: 20%) |
| created_at | Timestamp | Creation time |

### Usage Events

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | Foreign key to tenant |
| model | String | LLM model used |
| provider | String | openai, anthropic, or gemini |
| input_tokens | Integer | Prompt tokens consumed |
| output_tokens | Integer | Completion tokens generated |
| total_cost_usd | Float | Raw provider cost |
| billed_cost_usd | Float | Cost with tenant markup applied |
| request_id | String | Unique request identifier |
| ts | Timestamp | Event timestamp |

### Credit Ledger

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| tenant_id | UUID | Foreign key to tenant |
| amount_usd | Float | Positive = topup, negative = deduction |
| event_type | String | topup, usage, adjustment, or refund |
| note | String | Human-readable description |
| ts | Timestamp | Event timestamp |

## Model Rate Card

Pricing per 1 million tokens (USD):

| Model | Input | Output | Provider |
|-------|------:|-------:|----------|
| gpt-4o | $2.50 | $10.00 | OpenAI |
| gpt-4o-mini | $0.15 | $0.60 | OpenAI |
| o1 | $15.00 | $60.00 | OpenAI |
| o1-mini | $3.00 | $12.00 | OpenAI |
| claude-opus-4-6 | $15.00 | $75.00 | Anthropic |
| claude-sonnet-4-6 | $3.00 | $15.00 | Anthropic |
| claude-haiku-4-5-20251001 | $0.80 | $4.00 | Anthropic |
| gemini-2.0-flash | $0.10 | $0.40 | Google |
| gemini-2.5-flash | $0.15 | $3.50 | Google |
| gemini-2.5-pro | $1.25 | $10.00 | Google |

Unknown models fall back to $0.001 (input) / $0.003 (output).

## How It Works

### Proxy Flow

1. Client sends an OpenAI-format request with their API key
2. Backend authenticates the key and looks up the tenant
3. Credit balance is checked -- returns `402` if balance <= 0
4. Request is transformed to the target provider's format (Gemini content structure, Anthropic system prompt extraction, or OpenAI pass-through)
5. Request is forwarded to the LLM provider
6. Exact token counts are extracted from the provider response
7. Cost is calculated: `(tokens / 1M) x rate x (1 + markup_pct/100)`
8. Response is immediately returned to the client
9. Background task asynchronously logs the usage event and deducts credits

### AI Features

- **Anomaly Detection**: Z-score analysis on daily spend; flags days > 2 standard deviations from mean; requires minimum 7 days of history
- **Spend Forecasting**: Linear regression on last 14 days projected to month-end; reports trend direction (increasing/decreasing/stable)
- **RAG Advisor**: Stores resolved anomalies in ChromaDB with semantic embeddings; retrieves similar past cases for new anomalies; Gemini generates plain-English explanations
- **NL Query**: Gemini converts natural language questions to SQL against the usage_events table; executes and narrates results

## Testing

```bash
cd backend
pytest tests/ -v
```

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Tenants** | Create tenants, generate/revoke API keys |
| **Overview** | Platform KPIs, daily spend trends, anomaly alerts |
| **Usage** | Raw usage events with model/day breakdowns |
| **AI Insights** | Anomaly detection, spend forecast, RAG explanations |
| **Billing** | Credit balances, topup management, invoice previews |
| **Chat** | Natural language query interface for usage data |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `connection refused` on database | Ensure PostgreSQL is running and `DATABASE_URL` in `.env` is correct |
| `402 Payment Required` | Tenant has no credits; use `/billing/{id}/credits/topup` to add funds |
| Unknown model fallback pricing | Add the model to `MODEL_RATES` in `config.py` |
| Anomaly detection returns empty | Needs at least 7 days of usage history |
| NL query returns unexpected results | Check that usage events exist; the feature queries `usage_events` table |

## License

MIT License
