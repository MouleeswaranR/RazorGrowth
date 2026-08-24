# System Architecture Specification

## 1. Executive Summary

RazorGrowth AI is an autonomous, event-driven growth engine purpose-built for Razorpay merchants. The platform bridges transaction processing infrastructure and autonomous marketing intelligence by operating an automated closed loop: transaction telemetry is continuously ingested, analyzed by an analytical intelligence layer, evaluated by a multi-agent decision system, guarded by deterministic permission gates, executed through real Razorpay checkout workflows, and measured via webhook-driven A/B experiments.

---

## 2. High-Level Architecture Diagram

```mermaid
graph TD
    subgraph ClientLayer["User Interface and API Gateway"]
        UI["Merchant Dashboard (HTML5 / Vanilla JS)"]
        API["FastAPI REST Gateway (/api/v1)"]
    end

    subgraph OrchestrationLayer["Autonomous Multi-Agent Layer"]
        GMA["GrowthManagerAgent (Deterministic Pipeline)"]
        AG_ORCH["AgenticOrchestrator (Bounded ReAct Tool Loop)"]
        TOOL_REG["ToolRegistry (JSON Schema Domain Tools)"]
        CA["CustomerAgent (Audience Selection)"]
        OA["OfferAgent (Incentive Optimization)"]
        CPA["CampaignAgent (Copywriting & Channel)"]
        EA["ExperimentAgent (Cohort & Lift Measurement)"]
        PG["PermissionGateService (Deterministic Safety Guardrails)"]
        LLM["LLMService (Tool Calling & Strategic Reasoner)"]
    end

    subgraph IntelligenceLayer["Analytical Intelligence Layer"]
        C360["Customer 360 Engine"]
        RFM["RFM Segmentation Engine"]
        CHURN["Churn Predictor (Decay Model)"]
        CLV["CLV Estimator (12-Month Predictive)"]
        AFF["Co-Purchase Affinity Recommender"]
        PMA["Payment Method Performance Analyzer"]
        OD["Opportunity Detection Engines"]
    end

    subgraph DataLayer["Persistence, Vector Memory, and Event Bus"]
        PGDB[("PostgreSQL Database (Async Engine / NullPool)")]
        VEC_MEM[("ChromaDB Vector Store (384-Dim Semantic Memory)")]
        EMBED["EmbeddingService (FastEmbed / Local ONNX)"]
        EB["Domain Event Publisher & Consumer"]
        TRACE["Trace Logger & Hybrid Micro-Tool Retrieval"]
    end

    subgraph IntegrationLayer["Razorpay Test Mode Infrastructure"]
        RZP_CLI["Razorpay Client (Orders API / Key Secret Auth)"]
        RZP_WH["Razorpay Webhook Handler (HMAC-SHA256 Verification)"]
        RZP_GW["Razorpay Payment Gateway (Test Mode / UPI / Cards)"]
    end

    UI <--> API
    API --> GMA
    GMA --> C360
    C360 --> IntelligenceLayer
    OD --> GMA
    GMA --> CA
    GMA --> OA
    GMA --> CPA
    GMA --> PG
    GMA --> EA
    GMA --> LLM

    EA --> RZP_CLI
    RZP_CLI --> RZP_GW
    RZP_GW --> RZP_WH
    RZP_WH --> EB
    EB --> DataLayer
    DataLayer --> API
```

---

## 3. Layered Architectural Stack

| Layer | Responsibility | Primary Modules |
|---|---|---|
| 1. Simulation & Ingestion | Generates realistic merchant transaction telemetry (500 customers, 2,000 orders) with authentic power-law spend curves. | `app/simulator/` |
| 2. Integration Layer | Communicates with Razorpay REST APIs for order generation and validates incoming HMAC signatures on webhooks. | `app/integrations/` |
| 3. Event Layer | Decoupled asynchronous in-memory event bus broadcasting domain events (`order.paid`, `payment.captured`, `campaign.launched`). | `app/events/` |
| 4. Data & Knowledge Layer | Customer 360 unified profiles, relational PostgreSQL persistence, and JSON session snapshot archiving. | `app/models/`, `app/customer_360/`, `app/schemas/` |
| 5. Intelligence Layer | Deterministic mathematical algorithms for RFM segmentation, churn scoring, predictive CLV, product affinities, and opportunity detection. | `app/intelligence/` |
| 6. Multi-Agent Layer | Role-specialized agents coordinating audience segmentation, incentive economics, messaging copy, and randomized cohort splits. | `app/agents/` |
| 7. Cross-Cutting Services | Real-time webhook lift measurement, deterministic Permission Gate safety evaluation, context aggregation, session tracing, and LLM orchestration. | `app/services/` (`live_experiment_service`, `permission_gate_service`, `context_engine`, `trace_logger_service`, `trace_tool_service`, `llm_service`) |
| 8. Action Layer | Campaign execution engines, template renderers, Razorpay checkout session generators, and message dispatchers. | `app/actions/` |
| 9. API & Interface Layer | High-performance FastAPI asynchronous endpoints, SSE streaming hooks, session trace inspection, and merchant dashboard. | `app/api/`, `app/static/` |

---

## 4. Relational Database Schema and Entity Relationships

The platform utilizes asynchronous PostgreSQL managed via SQLAlchemy 2.0. The connection layer is configured with `NullPool` to ensure connection isolation across asynchronous request boundaries and test runners.

```mermaid
erDiagram
    MERCHANT ||--o{ CUSTOMER : owns
    MERCHANT ||--o{ PRODUCT : catalogs
    MERCHANT ||--o{ ORDER : processes
    MERCHANT ||--o{ OPPORTUNITY : discovers
    MERCHANT ||--o{ CAMPAIGN : executes
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER ||--o{ EXPERIMENT_ASSIGNMENT : assigned_to
    ORDER ||--o{ PAYMENT : records
    OPPORTUNITY ||--o{ CAMPAIGN : triggers
    CAMPAIGN ||--o{ EXPERIMENT_ASSIGNMENT : tracks
    WEBHOOK_EVENT ||--o{ PAYMENT : verifies

    MERCHANT {
        string id PK
        string name
        string category
        datetime created_at
    }

    CUSTOMER {
        string id PK
        string merchant_id FK
        string name
        string email
        string customer_segment
        float total_spend_amount
        int total_orders_count
        float churn_risk_score
        float predicted_lifetime_value
        datetime last_purchase_timestamp
    }

    PRODUCT {
        string id PK
        string merchant_id FK
        string title
        string category
        float price
    }

    ORDER {
        string id PK
        string merchant_id FK
        string customer_id FK
        string product_id FK
        string razorpay_order_id
        float amount
        string status
        datetime created_at
    }

    PAYMENT {
        string id PK
        string order_id FK
        string razorpay_payment_id
        string payment_method
        float amount
        string status
        datetime created_at
    }

    OPPORTUNITY {
        string id PK
        string merchant_id FK
        string title
        string opportunity_type
        text description
        int target_audience_count
        float estimated_gmv_impact
        float confidence_score
        string status
    }

    CAMPAIGN {
        string id PK
        string opportunity_id FK
        string name
        string channel
        string offer_details
        string status
        float treatment_conversion_rate
        float control_conversion_rate
        float incremental_revenue_generated
    }

    EXPERIMENT_ASSIGNMENT {
        string id PK
        string campaign_id FK
        string customer_id FK
        string variant
        string razorpay_order_id
        boolean is_converted
        float conversion_amount
        datetime converted_at
    }

    WEBHOOK_EVENT {
        string id PK
        string razorpay_event_id
        string event_name
        string entity_id
        json payload_json
        string status
        datetime received_at
    }
```

---

## 5. Razorpay Integration Architecture

### 5.1 Order Creation Lifecycle
When a campaign is launched for a target cohort:
1. `ExperimentAgent` splits the eligible audience into Treatment (80%) and Control (20%) cohorts.
2. For treatment customers, `LiveExperimentService` invokes `RazorpayClient.create_order()` with structured metadata notes:
   - `campaign_id`: ID of the running autonomous campaign.
   - `customer_id`: Unique identifier of the target customer.
   - `variant`: `treatment`.
   - `session_id`: Unique active growth management session ID.
3. Order and assignment rows are persisted in `orders` and `experiment_assignments` tables in PostgreSQL.

### 5.2 Webhook Ingestion and Verification
1. Razorpay dispatches `payment.captured` HTTP POST requests to `/api/v1/webhooks/razorpay`.
2. `RazorpayWebhookHandler.verify_signature()` computes `HMAC-SHA256(raw_body, secret)` and validates against the `X-Razorpay-Signature` header in constant time.
3. Raw event is archived in `webhook_events`.
4. `LiveExperimentService.record_webhook_payment()` matches the order via `razorpay_order_id` or notes metadata, marks `experiment_assignments.is_converted = True`, and updates the campaign conversion metrics in PostgreSQL.

---

## 6. Performance and Scalability Guarantees

- **Async I/O Throughout**: Built entirely on asyncpg and FastAPI, eliminating thread blocking on external API calls or database operations.
- **Connection Isolation**: Configured with `NullPool` to guarantee clean event loop lifecycle management under concurrent testing and production reloads.
- **Context Engine Optimization**: Analytical context is pre-aggregated and compressed into targeted key-value summaries before passing to LLM agents, keeping token overhead minimal.
