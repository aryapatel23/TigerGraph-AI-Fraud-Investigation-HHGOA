# 🎥 Demo Video Guide (Practice & Recording Script)

This guide provides an end-to-end rehearsal script and operational checklist to record a winning **3 to 5-minute hackathon presentation**.

---

## Part 1: Key Innovations to Emphasize

When presenting to judges, highlight these core differentiators:

| Feature | Implementation | Competitive Advantage |
|---|---|---|
| **Graph-Native Scale** | TigerGraph CE 4.2.2 | **590,742 transactions**, 144,432 identity records, and 5,585 fraud cases modeled and queried in sub-second latency. |
| **GSQL Query Engine** | 7 Installed GSQL Queries | Traverses multi-hop entity graphs (device sharing, card testing, regional anomalies, and historical case memory). |
| **Honest Uncertainty Handling** | LangGraph + Groq (`gpt-oss-120b`) | **Refuses to hallucinate synthetic evidence.** 17/20 benchmark cases are honestly escalated pending verification; only 3 cases with rock-solid evidence are closed as fraud. |
| **SAR Compliance Coincidence** | Regulatory Auditing | Regulatory Suspicious Activity Reports (SARs) are strictly tied to confirmed fraud (3 cases), never filed prematurely on ambiguous signals. |
| **Full Graph Write-Back** | Real-time GSQL Persistence | All decisions, provisional actions, and evidence items are persisted directly back to `FraudCase`, `Decision`, and `Evidence` graph vertices (20/20 cases). |
| **Interactive Dashboard** | Light-Theme UI + Cytoscape.js | High-contrast, executive-ready dashboard with live graph topology visualization, side-by-side action diffs, and audit trails. |
| **Continuous Verification** | 54 Automated Pytest Tests | 100% pass rate in 0.51s across schema topology, loaded row counts, pattern fidelity, and SAR alignment. |

---

## Part 2: Pre-Recording Checklist & Environment Setup

Run these commands in PowerShell before recording:

### 1. Verify TigerGraph Health
```powershell
.venv\Scripts\python scripts/tg_status.py
```
> Confirms all 11 vertex types and 778,640+ vertices are active.

### 2. Verify Test Suite (54/54 Passing)
```powershell
.venv\Scripts\pytest -v
```
> Confirms all 54 tests pass in ~0.5s.

### 3. Launch Dashboard Server
```powershell
.venv\Scripts\python dashboard/server.py
```
> Server starts on `http://localhost:8080`.

### 4. Setup Browser Tabs Side-by-Side
- **Tab 1:** `http://localhost:8080` (Case Review Dashboard)
- **Tab 2:** `http://localhost:14240` (TigerGraph GraphStudio — `FraudInvestigation` graph)
- **Tab 3:** Terminal ready to run `pytest`.

---

## Part 3: Scene-by-Scene Script (3 to 5 Minutes)

### 🎬 Scene 1: Problem & Honest Uncertainty (0:00 – 0:50)
- **Visual:** Dashboard homepage (`http://localhost:8080`) showing the header stats: 20 Cases Evaluated, 3 Confirmed Fraud, 17 Escalated / Pending Evidence, 3 SARs Filed.
- **Narrative:**
  > *"Hello! This is our Graph-Native Autonomous Fraud Investigation System for the TigerGraph Hacker House Goa 2026.*  
  > *Traditional fraud rules generate crippling false-positive rates, while naive LLM agents suffer from a fatal flaw: hallucination. When faced with missing or ambiguous signals, ordinary AI agents invent synthetic customer confirmations or force every ambiguous case into a premature fraud verdict.*  
  > *Our system is architected around **Honest Uncertainty Handling**. When multi-hop graph signals indicate risk but cannot conclusively prove malicious intent, our agent refuses to fabricate evidence. It takes non-destructive provisional safeguards—like card monitoring and step-up authentication—and escalates the case for real-world verification, deferring irreversible card blocks and regulatory SAR filings until confirmed."*

---

### 🎬 Scene 2: TigerGraph Enterprise Graph Architecture (0:50 – 1:40)
- **Visual:** Switch briefly to Tab 2 (GraphStudio) or show `agent/scripts/tg_status.py` output.
- **Narrative:**
  > *"Our foundation is built on TigerGraph Community Edition 4.2.2. We verified data integrity before writing a single rule, reconciling exact row counts against source data:*  
  > *590,742 transactions, 144,432 identity records, 13,564 customers, 13,944 cards, 9,705 device profiles, and 5,585 historical fraud cases.*  
  > *We installed 7 production GSQL queries executing in sub-50 milliseconds:*  
  > *From rapid card-testing micro-authorization detection and geographic hop analysis, to dynamic multi-hop case memory retrieval."*

---

### 🎬 Scene 3: The Ambiguous vs Confirmed Fraud Comparison (1:40 – 3:00) — ⭐ **KEY JUDGING MOMENT**
- **Visual:** Return to `http://localhost:8080`.
  1. Click **`HHG-006`** (Card Not Present on New Device).
     - Show the **Initial vs Final Action Comparison** table.
     - Point to Initial Actions: `STEP_UP_AUTH`, `VERIFY_WITH_CUSTOMER`, `MONITOR_CARD`.
     - Point out: `verdict: "uncertain"`, `status: "escalated"`, `sar.file: false`.
     - Highlight the Cytoscape subgraph showing the transaction connected to customer, card, and device.
  2. Click **`HHG-011`** (Confirmed Card Testing).
     - Point out: `verdict: "fraud"`, `status: "closed_fraud"`, `sar.file: true`, `confidence: 0.92`.
     - Show the evidence: 225 rapid micro-authorizations followed by a high-value jump.
- **Narrative:**
  > *"Let's see this in action on two distinct benchmark cases:*  
  > *In **HHG-006**, an online transaction occurred on a new device with a shared OS fingerprint. A naive system would immediately block the customer's card and file a SAR. But as our device-sharing audit proved, common browser fingerprints are shared by hundreds of legitimate users! Because no prior fraud was linked, our agent assigned high risk (0.78) but honestly marked the case as 'uncertain', recommended step-up authentication, and refused to file a SAR without corroboration.*  
  > *Now look at **HHG-011**. Here, our GSQL `detect_card_testing` query revealed an undeniable signature: 225 rapid micro-authorizations followed by a high-value spike. With conclusive topological proof, the agent decisively closed the case as fraud, recommended card cancellation, and generated a structured Suspicious Activity Report for FinCEN."*

---

### 🎬 Scene 4: Graph Write-Back & Complete Auditability (3:00 – 3:45)
- **Visual:** In the case detail panel, scroll to the **Decision & Graph Write-Back** section and FinCEN SAR narrative.
- **Narrative:**
  > *"Every single investigation step is fully auditable. Unlike systems that output ephemeral chat messages or static text files, our agent executes a real-time write-back into TigerGraph:*  
  > *It creates new `Decision` and `Evidence` vertices linked directly to the `FraudCase` node, making today's investigations instantly searchable as historical case memory for tomorrow's alerts."*

---

### 🎬 Scene 5: Verification & Automated Test Suite (3:45 – 4:15)
- **Visual:** Switch to Terminal and run `.venv\Scripts\pytest -v`.
- **Narrative:**
  > *"To ensure zero regressions, we maintain 54 automated pytest tests verifying schema topology, loaded row counts, upstream-to-downstream pattern consistency across all 20 cases, and regulatory SAR-verdict alignment. All 54 tests pass in half a second.*  
  > *Thank you, and we welcome your questions!"*
