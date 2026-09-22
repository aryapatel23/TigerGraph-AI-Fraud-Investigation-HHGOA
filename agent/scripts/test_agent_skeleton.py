import os
import sys
import json
import asyncio
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from agent.investigation_agent import build_investigation_graph

async def main():
    print("==================================================")
    print("   LangGraph -> TigerGraph MCP Agent Plumbing Test")
    print("==================================================")

    test_txn = "3514030"
    print(f"Target Benchmark Transaction: {test_txn} (HHG-001)")
    print("Initializing LangGraph workflow...")

    app = build_investigation_graph()

    print("\nExecuting graph workflow: trigger node -> MCP run_installed_query...")
    initial_state = {
        "txn_id": test_txn,
        "transaction_context": None,
        "raw_mcp_output": None,
        "status": "init",
        "error": None
    }

    final_state = await app.ainvoke(initial_state)

    print("\nWorkflow Execution Status:", final_state.get("status"))
    if final_state.get("error"):
        print("[ERROR]:", final_state.get("error"))
        sys.exit(1)

    print("\n" + "="*70)
    print("RAW PARSED TRANSACTION CONTEXT FROM LANGGRAPH STATE:")
    print("="*70)
    context = final_state.get("transaction_context")
    print(json.dumps(context, indent=2, default=str))

    # Validation against Test 1 baseline
    print("\n" + "="*70)
    print("VALIDATION AGAINST TEST 1 BASELINE:")
    print("="*70)

    if context and len(context) > 0:
        ctx0 = context[0]
        txns = ctx0.get("target_txn", [])
        cards = ctx0.get("cards", [])
        custs = ctx0.get("custs", [])
        regions = ctx0.get("regions", [])

        txn_match = len(txns) == 1 and txns[0].get("v_id") == "3514030"
        card_match = len(cards) == 1 and cards[0].get("v_id") == "C12382-K1"
        cust_match = len(custs) == 1 and custs[0].get("v_id") == "C12382"
        reg_match = len(regions) == 1 and regions[0].get("v_id") == "444.0"

        print(f"  [+] Transaction 3514030 resolved: {txn_match}")
        print(f"  [+] Card C12382-K1 resolved:       {card_match}")
        print(f"  [+] Customer C12382 resolved:      {cust_match}")
        print(f"  [+] BillingRegion 444.0 resolved:  {reg_match}")

        if txn_match and card_match and cust_match and reg_match:
            print("\n[SUCCESS] LangGraph -> MCP -> TigerGraph end-to-end plumbing verified!")
        else:
            print("\n[!] Discrepancy detected in resolved entities.")
            sys.exit(1)
    else:
        print("[!] Empty transaction context returned.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
