# File Inventory, Specifications & Status Audit

This document provides a line-by-line audit of all files in the codebase. It details what each file is intended to do in production, what its current implementation does, and whether it represents an Integrated Component, a Scaffold/Heuristic, or a Simulation/Mock.

---

## Classification Legend

- **`[INTEGRATED]`**: Fully functional production-grade code (database sessions, ORM schemas, cryptographic verifications, routing, live measurement, real LLM integration).
- **`[SCAFFOLD]`**: Fully functioning deterministic logic and algorithms ready for production extension.
- **`[SIMULATION]`**: Explicitly designed to simulate external systems, test data, or third-party communications (e.g., message dispatchers, initial 500-customer historical dataset generator).

---

## 1. Application Configuration & Database

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/config/settings.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/config/settings.py) | **`[INTEGRATED]`** | Loads and validates environment variables (`DATABASE_URL`, Razorpay test API keys, LLM keys) using Pydantic Settings. | Reads `.env` or defaults to development values. Production-ready. |
| [`app/config/prompts.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/config/prompts.py) | **`[INTEGRATED]`** | Central registry of typed prompt templates for growth reasoning, streaming, copy generation, and merchant chat. | Modular prompt builders enforcing strict schema output, metric citations, and anti-hallucination rules. |
| [`app/database/base.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/database/base.py) | **`[INTEGRATED]`** | Serves as the declarative base class for all SQLAlchemy ORM models. | Standard SQLAlchemy 2.0 `DeclarativeBase` implementation. Production-ready. |
| [`app/database/session.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/database/session.py) | **`[INTEGRATED]`** | Manages async database connections, session pooling, and async request generators. | Configured with `create_async_engine` using `NullPool` for clean event loop isolation. Production-ready. |

---

## 2. Schemas & Structured Data Contracts

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/schemas/agent_outputs.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/schemas/agent_outputs.py) | **`[INTEGRATED]`** | Defines strictly typed Pydantic models for all agent outputs, permission gates, and LLM reasoning payloads. | Complete data contracts (`AudienceSelectionOutput`, `OfferRecommendationOutput`, `CampaignCopyOutput`, `ExperimentMetricsOutput`, `PermissionGateResult`, `GrowthPlanOutput`). |

---

## 3. Domain Models (`app/models/`)

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/models/merchant.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/merchant.py) | **`[INTEGRATED]`** | Persists merchant organization details, category, currency, and credentials. | SQLAlchemy model defining merchant columns and relationships. |
| [`app/models/customer.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/customer.py) | **`[INTEGRATED]`** | Stores customer profiles, RFM aggregations, churn scores, and predictive CLV. | Defines schema for Customer 360 fields and foreign key links. |
| [`app/models/product.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/product.py) | **`[INTEGRATED]`** | Stores merchant catalog items, SKU, category, and pricing. | Complete ORM model with relationships to orders and merchants. |
| [`app/models/order.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/order.py) | **`[INTEGRATED]`** | Records order transactions, amounts, quantities, and Razorpay order references. | ORM model linking customers, products, and payments. |
| [`app/models/payment.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/payment.py) | **`[INTEGRATED]`** | Tracks payment gateway attempts, payment methods (UPI, Card), and error reasons. | ORM model storing Razorpay payment IDs and capture statuses. |
| [`app/models/opportunity.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/opportunity.py) | **`[INTEGRATED]`** | Persists AI-discovered growth opportunities, audience counts, and GMV upside. | Schema storing financial potential, confidence scores, and status. |
| [`app/models/campaign.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/campaign.py) | **`[INTEGRATED]`** | Records autonomous campaign executions, discount offers, and A/B test results. | Schema capturing treatment/control conversion rates and net GMV lift. |
| [`app/models/experiment_assignment.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/experiment_assignment.py) | **`[INTEGRATED]`** | Maps customers to A/B variants (Treatment / Control) and tracks post-campaign conversion state. | Persists cohort assignment, `is_converted`, `conversion_order_id`, and conversion timestamps. |
| [`app/models/session_memory.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/models/session_memory.py) | **`[INTEGRATED]`** | Stores episodic outcome memories and growth reasoning for vector search retrieval. | Defines schema for session memory records, metadata JSON, and timestamps. |

---

## 4. Core Business Services (`app/services/`)

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/services/embedding_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/embedding_service.py) | **`[INTEGRATED]`** | Generates dense 384-dimensional semantic embeddings using local in-process FastEmbed ONNX models. | In-process embedding generation (`embed_text`, `embed_texts`) with normalized vector projections and fast deterministic token fallback. |
| [`app/services/vector_memory_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/vector_memory_service.py) | **`[INTEGRATED]`** | Manages persistent ChromaDB vector storage and cosine similarity retrieval for historical sessions and campaign outcomes. | Persistent local client (`./data/vector_memory`), `store_memory`, and `find_similar_memories`. Zero cloud network dependency. |
| [`app/services/live_experiment_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/live_experiment_service.py) | **`[INTEGRATED]`** | Orchestrates real Razorpay Test Mode order creation for cohorts, processes incoming webhooks, and recalculates A/B lift in PostgreSQL. | Creates real Razorpay orders with notes metadata, logs webhook events, updates `experiment_assignments.is_converted = True`, recalculates incremental GMV, and auto-indexes outcome memories in `VectorMemoryService`. |
| [`app/services/permission_gate_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/permission_gate_service.py) | **`[INTEGRATED]`** | Deterministic security firewall enforcing merchant safety guardrails on campaign cost, discount depth, and audience size. | Computes dynamic thresholds based on total store GMV and customer count. Returns `AUTO_APPROVED` or `REQUIRES_MERCHANT_APPROVAL`. |
| [`app/services/context_engine.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/context_engine.py) | **`[INTEGRATED]`** | Pre-aggregates store telemetry and retrieves relevant episodic memories into compact, high-signal context objects. | Computes merchant summary stats (total GMV, customer count, segment distribution, payment success rates, retrieved vector memory). |
| [`app/services/snapshot_storage_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/snapshot_storage_service.py) | **`[INTEGRATED]`** | Archives and retrieves local JSON dataset snapshots in `data/latest_simulation.json`. | Saves full merchant dataset snapshot and serves it for local offline inspection. |
| [`app/services/trace_logger_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/trace_logger_service.py) | **`[INTEGRATED]`** | Records chronological multi-agent execution steps and writes complete session logs to `output/session_{id}.json`. | Thread-safe in-memory and disk logger capturing agent reasoning and metrics at every step. |
| [`app/services/trace_tool_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/trace_tool_service.py) | **`[INTEGRATED]`** | Micro-tool retrieval service providing hybrid exact keyword facts + vector semantic fallback for merchant chat. | Routes merchant queries to specific trace steps; falls back to `VectorMemoryService` similarity search for qualitative historical context. |
| [`app/services/llm_provider_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/llm_provider_service.py) | **`[INTEGRATED]`** | Multi-provider orchestration and automatic failover across NVIDIA NIM, OpenRouter, Groq, and Mistral. | Prioritizes NVIDIA NIM for tool calling, Groq for real-time SSE streaming, OpenRouter for strategy reasoning, with reasoning trace `<think>` extraction. |
| [`app/services/llm_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/services/llm_service.py) | **`[INTEGRATED]`** | Connects to AI models via `LLMProviderService` with tool-calling and automatic deterministic fallback. | Supports `call_with_tools`, `generate_growth_reasoning`, personalized copy, and chat streaming with model reasoning traces. |

---

## 5. Intelligence Layer (`app/intelligence/`)

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/intelligence/customer_segmentation.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/intelligence/customer_segmentation.py) | **`[INTEGRATED]`** | Classifies customers using RFM composite scoring into 6 distinct behavioral cohorts. | Weighted RFM scoring mapping customers into `VIP Active`, `VIP Dormant`, `Loyal`, `Loyal At Risk`, `New`, and `Standard`. |
| [`app/intelligence/churn_predictor.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/intelligence/churn_predictor.py) | **`[INTEGRATED]`** | 3-factor composite churn model: 50% recency, 30% frequency decay, 20% spend decline. | Analyzes historical order intervals and spend trajectories to yield a 0.0-1.0 risk score. |
| [`app/intelligence/clv_estimator.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/intelligence/clv_estimator.py) | **`[INTEGRATED]`** | 12-month forward predictive CLV combining historical spend, order run rate, and churn discount. | Computes projected CLV clamped between 1.0x and 5.0x historical spend. |
| [`app/intelligence/product_recommender.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/intelligence/product_recommender.py) | **`[INTEGRATED]`** | Discovers co-purchase affinity matrix and identifies cross-sell candidate cohorts. | Computes category co-purchase confidence rules across order histories. |
| [`app/intelligence/payment_method_analyzer.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/intelligence/payment_method_analyzer.py) | **`[INTEGRATED]`** | Benchmarks payment method success rates (Card vs UPI) and quantifies lost GMV. | Identifies underperforming channels against the 92.0% benchmark and computes recoverable revenue. |
| [`app/intelligence/opportunity_detector.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/intelligence/opportunity_detector.py) | **`[INTEGRATED]`** | Scans merchant intelligence for 5 distinct opportunity types with dynamic data-derived confidence. | Computes Dormant VIP Recovery, Cross-Sell Affinity, Payment Optimization, Proactive Churn Intervention, and Tiered Basket Builder with empirical confidence formulas. |

---

## 6. Multi-Agent System (`app/agents/`)

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/agents/growth_manager_agent.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents/growth_manager_agent.py) | **`[INTEGRATED]`** | Master orchestrator coordinating multi-agent growth scan, opportunity ranking, and action planning. | Coordinates opportunity detectors, delegates to sub-agents, validates Permission Gates, auto-indexes growth scan memories in `VectorMemoryService`, and calls LLMService. |
| [`app/agents/agentic_orchestrator.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents/agentic_orchestrator.py) | **`[INTEGRATED]`** | Runs bounded ReAct tool-calling loop (`MAX_STEPS = 6`) where the LLM drives multi-step growth decisions. | Invokes tool-calling LLM, dispatches tools via `ToolRegistry`, recalls historical memory, formats decision plans, and stops within bound. |
| [`app/agents/tool_registry.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents/tool_registry.py) | **`[INTEGRATED]`** | Exposes JSON-schema-described domain agent tools (`get_merchant_context`, `detect_opportunities`, `select_audience`, `recommend_offer`, `recall_similar_past_campaigns`, `check_permission_gate`). | Wraps existing agent and intelligence layer methods into callable tool functions without duplicate logic. |
| [`app/agents/customer_agent.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents/customer_agent.py) | **`[INTEGRATED]`** | Curates prioritized audience segments matching specific growth opportunity criteria. | Filters customer records by segment, churn risk, and spend ranking into structured manifests. |
| [`app/agents/offer_agent.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents/offer_agent.py) | **`[INTEGRATED]`** | Formulates margin-optimized discount offers tailored to cohort spend tiers. | Selects optimal discount tiers (`WELCOME15`, `VIP20OFF`, `UPISWIFT`, `BUNDLE10`) with urgency limits. |
| [`app/agents/campaign_agent.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents/campaign_agent.py) | **`[INTEGRATED]`** | Generates personalized multi-channel email and WhatsApp copy. | Implements both async LLM-backed personalized copy generation and deterministic template fallbacks. |
| [`app/agents/experiment_agent.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents/experiment_agent.py) | **`[INTEGRATED]`** | Configures A/B randomized splits and calculates statistical conversion lift and incremental GMV. | Calculates treatment/control conversion rates, absolute pp difference, relative lift, and incremental revenue. |

---

## 7. Action Execution Layer (`app/actions/`)

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/actions/discount_coupon_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/actions/discount_coupon_service.py) | **`[INTEGRATED]`** | Creates and validates promotional discount codes with dynamic discount types and values during checkout. | In-memory active coupon repository supporting dynamic issuance and redemption validation. |
| [`app/actions/message_simulator.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/actions/message_simulator.py) | **`[SIMULATION]`** | Delivers outbound communications across Email, WhatsApp, and SMS channels. | Records dispatched messages to an in-memory history log for audit and verification. |
| [`app/actions/campaign_dispatcher.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/actions/campaign_dispatcher.py) | **`[INTEGRATED]`** | Coordinates campaign dispatch, coupon issuance with exact OfferAgent parameters, and messaging delivery. | Integrates message simulator with coupon issuance using dynamic `discount_type` and `discount_value` for treatment cohorts. |
| [`app/actions/conversion_simulator.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/actions/conversion_simulator.py) | **`[SIMULATION]`** | Generates historical baseline order/payment data for initial pre-launch simulation datasets. | Uses independent Bernoulli draws per customer for historical data generation. (Live post-campaign conversions are measured via `live_experiment_service.py` through Razorpay webhooks). |

---

## 8. Integrations & Event Bus (`app/integrations/` & `app/events/`)

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/integrations/razorpay_client.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/integrations/razorpay_client.py) | **`[INTEGRATED]`** | Communicates with the official Razorpay SDK to create orders and verify payments in Test Mode. | Wraps `razorpay.Client` with sanitized helper methods and structured notes metadata. |
| [`app/integrations/razorpay_webhook_handler.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/integrations/razorpay_webhook_handler.py) | **`[INTEGRATED]`** | Cryptographically verifies Razorpay webhook signatures using HMAC-SHA256 and extracts payloads. | Validates `X-Razorpay-Signature` against secret key in constant time and parses event structures. |
| [`app/events/event_types.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/events/event_types.py) | **`[INTEGRATED]`** | Defines domain event schemas and enumeration types. | Declares `DomainEvent` Pydantic model and `EventType` enum. |
| [`app/events/event_publisher.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/events/event_publisher.py) | **`[SCAFFOLD]`** | Dispatches domain events to asynchronous subscribers. | Implements an in-memory async pub/sub event bus. |
| [`app/events/event_consumer.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/events/event_consumer.py) | **`[INTEGRATED]`** | Subscribes to domain events to log domain activity and trigger profile recomputation. | Subscribes to `payment.captured` and logs structured domain event payloads. |

---

## 9. API Gateway (`app/api/`)

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`app/api/routes_simulator.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/api/routes_simulator.py) | **`[INTEGRATED]`** | Triggers synthetic merchant dataset creation and serves local JSON snapshots. | `POST /api/v1/simulator/generate`, `GET /api/v1/simulator/local-snapshot`, `POST /api/v1/simulator/load-from-local`. |
| [`app/api/routes_customers.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/api/routes_customers.py) | **`[INTEGRATED]`** | Queries paginated Customer 360 records and profiles. | `GET /api/v1/customers` and `GET /api/v1/customers/{id}`. |
| [`app/api/routes_growth.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/api/routes_growth.py) | **`[INTEGRATED]`** | Multi-agent growth scans, bounded agentic ReAct loop, live SSE step streaming, trace retrieval, and chat. | `POST /scan`, `GET /scan-live`, `POST /agentic-scan`, `GET /agentic-scan-live`, `GET /latest-trace`, `GET /sessions`, `POST /cross-reference`, `POST /chat`. |
| [`app/api/routes_campaigns.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/api/routes_campaigns.py) | **`[INTEGRATED]`** | Evaluates Permission Gate and launches autonomous campaigns with Razorpay Test Orders. | `POST /api/v1/campaigns/launch/{opportunity_id}`. |
| [`app/api/routes_experiments.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/api/routes_experiments.py) | **`[INTEGRATED]`** | Reads PostgreSQL A/B metrics and provides test payment webhook trigger. | `GET /api/v1/experiments/results/{campaign_id}`, `POST /api/v1/experiments/webhook-payment`. |
| [`app/api/routes_sessions.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/api/routes_sessions.py) | **`[INTEGRATED]`** | Manages merchant conversation threads and vectorizes memories into ChromaDB. | `GET /api/v1/sessions` and `POST /api/v1/sessions/conversations`. |
| [`app/api/routes_webhooks.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/api/routes_webhooks.py) | **`[INTEGRATED]`** | Ingests and HMAC-verifies real Razorpay payment webhooks. | `POST /api/v1/webhooks/razorpay`, `GET /api/v1/webhooks/recent`, `POST /api/v1/webhooks/simulate-test-event`. |
| [`app/main.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/main.py) | **`[INTEGRATED]`** | FastAPI application entry point, lifecycle manager, CORS middleware, and API router. | Serves API at `/api/v1` and Swagger docs at `/docs`. |

---

## 10. Frontend Application (`client/`)

| File Path | Status | Production Specification | Current Implementation |
|:---|:---|:---|:---|
| [`client/src/app/page.tsx`](file:///c:/Users/ffmou/Desktop/razorpay/client/src/app/page.tsx) | **`[INTEGRATED]`** | Primary Merchant Growth Dashboard with real-time telemetry, opportunity pipeline, and A/B console. | Interactive Next.js 16 + React 19 dashboard with Warm Sand and Dark Obsidian themes. |
| [`client/src/app/trace/page.tsx`](file:///c:/Users/ffmou/Desktop/razorpay/client/src/app/trace/page.tsx) | **`[INTEGRATED]`** | Dedicated Multi-Agent Live Execution Trace & Timeline viewer. | Real-time SSE streaming visualizer for ReAct tool invocations, RAG vector memory citations, and A/B results. |
| [`client/src/components/ClaudeGrowthStrategist.tsx`](file:///c:/Users/ffmou/Desktop/razorpay/client/src/components/ClaudeGrowthStrategist.tsx) | **`[INTEGRATED]`** | Conversational growth advisor grounded in trace micro-tools with interactive tool dropdowns. | Renders model reasoning trace pills, interactive tool inspection drawers, and Markdown formatting. |
| [`client/src/components/SessionSwitcher.tsx`](file:///c:/Users/ffmou/Desktop/razorpay/client/src/components/SessionSwitcher.tsx) | **`[INTEGRATED]`** | Top-header session history dropdown with 1-click switching and Cross-Reference RAG modal. | Queries past sessions, switches active session state, and opens cross-session semantic search modal. |
| [`client/src/components/Header.tsx`](file:///c:/Users/ffmou/Desktop/razorpay/client/src/components/Header.tsx) | **`[INTEGRATED]`** | Top navigation bar with Razorpay sandbox status, theme toggle, session switcher, and demo launcher. | Cleanly aligned sticky header with direct link to Live Trace page. |

---

## 11. Automated Test Suite (`tests/`)

| File Path | Status | Coverage |
|:---|:---|:---|
| [`tests/test_multi_provider_llm.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_multi_provider_llm.py) | **`[INTEGRATED]`** | Tests multi-provider LLM cascade, failover logic across NVIDIA NIM/OpenRouter/Groq/Mistral, and `<think>` reasoning extraction. |
| [`tests/test_rag_and_agentic_loop.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_rag_and_agentic_loop.py) | **`[INTEGRATED]`** | Tests FastEmbed embeddings, ChromaDB vector memory persistence, tool execution, and bounded ReAct loops. |
| [`tests/test_agents.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_agents.py) | **`[INTEGRATED]`** | Tests CustomerAgent filtering, OfferAgent tiers, CampaignAgent copy, and ExperimentAgent math. |
| [`tests/test_intelligence.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_intelligence.py) | **`[INTEGRATED]`** | Tests RFM segmentation, Churn decay formula, CLV estimation, Co-purchase matrix, and Opportunity Detector. |
| [`tests/test_permission_gates.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_permission_gates.py) | **`[INTEGRATED]`** | Tests dynamic threshold computation, discount limit violations, audience caps, and auto-approval. |
| [`tests/test_real_razorpay_flow.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_real_razorpay_flow.py) | **`[INTEGRATED]`** | Tests Razorpay SDK Order creation with notes, webhook note extraction, and webhook payment recording. |
| [`tests/test_full_loop_api.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_full_loop_api.py) | **`[INTEGRATED]`** | Tests complete 7-step API lifecycle: Generate &rarr; Snapshot &rarr; Scan &rarr; Launch &rarr; Webhook-Payment &rarr; Results &rarr; Chat. |
| [`tests/test_full_architecture_schema.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_full_architecture_schema.py) | **`[INTEGRATED]`** | Tests PostgreSQL `webhook_events` and `experiment_assignments` lifecycle through HTTP endpoints. |
| [`tests/test_webhook_and_security.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_webhook_and_security.py) | **`[INTEGRATED]`** | Tests HMAC-SHA256 signature verification (valid, tampered, invalid secrets) and payload parsing. |
| [`tests/test_simulator.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_simulator.py) | **`[INTEGRATED]`** | Tests synthetic merchant, customer cohorts, order generator, and payment failure distributions. |
| [`tests/test_trace_tool_service.py`](file:///c:/Users/ffmou/Desktop/razorpay/tests/test_trace_tool_service.py) | **`[INTEGRATED]`** | Tests micro-tool context routing for LLM merchant chat queries. |
