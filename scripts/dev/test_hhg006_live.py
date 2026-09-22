import asyncio
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agent.investigation_agent import build_investigation_graph

async def main():
    print("================================================================================")
    print("STEP 1: LIVE TEST OF HHG-006 (Txn: 3476682) VIA GROQ (openai/gpt-oss-120b)")
    print("================================================================================")
    
    app = build_investigation_graph()
    
    initial_state = {
        "txn_id": "3476682",
        "case_id": "HHG-006",
        "trigger_type": "risk_score",
        "trigger_text": "Real-time model scored transaction 3476682 ($117.0, in billing region 315.0) at 0.72. Review and decide.",
        "trigger_risk_score": 0.72,
        "transaction_context": None,
        "customer_history": None,
        "pattern_signals": None,
        "similar_cases": None,
        "policy_passages": None,
        "risk_assessment": None,
        "needs_more_evidence": False,
        "evidence_requests": [],
        "raw_prompt": None,
        "raw_response": None,
        "status": "init",
        "error": None
    }

    result = await app.ainvoke(initial_state)

    print("\n------------------------- RAW API REQUEST PROMPT -------------------------")
    print(result.get("raw_prompt", "NO RAW PROMPT RECORDED"))

    print("\n------------------------- RAW API RESPONSE FROM GROQ -------------------------")
    print(result.get("raw_response", "NO RAW RESPONSE RECORDED"))

    print("\n------------------------- PARSED RISK ASSESSMENT -------------------------")
    print(json.dumps(result.get("risk_assessment"), indent=2))
    print("Status:", result.get("status"))
    print("Needs more evidence:", result.get("needs_more_evidence"))
    print("Evidence requests:", result.get("evidence_requests"))
    if "error" in result and result["error"]:
        print("ERROR:", result["error"])

if __name__ == "__main__":
    asyncio.run(main())
