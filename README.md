# RazorGrowth AI
### Autonomous AI Growth Manager for Razorpay Merchants

---

## Technical Documentation Index

| Topic | Documentation Link | Key Coverage |
|:---|:---|:---|
| **System Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 9-layer stack, ERD models, Razorpay integration, asyncpg engine, observability |
| **Autonomous Workflow** | [docs/WORKFLOW.md](docs/WORKFLOW.md) | 7-stage closed loop, sequence diagrams, live payload examples |
| **Multi-Agent System** | [docs/AGENTS.md](docs/AGENTS.md) | Multi-provider LLM cascade, ReAct tool loop, consensus builder, specialized agents |
| **Intelligence Layer** | [docs/INTELLIGENCE.md](docs/INTELLIGENCE.md) | RFM segmentation, Churn decay model, CLV, Co-purchase affinity |
| **File Inventory & Status** | [docs/FILE_INVENTORY_AND_STATUS.md](docs/FILE_INVENTORY_AND_STATUS.md) | Verified integration status across all backend and frontend files |
| **System Specification** | [PROJECT.md](PROJECT.md) | Architecture specification, goals, and technical guidelines |


---

## 1. System Overview

RazorGrowth AI transforms Razorpay from payment processing infrastructure into an autonomous revenue engine. The platform operates a continuous, data-driven closed loop:

1. **Observe**: Ingests real-time payment transactions and merchant store telemetry.
2. **Understand**: Synthesizes unified Customer 360 profiles, RFM segments, and churn decay scores.
3. **Find Opportunity**: Discovers high-conviction revenue leaks (Dormant VIPs, Payment Failures, Cross-Sell gaps).
4. **Decide**: Deploys a multi-agent system to formulate margin-safe promotional strategies verified by deterministic Permission Gates.
5. **Act**: Dispatches multi-channel communications and registers real checkout sessions via the **Razorpay Orders API** in Test Mode.
6. **Measure**: Ingests HMAC-verified **Razorpay Webhooks** to record real-time conversions and compute mathematical A/B lift in PostgreSQL.
7. **Learn**: Archives session traces to continuously calibrate future cohort selection and incentive discount curves.

---

## 2. High-Level Architecture

```mermaid
graph TD
    subgraph UI["Presentation Layer"]
        DASH["Next.js Dashboard\n(React 19 + TypeScript + Tailwind)"]
    end

    subgraph Gateway["API Layer"]
        API["FastAPI REST Services\n(/api/v1)"]
    end

    subgraph Agents["Multi-Agent Layer"]
        GMA["GrowthManagerAgent (Master Orchestrator)"]
        CA["CustomerAgent (Audience Cohorts)"]
        OA["OfferAgent (Margin-Safe Incentives)"]
        CPA["CampaignAgent (Copy & Channels)"]
        EA["ExperimentAgent (A/B Test Design & Lift)"]
        PG["PermissionGateService (Deterministic Safety)"]
    end

    subgraph Intelligence["Analytical Intelligence Layer"]
        C360["Customer 360 Engine"]
        RFM["RFM Segmentation Engine"]
        CHURN["Churn Risk Predictor"]
        CLV["12-Month Predictive CLV"]
        PMA["Payment Method Performance Analyzer"]
        OD["Opportunity Detection Engines"]
    end

    subgraph Storage["Persistence Layer"]
        DB[("PostgreSQL\n(SQLAlchemy 2.0 / NullPool)")]
        BUS["Domain Event Publisher / Bus"]
    end

    subgraph Razorpay["Razorpay Test Mode"]
        RZP_ORDERS["Razorpay Orders API"]
        RZP_CHECKOUT["Razorpay Standard Checkout"]
        RZP_WEBHOOK["Razorpay Webhook Handler\n(HMAC-SHA256 Verification)"]
    end

    DASH <--> API
    API --> GMA
    GMA --> Intelligence
    GMA --> Agents
    Agents --> PG
    GMA --> RZP_ORDERS
    RZP_ORDERS --> RZP_CHECKOUT
    RZP_CHECKOUT --> RZP_WEBHOOK
    RZP_WEBHOOK --> BUS
    BUS --> DB
    DB --> API
```

---

## 3. Project Directory Layout

```
razorpay/
├── .env.example                       # Environment configuration template  
├── .env.docker.example                # Docker environment template
├── docker-compose.yml                 # Docker orchestration configuration
├── Dockerfile                         # Backend Docker image definition
├── requirements.txt                   # Backend Python dependencies
├── requirements-dev.txt               # Development & test dependencies
├── README.md                          # Main project specification and index
├── .gitignore                         # Git ignore definitions
├── client/                            # Next.js React Frontend
│   ├── Dockerfile                     # Frontend Docker image definition
│   ├── src/
│   │   ├── app/                       # Next.js app router pages
│   │   ├── components/                # React components
│   │   ├── services/                  # API client services
│   │   └── types/                     # TypeScript type definitions
│   ├── package.json                   # Frontend dependencies
│   └── next.config.ts                 # Next.js configuration
├── docs/
│   ├── ARCHITECTURE.md                # 9-layer architecture and data models
│   ├── WORKFLOW.md                    # 7-stage autonomous closed-loop walkthrough
│   ├── AGENTS.md                      # Multi-agent system and Permission Gates
│   ├── INTELLIGENCE.md                # Mathematical algorithms and models
│   ├── FILE_INVENTORY_AND_STATUS.md   # Line-by-line file audit and status
│   └── HACKATHON_RUNBOOK.md           # Live demonstration script
├── data/                              # Archived dataset snapshots
│   └── latest_simulation.json         # Latest generated merchant dataset
├── output/                            # Multi-agent session traces
│   └── session_*.json                 # Complete execution trace JSON logs
├── app/
│   ├── main.py                        # FastAPI application entrypoint
│   ├── config/
│   │   ├── settings.py                # Environment configuration
│   │   └── prompts.py                 # Centralized prompt template registry
│   ├── database/
│   │   ├── base.py                    # SQLAlchemy Base
│   │   └── session.py                 # Async PostgreSQL session provider (NullPool)
│   ├── schemas/                       # Pydantic data contracts
│   │   └── agent_outputs.py           # Structured agent input/output models
│   ├── models/                        # Declarative ORM entities
│   │   ├── merchant.py                # Merchant model
│   │   ├── customer.py                # Customer & RFM profile
│   │   ├── product.py                 # Product catalog
│   │   ├── order.py                   # Order transactions
│   │   ├── payment.py                 # Payment records
│   │   ├── opportunity.py             # Discovered growth opportunities
│   │   ├── campaign.py                # Autonomous campaigns
│   │   ├── experiment_assignment.py   # Cohort A/B assignments
│   │   └── webhook_event.py           # Webhook audit log
│   ├── customer_360/                  # Unified customer profile builder
│   │   ├── metric_calculator.py       # Aggregate spend and order metrics
│   │   └── profile_builder.py         # Dynamic profile synchronization
│   ├── intelligence/                  # Distribution-aware computational engines
│   │   ├── distribution_thresholds.py # Empirical quantile threshold calculator
│   │   ├── customer_segmentation.py   # Distribution-aware RFM segmentation logic
│   │   ├── churn_predictor.py         # Continuous churn decay model
│   │   ├── clv_estimator.py           # Continuous frequency-scaled CLV
│   │   ├── product_recommender.py     # Cross-sell association rules
│   │   ├── payment_method_analyzer.py # Payment failure baseline benchmarking
│   │   └── opportunity_detector.py    # Revenue leakage detection
│   ├── agents/                        # Autonomous multi-agent layer
│   │   ├── growth_manager_agent.py    # Chief growth orchestrator
│   │   ├── agent_consensus.py         # Multi-agent consensus & voting engine
│   │   ├── agentic_orchestrator.py    # Bounded ReAct multi-tool decision loop
│   │   ├── tool_registry.py           # Domain tool definitions & dispatchers
│   │   ├── customer_agent.py          # Audience selection & ranking
│   │   ├── offer_agent.py             # Incentive optimization & margin safety
│   │   ├── campaign_agent.py          # Personalized copywriting & channels
│   │   └── experiment_agent.py        # A/B testing & statistical lift math
│   ├── services/                      # Core business services
│   │   ├── live_experiment_service.py # Experiment coordinator facade
│   │   ├── experiment_order_creator.py# Razorpay order generation & cohort assignment
│   │   ├── webhook_payment_processor.py# Webhook HMAC verification & payment logging
│   │   ├── experiment_metrics_calculator.py# Conversion rate & lift math computation
│   │   ├── metrics_service.py         # Prometheus metrics collection (/metrics)
│   │   ├── agent_performance_tracker.py# Per-agent latency & success rate monitoring
│   │   ├── cache_service.py           # In-memory TTL query caching
│   │   ├── vector_memory_service.py   # ChromaDB 384-dim semantic memory store
│   │   ├── embedding_service.py       # FastEmbed / ONNX in-process dense embeddings
│   │   ├── llm_provider_service.py    # 3-tier benchmarked multi-provider cascade
│   │   ├── llm_service.py             # Tool-calling cognitive interface & SSE streaming
│   │   ├── session_management_service.py # Persistent session & thread tracking
│   │   ├── conversation_service.py    # Message history & episodic memory vectorization
│   │   ├── permission_gate_service.py # Deterministic safety guardrails firewall
│   │   ├── context_engine.py          # Store telemetry & memory context builder
│   │   ├── snapshot_storage_service.py# Local JSON snapshot persistence
│   │   ├── trace_logger_service.py    # Timezone-aware multi-agent trace logger
│   │   └── trace_tool_service.py      # Micro-tool trace retrieval for grounded chat

│   ├── actions/                       # Campaign execution and dispatchers
│   │   ├── campaign_dispatcher.py     # Outbound campaign coordinator
│   │   ├── discount_coupon_service.py # Promotional coupon issuer
│   │   ├── message_simulator.py       # Outbound delivery simulator
│   │   └── conversion_simulator.py    # Historical simulation data generator
│   ├── integrations/                  # Razorpay SDK wrappers
│   │   ├── razorpay_client.py         # Razorpay Orders API client
│   │   └── razorpay_webhook_handler.py# HMAC signature validation
│   ├── events/                        # Domain event bus
│   │   ├── event_types.py             # Domain event definitions
│   │   ├── event_publisher.py         # Event broadcasting service
│   │   └── event_consumer.py          # Event subscriber handlers
│   ├── simulator/                     # Synthetic merchant telemetry generator
│   │   ├── merchant_generator.py      # Sandbox merchant generator
│   │   ├── customer_generator.py      # Cohort customer generator
│   │   ├── order_generator.py         # Chronological order generator
│   │   ├── payment_event_generator.py # Payment failure generator
│   │   └── simulation_orchestrator.py # Simulation pipeline coordinator
│   └── api/                           # FastAPI REST and SSE streaming endpoints
│       ├── routes_simulator.py        # Dataset generation & local snapshot
│       ├── routes_customers.py        # Customer 360 queries
│       ├── routes_growth.py           # Multi-agent scan, ReAct loop, chat, & cross-reference
│       ├── routes_campaigns.py        # Campaign launch & Permission Gate
│       ├── routes_experiments.py      # A/B results & webhook simulation
│       ├── routes_sessions.py         # Session history & memory vectorization
│       └── routes_webhooks.py         # HMAC-verified Razorpay webhooks
└── tests/                             # Pytest automated test suite
    ├── conftest.py                    # Pytest asyncio configuration
    ├── test_agents.py                 # Agent schema and decision tests
    ├── test_intelligence.py           # Distribution-aware algorithm tests
    ├── test_permission_gates.py       # Permission Gate guardrail tests
    ├── test_real_razorpay_flow.py     # Razorpay Orders and Webhooks tests
    ├── test_full_loop_api.py          # Complete 7-step API loop test
    ├── test_full_architecture_schema.py # PostgreSQL assignment lifecycle test
    ├── test_webhook_and_security.py   # HMAC signature verification tests
    ├── test_simulator.py              # Synthetic data generator tests
    ├── test_trace_tool_service.py     # Micro-tool trace routing tests
    ├── test_multi_provider_llm.py     # Multi-provider cascade & failover tests
    └── test_rag_and_agentic_loop.py   # ChromaDB vector recall & ReAct loop tests
```

---

## 4. Quickstart and Setup Guide

### 4.1 🐳 Docker Setup (Recommended - One Command)

The fastest way to get RazorGrowth AI running with all dependencies:

```bash
# 1. Clone the repository
git clone https://github.com/MouleeswaranR/RazorGrowth.git
cd razorpay

# 2. Configure environment variables
cp .env.docker.example .env
# Edit .env with your Razorpay and OpenRouter API keys

# 3. Start all services (PostgreSQL + Backend + Frontend)
docker-compose up -d

# 4. Verify services are running
docker-compose ps

# Services will be available at:
# - Frontend Dashboard: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health/detailed
```

**Stopping Services:**
```bash
docker-compose down

# To remove all data volumes:
docker-compose down -v
```

**Viewing Logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### 4.2 📦 Manual Installation (Development)

If you prefer to run services manually without Docker:

#### Prerequisites
- Python 3.10 or higher
- PostgreSQL database instance (local or hosted, e.g. Supabase, Neon)
- Razorpay Test Mode API Key ID and Secret Key

### 4.2 Installation

1. Clone the repository and navigate to the directory:
```bash
git clone https://github.com/MouleeswaranR/RazorGrowth.git
cd razorpay
```

2. Create and activate a Python virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

3. Install project dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/razorgrowth
RAZORPAY_KEY_ID=rzp_test_YourKeyIdHere
RAZORPAY_KEY_SECRET=YourKeySecretHere
RAZORPAY_WEBHOOK_SECRET=YourWebhookSecretHere
OPENROUTER_API_KEY=sk-or-v1-YourOpenRouterKeyHere
```

5. Start the FastAPI backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
- API & Interactive Swagger Docs: `http://localhost:8000/docs`

6. In a separate terminal, start the Next.js Frontend Dashboard:
```bash
cd client
npm install
npm run dev
```
- Primary Dashboard: `http://localhost:3000`
- Multi-Agent Live Execution Trace: available in-dashboard via the **Agents** tab (Live Multi-Agent / Agentic SSE streaming)

---

## 5. API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/simulator/generate` | Generates synthetic merchant dataset (50 customers, 150 orders) |
| `GET` | `/api/v1/simulator/local-snapshot` | Retrieves stored session JSON snapshot & active merchant telemetry |
| `POST` | `/api/v1/growth/scan/{merchant_id}` | Runs multi-agent intelligence scan and returns ranked opportunities |
| `GET` | `/api/v1/growth/scan-live/{merchant_id}` | Real-time Server-Sent Events (SSE) streaming of multi-agent pipeline progress |
| `POST` | `/api/v1/growth/agentic-scan/{merchant_id}` | Bounded autonomous ReAct loop with multi-tool calling & vector memory citations |
| `GET` | `/api/v1/growth/agentic-scan-live/{merchant_id}` | Real-time SSE streaming of bounded ReAct tool iterations |
| `GET` | `/api/v1/growth/latest-trace` | Retrieves ordered execution trace & decision record on disk |
| `GET` | `/api/v1/growth/sessions` | Lists all historical session traces with lift outcomes |
| `POST` | `/api/v1/growth/cross-reference` | Cross-session semantic memory search & comparative RAG analysis |
| `POST` | `/api/v1/growth/chat` | Conversational strategist grounded in episodic trace tools |
| `POST` | `/api/v1/campaigns/launch/{opp_id}` | Evaluates Permission Gate and creates Razorpay Test Mode orders |
| `POST` | `/api/v1/webhooks/razorpay` | Ingests and verifies live HMAC-signed Razorpay webhooks |
| `POST` | `/api/v1/experiments/webhook-payment` | Triggers test webhook payment capture and recalculates lift in PostgreSQL |
| `GET` | `/api/v1/experiments/results/{campaign_id}` | Reads real measured experiment lift metrics from database |
| `GET` | `/api/v1/sessions` | Lists all merchant conversational session threads |
| `POST` | `/api/v1/sessions/conversations` | Persists conversation turns and vectorizes memories into ChromaDB |

---

## 6. Automated Verification

Run the full automated test suite:
```bash
python -m pytest tests/ -v
```

All 29 test cases across unit, intelligence, multi-provider LLM, agentic loop, vector RAG memory, permission gates, and end-to-end integration tiers execute deterministically with 100% pass rate.
