# Hackathon Demonstration Runbook

This guide walks through the 7-step presentation flow to demonstrate the autonomous RazorGrowth AI platform to judges.

---

## The Core Demonstration Thesis

> *"RazorGrowth AI is not a conversational chatbot or a passive dashboard. It is an autonomous growth engine that continuously monitors Razorpay transaction telemetry, detects revenue leakage, formulates margin-safe recovery campaigns, executes real Razorpay test orders, and measures true incremental GMV through PostgreSQL-backed A/B experiments."*

---

## 7-Step Demonstration Walkthrough

```
Step 1: Generate Synthetic Merchant Dataset (500 customers, 2,000 orders)
   |
Step 2: Inspect Customer 360 Profiles & Behavioral Cohorts
   |
Step 3: Trigger Multi-Agent Growth Scan
   |
Step 4: Review Multi-Agent Action Plan & Dynamic Permission Gate
   |
Step 5: Launch Autonomous Campaign (Real Razorpay Orders Created)
   |
Step 6: Capture Conversion via Razorpay Webhook Lifecycle
   |
Step 7: Verify Real-Time Lift & Incremental GMV in PostgreSQL
```

---

### Step 1: Generate the Synthetic Merchant Dataset
- **Endpoint**: `POST /api/v1/simulator/generate?merchant_name=StyleKart&customer_count=500&order_count=2000`
- **What happens**: Generates a simulated merchant (`StyleKart`), product catalog (Apparel, Footwear, Electronics), 500 customer profiles, and 2,000 order transactions over a 90-day window.
- **Key Pattern Seeded**: A cluster of VIP customers who spent > 5,000 INR but have been inactive for over 30 days.

```bash
curl -X POST "http://localhost:8000/api/v1/simulator/generate?merchant_name=StyleKart&customer_count=500&order_count=2000"
```

---

### Step 2: Inspect Customer 360 & Intelligence Layer
- **Endpoint**: `GET /api/v1/customers?merchant_id=<MERCHANT_ID>` or via Dashboard Drawer
- **What happens**: Demonstrates unified customer profiles with computed RFM segments, 3-factor churn risk scores, and 12-month predictive CLV.

---

### Step 3: Trigger Autonomous Growth Scan
- **Endpoint**: `POST /api/v1/growth/scan/<MERCHANT_ID>`
- **What happens**: The Opportunity Detectors scan transaction recency, co-purchase affinity, and payment method failure rates.
- **Discovered Opportunities**:
  1. **Dormant VIP Recovery**: Re-engages high-spend customers inactive > 30 days.
  2. **Payment Optimization**: Detects payment method drop-offs below the 92.0% benchmark.
  3. **Cross-Sell Affinity**: Association rule discovery for category bundles.

---

### Step 4: Review Multi-Agent Action Plan & Permission Gate
- **What the Agents decide**:
  1. **CustomerAgent**: Filters and ranks the target cohort by `(total_spend, CLV)`.
  2. **OfferAgent**: Determines the optimal margin-safe incentive (`WELCOME15`, `VIP20OFF`, or `UPISWIFT`).
  3. **CampaignAgent**: Generates personalized copy referencing the customer's favorite category.
  4. **PermissionGateService**: Evaluates dynamic financial guardrails against store GMV.
     - *If within budget limits*: Returns `AUTO_APPROVED`.
     - *If exceeding limits*: Prompts interactive merchant override or safe audience cap.

---

### Step 5: Launch Autonomous Campaign (Real Razorpay Orders)
- **Endpoint**: `POST /api/v1/campaigns/launch/<OPPORTUNITY_ID>`
- **What happens**:
  - `ExperimentAgent` splits the cohort into 80% Treatment and 20% Control.
  - `LiveExperimentService` calls the official Razorpay SDK (`POST /v1/orders`) in Test Mode, generating real `razorpay_order_id` references with structured metadata notes (`campaign_id`, `customer_id`, `variant`).
  - Assignments are stored in the PostgreSQL `experiment_assignments` table.

---

### Step 6: Conversion Capture via Razorpay Webhook Lifecycle
The platform supports two conversion capture paths:

- **Path A (Live Interactive Test Checkout via ngrok)**:
  1. Open Razorpay Checkout in test mode and authorize payment with a test card/UPI.
  2. Razorpay sends an HMAC-SHA256 signed `payment.captured` webhook to `/api/v1/webhooks/razorpay`.
  3. Signature is verified in constant time, the webhook event is logged, and the customer assignment is marked `is_converted = True`.

- **Path B (Fast Demo Mode via UI Button)**:
  1. Click **"Complete Razorpay Test Payment"** in the dashboard.
  2. Invokes `POST /api/v1/experiments/webhook-payment`, which feeds an authentic-structure `payment.captured` payload into `LiveExperimentService.record_webhook_payment()`.
  3. Writes to PostgreSQL tables `webhook_events`, `payments`, and updates `experiment_assignments.is_converted = True`.

---

### Step 7: Measure Real-Time Lift & Incremental GMV
- **Endpoint**: `GET /api/v1/experiments/results/<CAMPAIGN_ID>`
- **What happens**: `LiveExperimentService` reads the real `experiment_assignments` rows from PostgreSQL and invokes `ExperimentAgent.calculate_experiment_metrics()`:
  - Treatment Conversion Rate: Computed directly from converted treatment rows.
  - Control Conversion Rate: Computed from organic control rows.
  - Absolute Difference: Quantified in percentage points.
  - Incremental Orders & GMV: Mathematically calculated against counterfactual control baseline.
  - Output is verified with the label: **MEASURED VIA RAZORPAY TEST MODE**.
