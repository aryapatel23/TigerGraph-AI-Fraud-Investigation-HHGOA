import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")
sys.stdout.reconfigure(encoding="utf-8")

from agent.investigation_agent import (
    gather_evidence_node,
    ground_policy_node,
    recommend_action_node,
    check_sar_requirement_node,
    generate_explanation_node,
    write_to_case_node
)

async def run_single_case(target_case_id="HHG-006"):
    # Load previously assessed case from dry_run_uncertainty_assessment.json
    dry_run_path = project_root / "cases" / "dry_run_uncertainty_assessment.json"
    with open(dry_run_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    target = None
    for c in cases:
        if c["case_id"] == target_case_id:
            target = c
            break

    if not target:
        print(f"Case {target_case_id} not found in dry run!")
        return

    print(f"Loaded {target_case_id} from dry run assessment.")
    txn_id = target["flagged_txn_id"]

    # Initialize state
    state = {
        "case_id": target_case_id,
        "txn_id": txn_id,
        "trigger_type": target["trigger_type"],
        "trigger_text": target["trigger_text"],
        "trigger_risk_score": target["trigger_risk_score"],
        "risk_assessment": target["risk_assessment"],
        "needs_more_evidence": target["needs_more_evidence"],
        "evidence_requests": target["evidence_requests"],
        "transaction_context": None,
        "customer_history": None,
        "pattern_signals": None,
        "similar_cases": None,
        "policy_passages": None,
        "recommended_actions": None,
        "approval_route": None,
        "sar_required": False,
        "sar_content": None,
        "final_explanation": None,
        "written_to_graph": False,
        "full_answer_package": None,
        "raw_prompt": None,
        "raw_response": None,
        "status": "assessed",
        "error": None
    }

    # 1. Gather evidence & ground policy to have full context
    print("Gathering graph context and policy passages...")
    ev_state = await gather_evidence_node(state)
    state.update(ev_state)
    pol_state = await ground_policy_node(state)
    state.update(pol_state)

    # 2. Recommend action
    print("Running recommend_action node...")
    act_state = await recommend_action_node(state)
    state.update(act_state)

    # 3. Check SAR requirement
    print("Running check_sar_requirement node...")
    sar_state = await check_sar_requirement_node(state)
    state.update(sar_state)

    # 4. Generate explanation
    print("Running generate_explanation node...")
    exp_state = await generate_explanation_node(state)
    state.update(exp_state)

    # 5. Write to case
    print("Running write_to_case node (updating TigerGraph and assembling answer package)...")
    write_state = await write_to_case_node(state)
    state.update(write_state)

    answer_pkg = state.get("full_answer_package", {})

    # Save to cases/HHG-006_answer.json
    out_file = project_root / "cases" / f"{target_case_id}_answer.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(answer_pkg, f, indent=2)

    print(f"\nSaved answer file to: {out_file}")
    print("\n================================================================================")
    print(f"FULL GENERATED ANSWER FILE FOR {target_case_id}:")
    print("================================================================================")
    print(json.dumps(answer_pkg, indent=2))

if __name__ == "__main__":
    case_arg = sys.argv[1] if len(sys.argv) > 1 else "HHG-011"
    asyncio.run(run_single_case(case_arg))
