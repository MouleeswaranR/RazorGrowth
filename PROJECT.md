# RazorGrowth AI — Project Specification & Mission Statement

---

## 1. Executive Vision & System Goal

**RazorGrowth AI** is an autonomous AI Growth Manager for merchants on the Razorpay ecosystem. It moves beyond passive reporting dashboards and conversational chatbots by closing the loop between data intelligence and real commerce actions:

$$\mathbf{Observe} \longrightarrow \mathbf{Understand} \longrightarrow \mathbf{Find\ Opportunity} \longrightarrow \mathbf{Decide} \longrightarrow \mathbf{Act} \longrightarrow \mathbf{Measure} \longrightarrow \mathbf{Learn}$$

### Core Operational Objectives
1. **Connect Razorpay Integration**: Ingest real payment lifecycle events (Orders, Payments, Webhooks, Refunds).
2. **Synthesize Merchant Ecosystem**: Model customer demographics, product catalog, and historical orders with seeded behavioral patterns.
3. **Build Customer 360**: Maintain unified behavioral and RFM metrics for every customer profile.
4. **Discover High-ROI Opportunities**: Autonomously detect revenue leakages (e.g., dormant VIP cohorts, cross-sell affinities, payment method drop-offs).
5. **Formulate & Execute Campaigns**: Generate personalized incentives (e.g., discount coupons) and dispatch targeted multi-channel communications.
6. **Execute Conversions via Razorpay**: Trigger real Razorpay test transactions when targeted customers purchase.
7. **Mathematically Quantify GMV Lift**: Run rigorous A/B experiments (treatment vs. control) to measure net incremental revenue generated.

---

## 2. Core Documentation Links

All developers and AI coding agents must align implementation details with the documents inside the [`docs/`](file:///c:/Users/ffmou/Desktop/razorpay/docs) directory:

* **[System Architecture](file:///c:/Users/ffmou/Desktop/razorpay/docs/ARCHITECTURE.md)**: Deep dive into the 9 layers, domain event bus, Razorpay integration, observability stack, and the autonomous growth loop.
* **[File Inventory & Implementation Status](file:///c:/Users/ffmou/Desktop/razorpay/docs/FILE_INVENTORY_AND_STATUS.md)**: Exhaustive audit of all codebase files, their production purpose, current implementation, and status classification (`[INTEGRATED]`, `[SCAFFOLD / HEURISTIC]`, `[SIMULATION / MOCKED]`).
* **[Multi-Agent System](file:///c:/Users/ffmou/Desktop/razorpay/docs/AGENTS.md)**: Specifications for specialized domain agents, ReAct loop, consensus builder, and Permission Gates.


---

## 3. Strict Coding Standards & Behavioral Rules

All modifications across the codebase must adhere to the following rules without exception:

### Code Style Rules
- **Functions**: Single responsibility; aim for under 30 lines.
- **Naming**: Explicit and descriptive; no abbreviations (`resolve_import_path`, not `res_imp_pth`).
- **Docstrings**: Every exported function/class gets a one-line doc comment describing *what* it does, not *how*.
- **Inline Comments**: Comment only non-obvious logic inline — avoid narrating obvious code.
- **Single Responsibility per File**: One file = one responsibility. Each agent resides in its own file under [`app/agents/`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents).
- **File Length**: Keep files under ~150 lines. If a file grows beyond that, split it logically.
- **Agent Registry**: Before writing a new agent, check [`app/agents/`](file:///c:/Users/ffmou/Desktop/razorpay/app/agents) for existing logic.

### Forbidden Anti-Patterns
- ❌ **No catch-all files** (`utils.py`, `helpers.py`, `misc.py`) that accumulate unrelated logic.
- ❌ **No commented-out dead code** — delete unused code; git history preserves it.
- ❌ **No vague identifiers** (`data`, `temp`, `handle_stuff`, `do_thing`).
- ❌ **No single-row Postgres inserts** — always batch insert with `session.add_all()`.
- ❌ **No hardcoded credentials or API keys** — always route via `.env` and [`app/config/settings.py`](file:///c:/Users/ffmou/Desktop/razorpay/app/config/settings.py).
- ❌ **No duplicate helpers** — maintain unified shared logic.

---

## 4. Pre-Change Planning Protocol

> [!IMPORTANT]
> **MANDATORY PLANNING REQUIREMENT**
> Before implementing any major architectural change, introducing new agents, or modifying core schemas, you **MUST** provide a detailed Implementation Plan in Markdown format for user review and approval before writing code.

### Required Plan Format:
```markdown
# [Proposed Feature / Architectural Change]

## 1. Goal & Context
Brief explanation of the objective and its alignment with PROJECT.md.

## 2. Impacted Components & File Paths
- [MODIFY] [file basename](file:///absolute/path/to/modifiedfile)
- [NEW] [file basename](file:///absolute/path/to/newfile)

## 3. Implementation Details
Step-by-step breakdown of changes, function signatures, and data models.

## 4. Verification & Testing Plan
Automated tests and manual API verification steps.
```
