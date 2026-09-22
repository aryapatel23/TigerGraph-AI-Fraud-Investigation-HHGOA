import os
import json
import pyTigerGraph as tg
from dotenv import load_dotenv

load_dotenv()

conn = tg.TigerGraphConnection(
    host=os.getenv("TG_HOST", "http://localhost"),
    restppPort=int(os.getenv("TG_PORT", "14240")),
    username=os.getenv("TG_USERNAME", "tigergraph"),
    password=os.getenv("TG_PASSWORD", "tigergraph"),
    graphname=os.getenv("TG_GRAPH_NAME", "FraudInvestigation"),
)

with open("cases/dry_run_uncertainty_assessment.json") as f:
    benchmarks = json.load(f)

print("--- AUDITING 20 BENCHMARK TRANSACTIONS ---")
for b in benchmarks:
    case_id = b["case_id"]
    txn_id = b["flagged_txn_id"]
    res = conn.runInstalledQuery("detect_device_sharing", {"txn_id": txn_id, "device_profile_id": ""})
    
    # Extract target_dp and counts
    dp_data = res[0].get("target_dp", [])
    is_shared = res[0].get("@@is_shared_device", False)
    cust_count = res[0].get("sharing_customers_count", 0)
    card_count = res[0].get("sharing_cards_count", 0)
    total_txns = res[0].get("@@total_device_txns", 0)
    
    dp_v_id = dp_data[0]["v_id"] if dp_data else "NO_DEVICE"
    dp_attrs = dp_data[0]["attributes"] if dp_data else {}
    
    print(f"{case_id} (Txn {txn_id}):")
    print(f"  DP Vertex ID: '{dp_v_id}'")
    print(f"  DP Attrs: info='{dp_attrs.get('device_info', '')}', os='{dp_attrs.get('os', '')}', browser='{dp_attrs.get('browser', '')}', res='{dp_attrs.get('screen_resolution', '')}'")
    print(f"  Shared: {is_shared}, CustCount: {cust_count}, CardCount: {card_count}, TotalTxns: {total_txns}")
