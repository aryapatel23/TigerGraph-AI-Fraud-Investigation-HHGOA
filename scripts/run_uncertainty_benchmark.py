import os
import sys
import csv
import json
import asyncio
from pathlib import Path

from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from agent.investigation_agent import build_investigation_graph

async def main():
    print("================================================================================")
    print("   LangGraph Fraud Investigation Agent — 20 Benchmark Cases Uncertainty Dry Run")
    print("================================================================================")

    case_pack_path = project_root / "data" / "HHGOA_IEEE" / "case_pack.csv"
    if not case_pack_path.exists():
        print(f"[ERROR] case_pack.csv not found at: {case_pack_path}")
        sys.exit(1)

    with open(case_pack_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cases = list(reader)

    print(f"Loaded {len(cases)} benchmark cases from case_pack.csv.")
    print("Compiling LangGraph workflow: trigger -> gather_evidence -> ground_policy -> assess_uncertainty...")
    app = build_investigation_graph()

    results_for_saving = []
    summary_rows = []

    print("\nRunning full investigation chain across all 20 cases...")
    print("-" * 80)

    for i, c in enumerate(cases, 1):
        case_id = c["case_id"]
        txn_id = c["flagged_txn_id"]
        trigger_type = c["trigger_type"]
        trigger_text = c["trigger_text"]
        try:
            risk_score = float(c["risk_score"]) if c.get("risk_score") else 0.0
        except ValueError:
            risk_score = 0.0

        print(f"[{i:02d}/20] Processing {case_id} (flagged_txn: {txn_id}, trigger: {trigger_type})...", end="", flush=True)

        initial_state = {
            "txn_id": txn_id,
            "case_id": case_id,
            "trigger_type": trigger_type,
            "trigger_text": trigger_text,
            "trigger_risk_score": risk_score,
            "transaction_context": None,
            "customer_history": None,
            "pattern_signals": None,
            "similar_cases": None,
            "policy_passages": None,
            "risk_assessment": None,
            "needs_more_evidence": False,
            "evidence_requests": [],
            "status": "init",
            "error": None
        }

        try:
            final_state = await app.ainvoke(initial_state)
            assessment = final_state.get("risk_assessment", {}) or {}
            risk_level = assessment.get("risk_level", "unknown")
            confidence = assessment.get("confidence", 0.0)
            pattern_matched = assessment.get("pattern_matched", "none")
            reasoning = assessment.get("reasoning", "")
            needs_ev = final_state.get("needs_more_evidence", False)
            ev_reqs = final_state.get("evidence_requests", [])

            print(" [DONE]")

            summary_rows.append({
                "case_id": case_id,
                "txn_id": txn_id,
                "pattern_matched": pattern_matched,
                "risk_level": risk_level,
                "confidence": confidence,
                "needs_more_evidence": needs_ev,
                "reasoning": reasoning
            })

            results_for_saving.append({
                "case_id": case_id,
                "flagged_txn_id": txn_id,
                "trigger_type": trigger_type,
                "trigger_text": trigger_text,
                "trigger_risk_score": risk_score,
                "risk_assessment": assessment,
                "needs_more_evidence": needs_ev,
                "evidence_requests": ev_reqs,
                "retrieved_policies": [
                    p.get("title") for p in final_state.get("policy_passages", [])
                ],
                "similar_cases_found": len(final_state.get("similar_cases", [])),
                "status": final_state.get("status")
            })

            # Pacing between LLM calls to respect Groq TPM
            await asyncio.sleep(8)

        except Exception as e:
            print(f" [FAILED: {e}]")
            summary_rows.append({
                "case_id": case_id,
                "txn_id": txn_id,
                "pattern_matched": "error",
                "risk_level": "error",
                "confidence": 0.0,
                "needs_more_evidence": True,
                "reasoning": str(e)
            })

    # Save full raw output
    cases_dir = project_root / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    out_file = cases_dir / "dry_run_uncertainty_assessment.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_for_saving, f, indent=2)

    print("\n" + "="*80)
    print(f"SAVED RAW OUTPUT FOR ALL 20 CASES TO: {out_file}")
    print("="*80)

    # Print summary table
    print("\n" + "="*145)
    print(f"{'Case ID':<9} | {'Txn ID':<8} | {'Pattern':<25} | {'Risk Level':<10} | {'Conf':<5} | {'Needs Ev':<8} | {'Reasoning Summary':<65}")
    print("-" * 145)
    for r in summary_rows:
        conf_str = f"{r['confidence']:.2f}"
        needs_str = "yes" if r['needs_more_evidence'] else "no"
        # truncate reasoning for table
        trunc_reasoning = (r['reasoning'][:62] + "...") if len(r['reasoning']) > 65 else r['reasoning']
        print(f"{r['case_id']:<9} | {r['txn_id']:<8} | {r['pattern_matched']:<25} | {r['risk_level']:<10} | {conf_str:<5} | {needs_str:<8} | {trunc_reasoning:<65}")
    print("="*145)

if __name__ == "__main__":
    asyncio.run(main())
