# Graph-Native Autonomous Fraud Investigation Agent (HH-GOA)

[![TigerGraph 4.2.2](https://img.shields.io/badge/TigerGraph-v4.2.2%20CE-orange.svg)](https://www.tigergraph.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-darkgreen.svg)](https://github.com/langchain-ai/langgraph)
[![Groq LLM](https://img.shields.io/badge/LLM-Groq%20openai%2Fgpt--oss--120b-purple.svg)](https://groq.com/)
[![Test Suite](https://img.shields.io/badge/Pytest-54%2F54%20Passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Autonomous, explainable, and policy-governed financial fraud investigation engine built on TigerGraph Community Edition, high-performance GSQL graph analytics, GraphRAG compliance grounding, and LangGraph multi-stage agentic reasoning.**

---

## 📑 Table of Contents

1. [Executive Summary & Core Differentiators](#1-executive-summary--core-differentiators)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Data Flow Diagrams (DFD Level 0 & Level 1)](#3-data-flow-diagrams-dfd)
4. [TigerGraph Knowledge Graph Schema & Topology](#4-tigergraph-knowledge-graph-schema--topology)
5. [The 7 Production GSQL Investigation Queries](#5-the-7-production-gsql-investigation-queries)
6. [GraphRAG Compliance Policy Engine (Rules R1–R10)](#6-graphrag-compliance-policy-engine-rules-r1r10)
7. [LangGraph Agentic State Machine & Dual-Stage Decisioning](#7-langgraph-agentic-state-machine--dual-stage-decisioning)
8. [The Breakthrough: Device-Sharing False-Positive Mitigation](#8-the-breakthrough-device-sharing-false-positive-mitigation)
9. [20-Case Benchmark Evaluation & Audit Results](#9-20-case-benchmark-evaluation--audit-results)
10. [Analyst Review Dashboard & Graph Visualizer](#10-analyst-review-dashboard--graph-visualizer)
11. [Automated Verification Test Suite (54 Tests)](#11-automated-verification-test-suite-54-tests)
12. [Quickstart & Operations Guide](#12-quickstart--operations-guide)
13. [Engineering Roadmap](#13-engineering-roadmap)
14. [License & Acknowledgments](#14-license--acknowledgments)

---

## 1. Executive Summary & Core Differentiators

Financial institutions face an operational crisis: legacy rule-based fraud detection engines produce false-positive rates exceeding 90%, inundating analysts with manual reviews. Conversely, experimental generative AI fraud agents exhibit **epistemic recklessness**—hallucinating factual certainty, inventing corroborating evidence, and prematurely filing regulatory reports or blocking customer cards on ambiguous signals.

The **HH-GOA Autonomous Fraud Investigation Agent** introduces a paradigm shift:

* **Enterprise Graph Scale**: Models **590,742 transactions**, **144,432 identity records**, and **5,585 fraud cases** in TigerGraph Community Edition (778,640 active vertices, 3,934,692 active edges).
* **Sub-50ms Graph Analytics**: Executes 7 compiled GSQL queries that evaluate multi-hop topological indicators (velocity bursts, out-of-region hops, card testing sequences, device sharing rings, and historical case memory).
* **Honest Uncertainty Handling**: When evidence is ambiguous, the system **explicitly refuses to fabricate confirmations**. Instead of forcing a binary fraud verdict, it escalates the case as `uncertain` / `pending_verification`, applies non-destructive provisional safeguards (`MONITOR_CARD`, `STEP_UP_AUTH`, `VERIFY_WITH_CUSTOMER`), and defers irreversible actions (`BLOCK_CARD`, `FILE_SAR`) until definitive proof is obtained.
* **Dual-Stage Action Protocol**: Formulates both `initial` (immediate protective) and `final` (conclusive post-investigation) action recommendations, auditable via an explicit `what_changed` differential.
* **Closed-Loop Graph Write-Back**: Writes investigation findings, provisional decisions, and structured evidence vertices back into TigerGraph, transforming live alerts into persistent case memory for future investigations.
* **Full Automated Rigor**: Backed by **54 automated pytest tests** covering schema integrity, exact data reconciliations, pattern fidelity, and regulatory SAR-verdict alignment.

---

## 2. End-to-End System Architecture

```
                                  ================================
                                     REAL-TIME TRANSACTION ALERT
                                  ================================
                                                 │
                                                 ▼
     ┌────────────────────────────────────────────────────────────────────────────────────────┐
     │ 1. TRIGGER & VALIDATION NODE                                                           │
     │    • Validates TransactionID existence against TigerGraph database                     │
     │    • Initializes state container & establishes audit session                           │
     └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                                 │
                                                 ▼
     ┌────────────────────────────────────────────────────────────────────────────────────────┐
     │ 2. TIGERGRAPH GSQL ENGINE (7 Installed Production Queries)                             │
     │    ├─ get_transaction_context ───► Resolves 1-hop neighborhood (Card, Customer, Device)│
     │    ├─ get_customer_history    ───► 90-day baseline spend, product mix, normal regions  │
     │    ├─ detect_card_testing     ───► Identifies rapid micro-auths (<= $5) + high spike   │
     │    ├─ detect_device_sharing   ───► Quantifies cross-account device profile fanout      │
     │    ├─ detect_out_of_region    ───► Compares current billing region vs registered home  │
     │    ├─ detect_new_device_flag  ───► Checks identity proxy/newness flags (id_15, id_23)  │
     │    └─ get_similar_cases       ───► Dynamic topological retrieval across 5,565 cases   │
     └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                                 │ Multi-Hop Graph Signals & Topology
                                                 ▼
     ┌────────────────────────────────────────────────────────────────────────────────────────┐
     │ 3. GRAPHRAG COMPLIANCE POLICY GROUNDING                                                │
     │    • Maps topological signals against regulatory and operational rules (R1 through R10)│
     │    • Identifies mandatory procedural constraints (e.g., Senior Approval for card blocks)│
     └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                                 │ Extracted Evidence + Grounded Policies
                                                 ▼
     ┌────────────────────────────────────────────────────────────────────────────────────────┐
     │ 4. LANGGRAPH UNCERTAINTY ASSESSOR (Groq: openai/gpt-oss-120b)                          │
     │    • Evaluates fraud typology (card_testing, account_takeover, cnp_fraud, none)        │
     │    • Calculates confidence score (0.00 – 1.00) and risk level (low, medium, high)      │
     │    • Evaluates uncertainty boundary: needs_more_evidence = (0.15 <= conf <= 0.85)     │
     └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                                 │ Risk Assessment State
                                                 ▼
     ┌────────────────────────────────────────────────────────────────────────────────────────┐
     │ 5. DUAL-STAGE ACTION RECOMMENDATION                                                    │
     │    • Initial Actions: Immediate provisional safeguards (STEP_UP_AUTH, MONITOR_CARD)    │
     │    • Evidence Assessment: Pauses if unconfirmed; avoids fabricating synthetic replies  │
     │    • Final Actions: Conclusive resolutions (BLOCK_CARD, CLEAR_TXN) + what_changed diff │
     └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                                 │ Evaluated Decision State
                                                 ▼
     ┌────────────────────────────────────────────────────────────────────────────────────────┐
     │ 6. REGULATORY SAR DETERMINATION                                                        │
     │    • Regulatory Invariant: sar.file=true ONLY if final verdict='fraud'                 │
     │    • Defers SAR filing on all 17 uncertain/escalated cases to eliminate false reports   │
     │    • Formulates structured FinCEN Narrative (Subject, Mechanics, Graph Traversal)      │
     └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                                 │ Final Dossier Package
                                                 ▼
     ┌────────────────────────────────────────────────────────────────────────────────────────┐
     │ 7. CASE WRITE-BACK TO TIGERGRAPH                                                       │
     │    • Upserts FraudCase vertex with updated verdict, status, and confidence             │
     │    • Instantiates Decision vertices (initial & final actions) linked via HAS_DECISION  │
     │    • Instantiates Evidence vertices (claims & query citations) linked via HAS_EVIDENCE │
     │    • Updates MATCHES_PATTERN edge to reference FraudPattern typology                   │
     └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                                 │ Persisted Graph State
                                                 ▼
     ┌────────────────────────────────────────────────────────────────────────────────────────┐
     │ 8. ANALYST REVIEW DASHBOARD (FastAPI + Cytoscape.js)                                   │
     │    • 20-Case executive ledger with status badges & pattern filtering                   │
     │    • Live Cytoscape topological subgraph visualization with interactive nodes          │
     │    • Side-by-side Initial vs Final action plan inspection with audit trails            │
     └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow Diagrams (DFD)

### DFD Level 0: Context Diagram

```
                               ┌────────────────────────────────┐
                               │   Card Payment Network / Core  │
                               └───────────────┬────────────────┘
                                               │ Ingest Stream (CSV / REST)
                                               ▼
     ┌──────────────────┐             ┌─────────────────┐             ┌──────────────────┐
     │   Bank Analyst   │◄────────────┤  HH-GOA AGENT   │◄────────────┤ Compliance Policy│
     │    (Reviewer)    │  Case Dossier│   INVESTIGATION │  Rules R1-10│  Knowledge Base  │
     └──────────────────┘  & Dashboard│     ENGINE      │             └──────────────────┘
                                      └────────┬────────┘
                                               │ Query Traversals & Write-Back
                                               ▼
                               ┌────────────────────────────────┐
                               │      TigerGraph CE 4.2.2       │
                               │   (778k Vertices, 3.9M Edges)  │
                               └────────────────────────────────┘
```

### DFD Level 1: Subsystem Data Flow

```
 [ Txn Alert ]
       │
       ▼
 [ 1.0 Trigger ] ─────────► (Query Txn) ──────────► [ TigerGraph DB ]
       │                                                   │
 (State Init)                                        (Graph Neighbors)
       ▼                                                   │
 [ 2.0 Feature Extraction & GSQL ] ◄───────────────────────┘
       │
 (Topology Signals: velocity, hops, fanout, prior cases)
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
              (Dual Snapshot: Initial / Final)
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

## 4. TigerGraph Knowledge Graph Schema & Topology

The graph schema is defined in [gsql/schema.gsql](file:///d:/HH%20X%20Tiger/gsql/schema.gsql). It comprises **11 vertex types** and **20 directed edge types** (represented by 16 forward edges and auto-generated reverse edges in TigerGraph catalog):

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

### Vertex Topology & Ingestion Statistics

| Vertex Type | Primary Key Format | Count Loaded | Source File | Description |
|---|---|:---:|---|---|
| **`Transaction`** | `transaction_id` (String) | **590,742** | `transactions.csv` | Core event: amount, timestamp, channel, product code, model score, V/C/D blobs. |
| **`IdentityRecord`**| `identity_id` (String) | **144,432** | `identity.csv` | Technical device attributes, proxy flags (`id_23`), device newness (`id_15`/`id_28`). |
| **`FraudCase`** | `case_id` (e.g. `HHG-001`, `CC-0001`) | **5,585** | `cases.csv` + pack | 5,565 historical closed fraud cases + 20 active benchmark evaluation cases. |
| **`Customer`** | `customer_id` (e.g. `C01234`) | **13,564** | Derived | Deduplicated cardholder identity entity anchoring ownership and baseline history. |
| **`Card`** | `card_id` (e.g. `C01234-K1`) | **13,944** | Derived | Payment card entity linking network (`card4`), type (`card6`), and home billing address (`addr1`). |
| **`DeviceProfile`**| `device_profile_id` (Composite) | **9,705** | Composite | Unique hardware/software fingerprint (`DeviceInfo|OS|Browser|Screen`). |
| **`BillingRegion`**| `region_code` (e.g. `444.0`) | **332** | `addr1` | Geographic billing district code used to detect out-of-region card-present hops. |
| **`EmailDomain`** | `domain_name` (e.g. `gmail.com`)| **60** | `P/R_emaildomain` | Purchaser and recipient email domain vertices for syndication link analysis. |
| **`FraudPattern`** | `pattern_code` | **7** | Reference | 7 standard typologies (`card_testing`, `account_takeover`, `out_of_region_use`, etc.). |
| **`Decision`** | `case_id-DEC-xx` | **176** | Graph Write-Back | Operational actions generated by the agent (initial & final phases). |
| **`Evidence`** | `case_id-EVD-xx` | **93** | Graph Write-Back | Structured claims, GSQL query citations, and confidence metrics. |
| **Total Vertices** | | **778,640** | | |

---

## 5. The 7 Production GSQL Investigation Queries

Installed in TigerGraph via [gsql/investigation_queries.gsql](file:///d:/HH%20X%20Tiger/gsql/investigation_queries.gsql):

```
                               ┌────────────────────────────────────────────────────────┐
                               │           7 INSTALLED GSQL INVESTIGATION QUERIES       │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
         ┌──────────────────┬──────────────────┬──────────┴───────┬──────────────────┬──────────────────┐
         ▼                  ▼                  ▼                  ▼                  ▼                  ▼
┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐┌──────────────────┐
│1. Context        ││2. History        ││3. Card Testing   ││4. Device Sharing ││5. Out of Region  ││6. New Device Flag│
│get_transaction_  ││get_customer_     ││detect_card_      ││detect_device_    ││detect_out_of_    ││detect_new_device_│
│context           ││history           ││testing           ││sharing           ││region            ││flag              │
└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘└──────────────────┘
                                                          │
                                                          ▼
                                               ┌──────────────────────┐
                                               │7. Case Memory        │
                                               │get_similar_cases     │
                                               └──────────────────────┘
```

1. **`get_transaction_context(STRING txn_id)`**
   * **Intent**: 1-hop neighborhood traversal resolving the transaction's Card, Customer, DeviceProfile, IdentityRecord, BillingRegion, and EmailDomains.
   * **Output**: Complete entity graph subgraph centered on the alert transaction.

2. **`get_customer_history(STRING customer_id, STRING txn_id, INT lookback_days)`**
   * **Intent**: Temporal aggregation of all prior transactions for the customer across all cards prior to the anchor timestamp.
   * **Output**: Total transaction count, average/min/max spend, channel distribution (`online` vs `in_person`), product code distribution, and set of historical billing regions.

3. **`detect_card_testing(STRING card_id, STRING customer_id, INT window_minutes)`**
   * **Intent**: Algorithmic detection of automated bot testing attacks.
   * **Signature**: Traverses online authorizations looking for $\ge 3$ rapid micro-authorizations ($\le \$5.00$) followed by a larger transaction attempt ($\ge \$15.00$) within a 60-minute sliding window.

4. **`detect_device_sharing(STRING txn_id, STRING device_profile_id)`**
   * **Intent**: Evaluates multi-card device fanout across distinct accounts.
   * **Safeguard**: Excludes null/empty/placeholder fingerprints (`|||`) to eliminate false clustering.
   * **Output**: Connected customer count, connected card count, and sample transactions.

5. **`detect_out_of_region(STRING txn_id)`**
   * **Intent**: Pattern 4 detection (card-present travel anomaly).
   * **Signature**: Checks if an in-person transaction occurred in a billing region never previously visited by the cardholder, while simultaneously verifying if normal activity continues at home within 48 hours.

6. **`detect_new_device_flag(STRING txn_id)`**
   * **Intent**: Identity verification check.
   * **Signature**: Evaluates `IdentityRecord` device newness flags (`id_15 == "New"`, `id_28 == "New"`), proxy masking (`id_23 == "anonymous"`), and computes whether the customer has prior successful history on this hardware profile.

7. **`get_similar_cases(STRING txn_id, STRING customer_id, INT top_k)`**
   * **Intent**: Dynamic topological case memory retrieval.
   * **Signature**: Traverses shared entities (Card, Customer, DeviceProfile, BillingRegion) into historical `FraudCase` vertices, scoring and returning the most relevant confirmed historical outcomes.

---

## 6. GraphRAG Compliance Policy Engine (Rules R1–R10)

Implemented in [agent/policy_rag.py](file:///d:/HH%20X%20Tiger/agent/policy_rag.py), the policy engine encodes institutional banking risk procedures and regulatory guidelines into deterministic constraints:

| Rule ID | Policy Name | Trigger Condition | Required Evidence Item | Mandatory Approval Route | SAR Implication |
|:---:|---|---|---|---|:---:|
| **R1** | Out-of-Region Card Present | In-person txn in new region differing from card registered address | Verification of cardholder travel or physical possession | Analyst Approval | Optional |
| **R2** | Online High-Velocity New Device | Online transaction on previously unseen device | Device newness flag (`id_15` = New) + velocity spike | Analyst Approval | Required if confirmed |
| **R3** | Account Takeover Protocol | Rapid identity updates followed by high-risk transactions | Multi-card device fanout + customer dispute | Senior Approval | **Mandatory** |
| **R4** | Anonymous Proxy Screening | Transaction routing through TOR/anonymous VPN (`id_23`) | IP masking indicator | Automated Step-Up | Deferred |
| **R5** | Card Testing Detection | Sequence of $\ge 3$ micro-auths ($\le \$5$) + large attempt | GSQL `detect_card_testing` positive match | Senior Approval | **Mandatory** |
| **R6** | Multi-Card Device Fanout | Single hardware profile shared across $>3$ distinct customer accounts | GSQL `detect_device_sharing` match + corroborating signal | Senior Approval | Required if confirmed |
| **R7** | Customer Dispute Escalation | Customer-reported unauthorized charge | Dispute ticket + baseline deviation | Analyst Approval | Case Dependent |
| **R8** | Irreversible Action Safeguard | Freezing accounts or placing hard card blocks | Conclusive graph proof or two corroborating signals | Senior Approval | Mandatory |
| **R9** | Model Score Discordance | Bank model score $>0.75$ with normal behavioral baseline | Baseline comparison audit | Automated Monitor | Deferred |
| **R10** | Multi-Card Compromise | $\ge 2$ cards owned by same customer flagged simultaneously | Customer portfolio traversal | Senior Approval | **Mandatory** |

---

## 7. LangGraph Agentic State Machine & Dual-Stage Decisioning

The orchestration pipeline in [agent/investigation_agent.py](file:///d:/HH%20X%20Tiger/agent/investigation_agent.py) is compiled as a stateful directed acyclic graph in LangGraph:

```
[trigger] ──► [gather_evidence] ──► [ground_policy] ──► [assess_uncertainty]
                                                               │
                                                               ▼
[write_to_case] ◄── [generate_explanation] ◄── [check_sar_requirement] ◄── [recommend_action]
```

### The Honest Uncertainty Protocol

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

1. **Phase 1 (Initial Recommendation)**: Formulates non-destructive provisional safeguards (`STEP_UP_AUTH`, `VERIFY_WITH_CUSTOMER`, `MONITOR_CARD`) designed to prevent immediate financial loss without harming legitimate customers.
2. **Phase 2 (Evidence Evaluation)**: In an offline benchmark where live cardholders cannot respond, the engine **explicitly refuses to hallucinate customer admissions**. It pauses irreversible actions and preserves the `uncertain / pending_verification` status.
3. **Phase 3 (Final Recommendation & Action Diff)**: Records both initial and final action states with an audited `what_changed` explanation, demonstrating exactly why irreversible blocks were executed or safely deferred.

---

## 8. The Breakthrough: Device-Sharing False-Positive Mitigation

During early testing, an algorithmic audit revealed a critical systemic flaw in device-sharing heuristics:

* **The Defect**: Common operating systems, browsers, and screen resolutions (e.g., standard Windows 10 with Google Chrome at 1920x1080) coalesce into identical device fingerprints shared by hundreds of distinct legitimate cardholders. Naive fraud systems flagged every transaction on these common profiles as multi-card account takeover rings.
* **The Solution**: We re-engineered the decision logic to mandate that **device sharing is a weak signal that cannot prove fraud in isolation**. The engine now enforces that device-sharing count must co-occur with at least one corroborating indicator:
  1. A `New` hardware flag (`id_15` or `id_28`) on the specific customer's profile.
  2. An out-of-baseline transaction amount ($> 90$-day average).
  3. An anonymous proxy connection (`id_23` = anonymous).
  4. An active cardholder dispute.
  5. A verified match to a historical confirmed fraud syndicate.

This refinement eliminated false-positive account takeover classifications across the entire benchmark.

---

## 9. 20-Case Benchmark Evaluation & Audit Results

The agent executed autonomous investigations across all 20 official benchmark evaluation cases (`HHG-001` through `HHG-020`):

### Portfolio Summary Metrics

| Metric | Result | Benchmark Significance |
|---|:---:|---|
| **Evaluated Benchmark Cases** | **20 / 20** | 100% completion with valid answer schemas |
| **Definitively Resolved as Fraud** | **3** | Supported by conclusive, multi-point graph proof (`HHG-010`, `HHG-011`, `HHG-014`) |
| **Honestly Escalated (Uncertain)** | **17** | Correctly deferred pending live verification; zero hallucinated admissions |
| **Regulatory SARs Mandated** | **3** | Exact 1:1 coincidence with confirmed fraud; zero premature filings |
| **Regulatory SARs Deferred** | **17** | Deferral protects institution from filing unsubstantiated regulatory reports |
| **TigerGraph Write-Back Success** | **20 / 20** | 100% written to `FraudCase`, `Decision`, and `Evidence` vertices |

### Complete 20-Case Investigation Ledger

| Case ID | Txn ID | Matched Pattern | Risk | Conf | Verdict | Status | SAR | Key Graph Evidence & Operational Rationale |
|---|---|---|:---:|:---:|---|---|:---:|---|
| **HHG-001** | `3514030` | `none` | Med | 0.61 | `uncertain` | `escalated` | ❌ | In-person $77 txn fits 90-day baseline; customer dispute recorded; awaiting cardholder interview. |
| **HHG-002** | `3478782` | `card_not_present_fraud` | High | 0.78 | `uncertain` | `escalated` | ❌ | $292 online purchase exceeds 90-day max ($90); high model score (0.79); step-up auth enacted. |
| **HHG-003** | `3530164` | `none` | Low | 0.40 | `uncertain` | `escalated` | ❌ | Normal in-person $49 txn; no card testing; dispute alone does not outweigh baseline consistency. |
| **HHG-004** | `3583227` | `card_not_present_new_device` | High | 0.78 | `uncertain` | `escalated` | ❌ | New device flags (`id_15`/`id_28` = New) + dispute; matches historical case CC-3778; step-up auth needed. |
| **HHG-005** | `3523199` | `account_takeover` | High | 0.78 | `uncertain` | `escalated` | ❌ | New device + unseen product code (R) + prior fraud link (`CC-2400`); card monitored. |
| **HHG-006** | `3476682` | `card_not_present_new_device` | High | 0.78 | `uncertain` | `escalated` | ❌ | $482 online txn on new device with shared OS; requires step-up authentication before blocking. |
| **HHG-007** | `3514948` | `none` | Med | 0.40 | `uncertain` | `escalated` | ❌ | In-person purchase in home region; elevated model score (0.87); monitored for anomalies. |
| **HHG-008** | `3558054` | `account_takeover` | Med | 0.62 | `uncertain` | `escalated` | ❌ | Shared device + dispute; spend is within normal range; identity verification requested. |
| **HHG-009** | `3581141` | `card_not_present_new_device` | Med | 0.62 | `uncertain` | `escalated` | ❌ | Online purchase on new device; low bank model score; out-of-band customer verification sent. |
| **HHG-010** | `3506725` | `card_not_present_new_device` | High | 0.88 | **`fraud`** | **`closed_fraud`** | ✅ | **Confirmed Fraud:** Unseen device, spend $1,000 exceeds $670 max, matches confirmed fraud case. |
| **HHG-011** | `3583368` | `card_testing` | Crit | 0.92 | **`fraud`** | **`closed_fraud`** | ✅ | **Confirmed Fraud:** 225 rapid micro-authorizations followed by high-value spike attempt. |
| **HHG-012** | `3553342` | `none` | Med | 0.60 | `uncertain` | `escalated` | ❌ | In-person low-value txn matching baseline; no device or regional anomalies; transaction cleared. |
| **HHG-013** | `3526826` | `account_takeover` | High | 0.78 | `uncertain` | `escalated` | ❌ | Online purchase on new device + shared email domain signal matching prior case (`CC-4294`). |
| **HHG-014** | `3478561` | `account_takeover` | High | 0.88 | **`fraud`** | **`closed_fraud`** | ✅ | **Confirmed Fraud:** Unseen device + anonymous proxy (`id_23`) + identical confirmed fraud profile. |
| **HHG-015** | `3464869` | `card_not_present_new_device` | High | 0.78 | `uncertain` | `escalated` | ❌ | $599 online spend exceeds baseline max on new device; matches `CC-0615`; awaiting verification. |
| **HHG-016** | `3534820` | `card_not_present_new_device` | High | 0.78 | `uncertain` | `escalated` | ❌ | New device with disputed charge matching prior device fingerprint; step-up verification enacted. |
| **HHG-017** | `3450629` | `none` | Low | 0.62 | `uncertain` | `escalated` | ❌ | Spend below 90-day average; known device (3 prior uses); no fraud indicators; flagged for review. |
| **HHG-018** | `3491361` | `none` | Low | 0.70 | `uncertain` | `escalated` | ❌ | In-person $39 purchase matching baseline; dispute alone insufficient for fraud classification. |
| **HHG-019** | `3503878` | `card_not_present_new_device` | High | 0.78 | `uncertain` | `escalated` | ❌ | Model score 0.90 on new device; channel matches history; provisional hold pending confirmation. |
| **HHG-020** | `3509359` | `card_not_present_new_device` | Med | 0.62 | `uncertain` | `escalated` | ❌ | Online txn from new device for customer with 100% in-person history; step-up auth triggered. |

---

## 10. Analyst Review Dashboard & Graph Visualizer

The application includes an executive review dashboard located in [dashboard/](file:///d:/HH%20X%20Tiger/dashboard):

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  HH-GOA FRAUD INVESTIGATION CONSOLE               [Total: 20]  [Fraud: 3]  [Uncertain: 17]  [SARs: 3]   │
├──────────────────────────────────┬──────────────────────────────────────────────────────────────────────┤
│ BENCHMARK CASES                  │ CASE DETAILS: HHG-006 (Transaction: 3476682)                         │
│ ──────────────────────────────── │ ──────────────────────────────────────────────────────────────────── │
│ [!] HHG-001  none       0.61  ES │ Status: ESCALATED  |  Verdict: UNCERTAIN  |  Risk: HIGH  |  SAR: NO     │
│ [!] HHG-002  cnp_fraud  0.78  ES │                                                                      │
│ [!] HHG-003  none       0.40  ES │ ┌─────────────────────────────┐ ┌──────────────────────────────────┐ │
│ [!] HHG-004  cnp_new_dev0.78  ES │ │ INITIAL PROVISIONAL ACTIONS │ │ FINAL EVALUATED ACTIONS          │ │
│ [!] HHG-005  acct_takeov0.78  ES │ │ • STEP_UP_AUTH (Auto)       │ │ • STEP_UP_AUTH (Auto)            │ │
│ [>] HHG-006  cnp_new_dev0.78  ES │ │ • VERIFY_WITH_CUSTOMER      │ │ • MONITOR_CARD (Auto)            │ │
│ [!] HHG-007  none       0.40  ES │ │ • MONITOR_CARD (Auto)       │ │ (Provisional hold; defer block)  │ │
│ [!] HHG-008  acct_takeov0.62  ES │ └─────────────────────────────┘ └──────────────────────────────────┘ │
│ [!] HHG-009  cnp_new_dev0.62  ES │                                                                      │
│ [*] HHG-010  cnp_new_dev0.88  FR │ INTERACTIVE TOPOLOGICAL SUBGRAPH (Cytoscape.js)                      │
│ [*] HHG-011  card_test  0.92  FR │                                                                      │
│ [!] HHG-012  none       0.60  ES │                     [ Customer: C08432 ]                             │
│ [!] HHG-013  acct_takeov0.78  ES │                              │                                       │
│ [*] HHG-014  acct_takeov0.88  FR │                              ▼                                       │
│ [!] HHG-015  cnp_new_dev0.78  ES │                      [ Card: C08432-K1 ]                             │
│ [!] HHG-016  cnp_new_dev0.78  ES │                              │                                       │
│ [!] HHG-017  none       0.62  ES │                              ▼                                       │
│ [!] HHG-018  none       0.70  ES │                    [ Txn: 3476682 ($482) ]                           │
│ [!] HHG-019  cnp_new_dev0.78  ES │                       /              \                               │
│ [!] HHG-020  cnp_new_dev0.62  ES │                      ▼                ▼                              │
│                                  │          [ DeviceProfile ]    [ BillingRegion: 444.0 ]                   │
│                                  │         (Shared OS / New)                                                │
└──────────────────────────────────┴──────────────────────────────────────────────────────────────────────┘
```

* **Interactive Network Explorer**: Powered by Cytoscape.js, dynamically rendering the 2-hop neighborhood of any selected case (Transaction, Card, Customer, DeviceProfile, and Historical Case precedents).
* **Dual Action Comparison**: Visually compares `initial` safeguards against `final` actions with explicit `what_changed` commentary.
* **FinCEN SAR Narrative Viewer**: Displays fully formatted regulatory Suspicious Activity Reports for confirmed fraud cases.

---

## 11. Automated Verification Test Suite (54 Tests)

Run the test suite using `pytest`:

```bash
pytest -v
```

### Verified Test Suite Breakdown (100% Pass Rate in 0.51s)

```
tests\test_data_load_counts.py .........                                 [ 16%]
tests\test_pattern_consistency.py .....................                  [ 55%]
tests\test_sar_consistency.py .....................                      [ 94%]
tests\test_schema_counts.py ...                                          [100%]

============================= 54 passed in 0.51s ==============================
```

* **`test_data_load_counts.py` (9 tests)**: Verifies exact row counts against the data dictionary for all 9 loaded entity types (590,742 transactions, 144,432 identity records, 5,585 fraud cases, 13,564 customers, 13,944 cards, 9,705 device profiles, 332 billing regions, 60 email domains, 7 fraud patterns).
* **`test_schema_counts.py` (3 tests)**: Asserts the existence of all 11 vertex types and 16 forward edge types in the active graph catalog.
* **`test_pattern_consistency.py` (21 tests)**: Programmatically verifies that all 20 benchmark case outputs match upstream LLM assessments with 0% pattern mutation or drift.
* **`test_sar_consistency.py` (21 tests)**: Validates regulatory compliance invariants—asserting that `sar.file: true` only coincides with confirmed fraud, and that all 17 uncertain cases strictly defer SAR filings.

---

## 12. Quickstart & Operations Guide

### Step 1: Environment Setup
Clone the repository and install dependencies:

```bash
git clone https://github.com/aryapatel23/TigerGraph-AI-Fraud-Investigation-HHGOA.git
cd TigerGraph-AI-Fraud-Investigation-HHGOA

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 2: Configure Environment Variables
Copy [.env.example](file:///d:/HH%20X%20Tiger/.env.example) to `.env`:

```bash
cp .env.example .env
```

Ensure `.env` contains:
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

### Step 3: Launch TigerGraph Community Edition Container
Choose either Docker Compose or direct Docker run:

#### Option A: Docker Compose (Recommended)
```bash
docker compose up -d
```

#### Option B: Direct Docker Run
```bash
docker run -d --name tigergraph-hhgoa \
  -p 14240:14240 -p 9000:9000 -p 14022:22 \
  -v tg-hhgoa-data:/home/tigergraph/tigergraph/data \
  tigergraph/community:4.2.2

docker exec -it tigergraph-hhgoa gadmin start
```

#### Verify Health & Vertex Counts
```bash
python agent/scripts/tg_status.py
```

### Step 4: Provision Schema, Load Data, and Install Queries
```bash
# 1. Apply vertex and edge schema
python agent/scripts/apply_schema.py

# 2. Run high-throughput GSQL loading jobs
python agent/scripts/load_data.py

# 3. Compile and install the 7 GSQL queries
python agent/scripts/install_queries.py
```

### Step 5: Execute Investigations & Launch Dashboard
```bash
# Run benchmark investigations and generate answer packages
python agent/scripts/run_uncertainty_benchmark.py
python agent/scripts/generate_all_answers.py

# Launch analyst dashboard
python dashboard/server.py
```
Open **`http://localhost:8080`** in your browser.

> For a complete rehearsal script and scene-by-scene presentation walkthrough for hackathon judges, consult **[docs/demo_video_guide.md](file:///d:/HH%20X%20Tiger/docs/demo_video_guide.md)**.

---

## 13. Engineering Roadmap

1. **Graph Neural Network (GNN) Embeddings**: Augment GraphRAG retrieval with inductive topological node embeddings (Node2Vec or Graph Convolutional Networks) to capture multi-hop structural similarities across fraud rings.
2. **Unsupervised Community Detection in GSQL**: Integrate graph-wide Louvain and Weakly Connected Component algorithms directly into GSQL to detect emergent synthetic identity clusters before transaction alerts fire.
3. **Asynchronous Human-in-the-Loop Webhooks**: Replace offline benchmark simulations with live asynchronous webhooks (SMS cardholder verification, 3DS step-up push notifications, senior analyst approval tasks) to transition cases from `escalated` to final resolution in real time.

---

## 14. License & Acknowledgments

* **License**: Open-source under the [MIT License](LICENSE).
* **Core Technologies**: Built with [TigerGraph](https://www.tigergraph.com/), [LangGraph](https://github.com/langchain-ai/langgraph), and [Groq](https://groq.com/).
* **Dataset**: IEEE-CIS Financial Fraud Detection Benchmark, adapted for the TigerGraph Hacker House Goa 2026 Hackathon.
