# Graph-Native Autonomous Fraud Investigation Agent (HH-GOA)

[![TigerGraph 4.2.2](https://img.shields.io/badge/TigerGraph-v4.2.2%20CE-orange.svg)](https://www.tigergraph.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-darkgreen.svg)](https://github.com/langchain-ai/langgraph)
[![Groq LLM](https://img.shields.io/badge/LLM-Groq%20openai%2Fgpt--oss--120b-purple.svg)](https://groq.com/)
[![Test Suite](https://img.shields.io/badge/Pytest-54%2F54%20Passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Autonomous financial fraud investigation powered by TigerGraph, LangGraph, and Groq (`openai/gpt-oss-120b`).**

An autonomous fraud investigation system that transforms static tabular transactions and entity records into a connected graph database (590,742 transactions, 144,432 identity records, and 5,585 cases), evaluates real-time transaction alerts via 7 specialized GSQL queries, grounds reasoning in banking compliance policies, and conducts multi-turn risk investigations. Unlike conventional automated fraud systems that force every ambiguous signal into an artificial binary verdict, this agent is built with **honest uncertainty handling**: when graph and behavioral evidence cannot conclusively prove fraud or innocence, the agent explicitly refuses to fabricate synthetic confirmations or jump to conclusions. Instead, it escalates the case as `uncertain` / `pending_verification`, proposes non-destructive provisional safeguards (e.g., card monitoring, step-up authentication, customer verification requests), and defers irreversible penalties and Suspicious Activity Report (SAR) filings until definitive corroborating evidence is secured.

---

## Architecture Diagram

```
                                  [ Transaction Alert ]
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  Trigger Node   │
                                   │ (Validate Txn)  │
                                   └────────┬────────┘
                                            │
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │      TigerGraph GSQL Engine (MCP)       │
                       │ ─────────────────────────────────────── │
                       │ 1. get_transaction_context              │
                       │ 2. get_customer_history                 │
                       │ 3. detect_card_testing                  │
                       │ 4. detect_device_sharing                │
                       │ 5. detect_out_of_region                 │
                       │ 6. detect_new_device_flag               │
                       │ 7. get_similar_cases                    │
                       └────────────────────┬────────────────────┘
                                            │ Extracted Evidence & Graph Context
                                            ▼
                               ┌─────────────────────────┐
                               │  GraphRAG Policy Ground │
                               │ (Rules R1-R10 Retrieval)│
                               └────────────┬────────────┘
                                            │ Policy Rules + Topology Signals
                                            ▼
                         ┌─────────────────────────────────────┐
                         │   LangGraph Uncertainty Assessor    │
                         │      (Groq: openai/gpt-oss-120b)    │
                         │ ─────────────────────────────────── │
                         │ • Pattern Matching & Typology       │
                         │ • Confidence Scoring (0.00 - 1.00)  │
                         │ • needs_more_evidence Determination │
                         └──────────────────┬──────────────────┘
                                            │ Risk Assessment State
                                            ▼
                         ┌─────────────────────────────────────┐
                         │     Action Recommendation Node      │
                         │ ─────────────────────────────────── │
                         │ • Initial Provisional Actions       │
                         │ • Evidence Gathering Simulation     │
                         │ • Final Actions & what_changed Diff │
                         └──────────────────┬──────────────────┘
                                            │ Final Action Plan
                                            ▼
                         ┌─────────────────────────────────────┐
                         │       SAR Determination Node        │
                         │ (Coincidence Check: Verdict=Fraud)  │
                         └──────────────────┬──────────────────┘
                                            │ SAR Decision + Structured Narrative
                                            ▼
                         ┌─────────────────────────────────────┐
                         │     Case Write-Back to Graph        │
                         │ (Upsert FraudCase, Decision, Evid)  │
                         └──────────────────┬──────────────────┘
                                            │ Graph Updated & Synced
                                            ▼
                         ┌─────────────────────────────────────┐
                         │       Web Review Dashboard          │
                         │ (FastAPI/Light Theme + Cytoscape.js)│
                         └─────────────────────────────────────┘
```

### Data Flow Diagram (DFD Level 0: System Context)

```
                               ┌────────────────────────────────┐
                               │   Card Payment Network / Core  │
                               └───────────────┬────────────────┘
                                               │ Real-Time Alert Ingest
                                               ▼
     ┌──────────────────┐             ┌─────────────────┐             ┌──────────────────┐
     │   Bank Analyst   │◄────────────┤  HH-GOA AGENT   │◄────────────┤ Compliance Policy│
     │    (Reviewer)    │  Case Dossier│   INVESTIGATION │  Rules R1-10│  Knowledge Base  │
     └──────────────────┘  & Dashboard│     ENGINE      │             └──────────────────┘
                                      └────────┬────────┘
                                               │ GSQL Traversals & Case Write-Back
                                               ▼
                               ┌────────────────────────────────┐
                               │      TigerGraph CE 4.2.2       │
                               │   (778k Vertices, 3.9M Edges)  │
                               └────────────────────────────────┘
```

### Data Flow Diagram (DFD Level 1: Subsystem Multi-Hop Flow)

```
 [ Txn Alert ]
       │
       ▼
 [ 1.0 Trigger Node ] ────────► (Query Txn) ──────────► [ TigerGraph DB ]
       │                                                       │
 (State Container)                                       (1-Hop Neighbors)
       ▼                                                       │
 [ 2.0 Feature Extraction & GSQL ] ◄───────────────────────────┘
       │
 (Topology Signals: velocity, card testing, device sharing, region hops)
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
 [ 3.0 Policy Grounding ]              [ 4.0 GSQL Case Memory ]
  (Match Rules R1-R10)                  (Traverse SIMILAR_TO_CASE)
       │                                         │
 (Applicable Policies)                   (Prior Precedents)
       │                                         │
       └────────────────────┬────────────────────┘
                            │
                            ▼
               [ 5.0 LangGraph Assessor ]
               (Groq: openai/gpt-oss-120b)
                            │
                   (Risk Assessment)
                            ▼
              [ 6.0 Action Recommender ]
              (Dual Snapshot: Initial vs Final)
                            │
                    (Decision State)
                            ▼
               [ 7.0 SAR Compliance ]
               (Verdict=Fraud Coincidence Check)
                            │
                   (Complete Dossier)
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
 [ 8.0 Graph Write-Back ]             [ 9.0 Dashboard Engine ]
 (Upsert Decision & Evidence)         (Cytoscape Subgraph Viewer)
         │                                     │
         ▼                                     ▼
 [ TigerGraph DB ]                    [ Analyst Web Console ]
```

---

## Repository Structure

```
.
├── agent/                       # Core agent implementation and utility scripts
│   ├── investigation_agent.py   # 8-node LangGraph autonomous pipeline
│   ├── policy_rag.py            # GraphRAG policy retriever for rules R1-R10
│   ├── scripts/                 # Operational scripts for data loading, audits, and runs
│   │   ├── tg_status.py         # Instant TigerGraph health & vertex count inspector
│   │   ├── smoke_mcp.py         # Standalone TigerGraph MCP tool execution verifier
│   │   ├── apply_schema.py      # Deploys gsql/schema.gsql to TigerGraph
│   │   ├── load_data.py         # Executes GSQL loading jobs and validates row counts
│   │   ├── install_queries.py   # Compiles and installs the 7 core GSQL queries
│   │   ├── run_uncertainty_benchmark.py # Executes assessment over 20 benchmark cases
│   │   ├── generate_all_answers.py      # Produces final submission JSON answers
│   │   ├── audit_pattern_consistency.py # Regression audit for upstream-to-final pattern matching
│   │   └── format_benchmark_table.py    # Formats benchmark verification summaries
├── cases/                       # Benchmark inputs, dry-run evaluations, and generated outputs
│   ├── dry_run_uncertainty_assessment.json # Canonical LLM uncertainty evaluations
│   └── HHG-001_answer.json ... HHG-020_answer.json # 20 final verified case answer packages
├── config/                      # Agent & protocol configurations
│   └── mcp_tools.yaml           # Curated TigerGraph MCP whitelist tool declarations
├── dashboard/                   # Self-contained web review interface
│   ├── server.py                # Python HTTP/REST backend (port 8080)
│   ├── index.html               # Clean, accessible light-theme single-page app
│   ├── app.js                   # Reactive case viewer and Cytoscape.js graph visualizer
│   └── style.css                # Professional typography, responsive layout, and contrast tokens
├── data/                        # Dataset schemas and raw ingestion inputs
│   └── HHGOA_IEEE/              # IEEE-CIS transaction and identity records
│       ├── transactions.csv     # 590,742 raw transaction rows
│       ├── identity.csv         # 144,432 identity attribute rows
│       ├── closed_cases_history.csv # 5,565 historical resolved cases
│       └── case_pack.csv        # 20 active benchmark evaluation cases
├── docs/                        # Architecture and data reconciliation documentation
│   ├── demo_video_guide.md      # Scene-by-scene presentation & recording guide for judges
│   ├── data-dictionary.md       # Exact field specifications and row-count reconciliations
│   └── schema-design.md         # Vertex/edge topology design and trade-off rationales
├── gsql/                        # Native TigerGraph GSQL definitions
│   ├── schema.gsql              # Graph schema: 11 vertex types and 20 edge definitions
│   ├── loading_jobs.gsql        # High-throughput batch ingestion pipelines
│   └── investigation_queries.gsql # 7 production-grade GSQL queries
├── tests/                       # Formal automated pytest test suite (54/54 passing)
│   ├── conftest.py              # Shared TigerGraph fixtures and connection management
│   ├── test_schema_counts.py    # Topology assertions (11 vertex types, 16 forward edges)
│   ├── test_data_load_counts.py # Data integrity assertions against data dictionary
│   ├── test_pattern_consistency.py # 20-case pattern fidelity regression tests
│   └── test_sar_consistency.py  # Regulatory SAR-to-verdict alignment tests
├── docker-compose.yml           # Container orchestration with health checks and volume persistence
├── .env.example                 # Template for environment and database credentials
├── pytest.ini                   # Pytest configuration and warning filters
├── requirements.txt             # Runtime production dependencies
└── requirements-dev.txt         # Testing and development tooling
```

---

## What Makes This Investigation Approach Distinct

This system was engineered with an emphasis on production rigor, data veracity, and auditable decision boundaries rather than black-box heuristic guesswork:

1. **Strict Data Reconciliation Prior to Construction**  
   Before any query or agent logic was written, the source datasets were exhaustively cataloged in [docs/data-dictionary.md](file:///d:/HH%20X%20Tiger/docs/data-dictionary.md). Ingestion runs were audited against exact row counts from the source files: exactly **590,742** transactions, **144,432** identity records, and **5,585** fraud cases (5,565 historical + 20 benchmark) were loaded without silent drops, truncated records, or missing relationships.

   ```
          ┌──────────┐                     ┌──────────┐
          │ Customer │◄─────── OWNS ───────┤   Card   │
          └────┬─────┘                     └────┬─────┘
               │                                │
               │ INVOLVES_CUSTOMER              │ MADE
               ▼                                ▼
          ┌──────────┐       INVOLVES_TXN  ┌─────────────┐       BILLED_IN     ┌───────────────┐
          │FraudCase │◄────────────────────┤ Transaction ├────────────────────►│ BillingRegion │
          └────┬─────┘                     └──────┬──────┘                     └───────────────┘
               │                                  │
               ├───────────────┐                  ├────────────────────────────┐
               │               │                  ▼                            ▼
         HAS_DECISION    HAS_EVIDENCE      ┌─────────────┐              ┌───────────────┐
               │               │           │DeviceProfile│              │IdentityRecord │
               ▼               ▼           └─────────────┘              └───────────────┘
          ┌──────────┐   ┌──────────┐             ▲                            ▲
          │ Decision │   │ Evidence │             │ FROM_DEVICE                │ HAS_IDENTITY
          └──────────┘   └──────────┘             └────────────────────────────┘
   ```

2. **Detection and Correction of Device-Sharing False Positives**  
   During initial testing of device fingerprinting, common operating system and browser configurations (such as generic Windows 10/Chrome setups) produced shared device counts spanning hundreds of cards. Naive fraud detection algorithms treat any high degree of device sharing as an automatic fraud ring or account takeover. We diagnosed this flaw and updated the reasoning engine to enforce that **device-sharing count alone is never sufficient evidence for fraud**. The model now mandates corroborating signals—such as a `New` device flag on the specific customer's profile, a customer dispute, a dramatic departure from the customer's 90-day baseline spend, or an explicit match to a historical confirmed fraud pattern—before flagging high risk.

3. **Honest Uncertainty Handling Over Fabricated Confirmations**  
   In a static, offline benchmark, real customer responses or live multi-factor authentication outcomes cannot be queried dynamically. Rather than inventing simulated responses (such as fabricating that a customer "confirmed the charge was unauthorized"), the agent honors the epistemic limits of the data:
   - **17 of the 20 benchmark cases** are honestly escalated with status `escalated`, verdict `uncertain`, and `sar.file: false`. Non-destructive provisional actions (`VERIFY_WITH_CUSTOMER`, `STEP_UP_AUTH`, `MONITOR_CARD`, `CREATE_CASE`, `ESCALATE_TO_ANALYST`) are enacted while blocking and regulatory filing are deferred.
   - Only **3 of the 20 cases** (`HHG-010`, `HHG-011`, and `HHG-014`) are resolved definitively as `fraud` based strictly on conclusive, multi-point graph evidence (e.g., rapid-fire 225 card testing micro-authorizations or coordinated proxy + new device + confirmed historical case links).

   ```
                        ┌──────────────────────────────────────────────┐
                        │           assess_uncertainty Node            │
                        │         Evaluates Model Confidence           │
                        └──────────────────────┬───────────────────────┘
                                               │
                        ┌──────────────────────┴───────────────────────┐
                        ▼                                              ▼
          ┌───────────────────────────┐                  ┌───────────────────────────┐
          │   CONFIDENCE >= 0.88      │                  │   0.15 <= CONFIDENCE < 0.88│
          │   OR CONCLUSIVE PROOF     │                  │   SIGNALS AMBIGUOUS       │
          └─────────────┬─────────────┘                  └─────────────┬─────────────┘
                        │                                              │
                        ▼                                              ▼
          ┌───────────────────────────┐                  ┌───────────────────────────┐
          │  Definitive Resolution    │                  │  Honest Escalation        │
          │  • verdict: "fraud"       │                  │  • verdict: "uncertain"   │
          │  • status: "closed_fraud" │                  │  • status: "escalated"    │
          │  • sar.file: true         │                  │  • sar.file: false        │
          │  • Final Action:          │                  │  • Provisional Actions:   │
          │    BLOCK_CARD, FILE_SAR   │                  │    STEP_UP, MONITOR_CARD  │
          └───────────────────────────┘                  └───────────────────────────┘
   ```

4. **Automated Auditing Against Pattern Mutation Regressions**  
   To prevent downstream pipeline stages from independently re-deriving or overwriting upstream assessments, we built an automated audit script ([agent/scripts/audit_pattern_consistency.py](file:///d:/HH%20X%20Tiger/agent/scripts/audit_pattern_consistency.py)). When an upstream LLM assessment identified `card_testing` on `HHG-011` but downstream nodes drifted to `account_takeover`, the audit flagged the mismatch. We resolved the bug by enforcing strict pattern pass-through across all LangGraph state transitions and integrated this check into the continuous regression suite.

5. **Exhaustive Automated Test Suite**  
   The system is fortified by **54 automated pytest tests** covering graph topology, loaded entity reconciliations, cross-case pattern fidelity, and SAR regulatory alignment—executing with a 100% pass rate.

---

## Quickstart

### 1. Prerequisites
- Docker Community Edition
- Python 3.10+ (tested on Python 3.12)
- Groq API Key

### 2. Start TigerGraph Community Edition Container
You can start TigerGraph using either **Docker Compose** or direct **Docker run**:

#### Option A: Docker Compose (Recommended)
```bash
docker compose up -d
```

#### Option B: Direct Docker Run
```bash
# Pull the community image
docker pull tigergraph/community:4.2.2

# Start the container
docker run -d --name tigergraph-hhgoa \
  -p 14240:14240 -p 9000:9000 -p 14022:22 \
  -v tg-hhgoa-data:/home/tigergraph/tigergraph/data \
  tigergraph/community:4.2.2

# Initialize TigerGraph services
docker exec -it tigergraph-hhgoa gadmin start
```

#### Verify Container Readiness
Check that TigerGraph services and RESTPP are operational:
```bash
python agent/scripts/tg_status.py
```


### 3. Configure Environment Variables
Copy [.env.example](file:///d:/HH%20X%20Tiger/.env.example) to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Ensure `.env` matches the following configuration:
```ini
TG_HOST=http://localhost
TG_PORT=14240
TG_RESTPP_PORT=14240
TG_GS_PORT=14240
TG_USERNAME=tigergraph
TG_PASSWORD=tigergraph
TG_GRAPH_NAME=FraudInvestigation
TG_GRAPHNAME=FraudInvestigation
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 5. Deploy Graph Schema, Ingest Data, and Install Queries
Execute the provisioning scripts in order:

```bash
# Step A: Apply vertex and edge schema
python agent/scripts/apply_schema.py

# Step B: Run GSQL loading jobs to ingest data
python agent/scripts/load_data.py

# Step C: Install the 7 core GSQL investigation queries
python agent/scripts/install_queries.py
```

### 6. Run Benchmark & Generate Answer Packages
Run the uncertainty benchmark and generate all 20 final answer files:

```bash
# Run uncertainty evaluation across all 20 cases
python agent/scripts/run_uncertainty_benchmark.py

# Generate full case packages with what_changed action diffs and graph write-backs
python agent/scripts/generate_all_answers.py
```

### 7. Launch the Case Review Dashboard
Start the local review dashboard server:

```bash
python dashboard/server.py
```
Open your browser and navigate to `http://localhost:8080` to inspect cases, view initial vs. final action plans, and explore interactive Cytoscape.js subgraphs.

---

## Test Suite

The automated test suite verifies database schema integrity, data load completeness, pipeline state consistency, and compliance alignment without manual inspection.

Run the test suite using `pytest`:

```bash
pytest -v
```

### Test Suite Execution Output
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\HH X Tiger
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1, langsmith-0.14.0
collected 54 items

tests\test_data_load_counts.py .........                                 [ 16%]
tests\test_pattern_consistency.py .....................                  [ 55%]
tests\test_sar_consistency.py .....................                      [ 94%]
tests\test_schema_counts.py ...                                          [100%]

============================= 54 passed in 0.51s ==============================
```

### Test Suite Scope
- **`test_schema_counts.py` (3 tests):** Validates that exactly 11 vertex types and 16 registered forward edge types (representing the 20 edge relationships defined in `gsql/schema.gsql`) exist in the active graph catalog.
- **`test_data_load_counts.py` (9 tests):** Asserts exact row-count matches across all loaded entities:
  - `Transaction`: 590,742
  - `IdentityRecord`: 144,432
  - `FraudCase`: 5,585 (5,565 historical + 20 benchmark)
  - `Customer`: 13,564
  - `Card`: 13,944
  - `DeviceProfile`: 9,705
  - `BillingRegion`: 332
  - `EmailDomain`: 60
  - `FraudPattern`: 7
- **`test_pattern_consistency.py` (21 tests):** Verifies all 20 cases to guarantee that the pattern assigned during initial uncertainty assessment is preserved without drift or overwrite throughout downstream action recommendation and answer generation.
- **`test_sar_consistency.py` (21 tests):** Enforces regulatory compliance rules—verifying that `sar.file == True` only ever coincides with `verdict == "fraud"`, and that all 17 uncertain/escalated cases defer SAR filings.

---

## Results Summary

Across the 20 benchmark evaluation cases (`HHG-001` through `HHG-020`), the agent completed full investigations, established initial vs. final action plans, evaluated SAR filing mandates, and recorded 20/20 outcomes back into the graph.

### Benchmark Distribution Overview

| Metric | Result | Notes |
|---|:---:|---|
| **Total Evaluated Cases** | **20** | Benchmark test pack (`HHG-001` to `HHG-020`) |
| **Definitively Resolved (Fraud)** | **3** | Conclusive evidence: `HHG-010`, `HHG-011`, `HHG-014` |
| **Honestly Escalated (Uncertain)** | **17** | Escalated pending customer/analyst verification |
| **SARs Mandated (`sar.file: true`)** | **3** | Coincides strictly with the 3 confirmed fraud cases |
| **SARs Deferred (`sar.file: false`)** | **17** | Deferred pending verification on all uncertain cases |
| **Graph Write-Back Success Rate** | **20 / 20** | 100% written back to `FraudCase`, `Decision`, `Evidence` |

### Case-by-Case Benchmark Breakdown

| Case ID | Flagged Txn ID | Matched Typology | Verdict | Status | SAR File | Risk Level | Confidence | Primary Evidence / Operational Rationales |
|---|---|---|---|---|:---:|---|:---:|---|
| **HHG-001** | `3514030` | `none` | `uncertain` | `escalated` | `false` | `medium` | 0.61 | In-person purchase below 90-day baseline; customer dispute flagged; pending cardholder interview. |
| **HHG-002** | `3478782` | `card_not_present_fraud` | `uncertain` | `escalated` | `false` | `high` | 0.78 | $292 online purchase exceeds 90-day max ($90); high bank model score (0.79); step-up auth required. |
| **HHG-003** | `3530164` | `none` | `uncertain` | `escalated` | `false` | `low` | 0.40 | In-person $49 txn fits normal history; customer dispute recorded; monitoring card. |
| **HHG-004** | `3583227` | `card_not_present_new_device` | `uncertain` | `escalated` | `false` | `high` | 0.78 | Brand new device flags (`id_15`/`id_28` = New) + customer dispute; step-up verification needed. |
| **HHG-005** | `3523199` | `account_takeover` | `uncertain` | `escalated` | `false` | `high` | 0.78 | New device + unseen product code (R) + historical fraud match (`CC-2400`); card placed on hold. |
| **HHG-006** | `3476682` | `card_not_present_new_device` | `uncertain` | `escalated` | `false` | `high` | 0.78 | $482 spend on new device with shared OS fingerprint; requires step-up authentication before blocking. |
| **HHG-007** | `3514948` | `none` | `uncertain` | `escalated` | `false` | `medium` | 0.40 | In-person normal baseline; elevated bank model score (0.87); card monitored for anomalies. |
| **HHG-008** | `3558054` | `account_takeover` | `uncertain` | `escalated` | `false` | `medium` | 0.62 | Device sharing + customer dispute; spend is within normal range; identity verification requested. |
| **HHG-009** | `3581141` | `card_not_present_new_device` | `uncertain` | `escalated` | `false` | `medium` | 0.62 | Online purchase on new device; low risk score; out-of-band customer verification triggered. |
| **HHG-010** | `3506725` | `card_not_present_new_device` | `fraud` | `closed_fraud` | `true` | `high` | 0.88 | **Confirmed Fraud:** Unseen device, spend $1,000 exceeds $670 max, matches confirmed fraud case. |
| **HHG-011** | `3583368` | `card_testing` | `fraud` | `closed_fraud` | `true` | `critical` | 0.92 | **Confirmed Fraud:** Automated card testing pattern: 225 rapid micro-authorizations + large jump. |
| **HHG-012** | `3553342` | `none` | `uncertain` | `escalated` | `false` | `medium` | 0.60 | In-person low-value txn matching baseline; no device or regional anomalies; transaction cleared. |
| **HHG-013** | `3526826` | `account_takeover` | `uncertain` | `escalated` | `false` | `high` | 0.78 | Online transaction on new device + shared email domain signal matching prior case (`CC-4294`). |
| **HHG-014** | `3478561` | `account_takeover` | `fraud` | `closed_fraud` | `true` | `high` | 0.88 | **Confirmed Fraud:** Unseen device + anonymous proxy (`id_23`) + identical confirmed fraud profile. |
| **HHG-015** | `3464869` | `card_not_present_new_device` | `uncertain` | `escalated` | `false` | `high` | 0.78 | $599 online spend exceeds baseline max on new device; matches `CC-0615`; awaiting verification. |
| **HHG-016** | `3534820` | `card_not_present_new_device` | `uncertain` | `escalated` | `false` | `high` | 0.78 | New device with disputed charge matching prior device fingerprint; step-up verification enacted. |
| **HHG-017** | `3450629` | `none` | `uncertain` | `escalated` | `false` | `low` | 0.62 | Amount below 90-day average; known device (3 prior uses); no fraud indicators; flagged for review. |
| **HHG-018** | `3491361` | `none` | `uncertain` | `escalated` | `false` | `low` | 0.70 | In-person $39 purchase matching baseline; dispute alone insufficient for fraud classification. |
| **HHG-019** | `3503878` | `card_not_present_new_device` | `uncertain` | `escalated` | `false` | `high` | 0.78 | Model score 0.90 on new device; channel matches history; provisional hold pending customer confirmation. |
| **HHG-020** | `3509359` | `card_not_present_new_device` | `uncertain` | `escalated` | `false` | `medium` | 0.62 | Online txn from new device for a customer with 100% in-person history; step-up auth triggered. |

---

## What We'd Improve With More Time

1. **Dense Graph Vector Embeddings for GraphRAG**  
   The current GraphRAG implementation leverages structured graph queries and lexical rule retrieval. With additional development time, we would implement joint graph-and-text vector embeddings (using Node2Vec or Graph Convolutional Networks alongside dense text embeddings) to compute semantic similarity between unstructured analyst case notes and multi-hop graph subgraphs.

2. **Graph-Native Community Detection Algorithms in GSQL**  
   While the 7 installed GSQL queries effectively detect localized behavioral patterns (card testing, out-of-region use, immediate device sharing), we would expand the query suite to include graph-wide unsupervised algorithms (such as Louvain Community Detection and Weakly Connected Components) executed directly inside TigerGraph to automatically discover distributed, multi-ring synthetic identity networks.

3. **Asynchronous Human-in-the-Loop Webhook Integration**  
   To bridge the gap between static benchmark evaluation and live production workflows, we would replace offline evidence simulations with asynchronous webhooks. When the agent outputs `needs_more_evidence: true` and requests customer verification, the system would dispatch live SMS/push alerts or analyst approval tasks, pausing the LangGraph state until real-world corroboration arrives to trigger final case resolution.

---

## License and Credits

- **License:** Distributed under the MIT License.
- **Platform & Frameworks:** Built with [TigerGraph](https://www.tigergraph.com/), [LangGraph](https://github.com/langchain-ai/langgraph), and [Groq](https://groq.com/).
- **Data Source:** IEEE-CIS Fraud Detection benchmark dataset, adapted for the HH-GOA Autonomous Agent track.
