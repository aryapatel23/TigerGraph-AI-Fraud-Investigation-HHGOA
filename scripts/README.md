# Scripts Directory

This directory contains the operational and development scripts for the **HH-GOA Autonomous Fraud Investigation Agent**.

## 🚀 Operational Scripts (Root)

| Script | Purpose | Command |
|---|---|---|
| **`tg_status.py`** | Inspects TigerGraph service health, RESTPP port, active vertex breakdown, and edge counts. | `python scripts/tg_status.py` |
| **`smoke_mcp.py`** | Standalone verification of TigerGraph Model Context Protocol (MCP) tool execution. | `python scripts/smoke_mcp.py` |
| **`apply_schema.py`** | Applies `gsql/schema.gsql` (11 vertex types, 20 edge definitions) to TigerGraph. | `python scripts/apply_schema.py` |
| **`load_data.py`** | Executes GSQL loading jobs to ingest transactions, identity records, and cases. | `python scripts/load_data.py` |
| **`install_queries.py`** | Compiles and installs the 7 core GSQL investigation queries into TigerGraph. | `python scripts/install_queries.py` |
| **`run_uncertainty_benchmark.py`** | Runs the 8-node LangGraph investigation agent across all 20 benchmark cases. | `python scripts/run_uncertainty_benchmark.py` |
| **`generate_all_answers.py`** | Generates final validated case answer packages with dual action plans. | `python scripts/generate_all_answers.py` |
| **`audit_pattern_consistency.py`** | Programmatically verifies 20/20 pattern consistency between upstream assessment and final output. | `python scripts/audit_pattern_consistency.py` |

## 🛠️ Internal Diagnostics & Utilities (`scripts/dev/`)

The `scripts/dev/` subdirectory contains internal diagnostic, exploratory, and verification tools used during development and regression testing:
- Device-sharing audits and graph edge verifications
- Query logic inspectors and prompt payload checkers
- Benchmark device profile inspections and test vertex cleanup utilities
