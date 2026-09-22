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

# Original counts recorded before the query update
original_counts = {
    "HHG-001": {"cust": 0, "card": 0, "dp": "NO_DEVICE"},
    "HHG-002": {"cust": 0, "card": 0, "dp": "NO_DEVICE"},
    "HHG-003": {"cust": 0, "card": 0, "dp": "NO_DEVICE"},
    "HHG-004": {"cust": 6, "card": 6, "dp": "||firefox 47.0|"},
    "HHG-005": {"cust": 112, "card": 112, "dp": "iOS Device|iOS 9.3.5|mobile safari 9.0|1024x768"},
    "HHG-006": {"cust": 543, "card": 543, "dp": "Trident/7.0|Windows 7|ie 11.0 for desktop|1920x1080"},
    "HHG-007": {"cust": 0, "card": 0, "dp": "NO_DEVICE"},
    "HHG-008": {"cust": 171, "card": 171, "dp": "||chrome 66.0|"},
    "HHG-009": {"cust": 0, "card": 0, "dp": "NO_DEVICE"},
    "HHG-010": {"cust": 208, "card": 208, "dp": "Windows|Windows 10|edge 16.0|1366x768"},
    "HHG-011": {"cust": 4, "card": 4, "dp": "SM-G610F Build/NRD90M||chrome 66.0 for android|"},
    "HHG-012": {"cust": 0, "card": 0, "dp": "NO_DEVICE"},
    "HHG-013": {"cust": 253, "card": 253, "dp": "Windows||chrome 66.0|"},
    "HHG-014": {"cust": 52, "card": 52, "dp": "SM-G935F Build/NRD90M|Android 7.0|chrome 62.0 for android|1920x1080"},
    "HHG-015": {"cust": 8, "card": 8, "dp": "Trident/7.0|Windows 8.1|ie 11.0 for desktop|1680x1050"},
    "HHG-016": {"cust": 158, "card": 158, "dp": "Windows||edge 16.0|"},
    "HHG-017": {"cust": 299, "card": 299, "dp": "Windows|Windows 10|chrome 65.0|1920x1080"},
    "HHG-018": {"cust": 0, "card": 0, "dp": "NO_DEVICE"},
    "HHG-019": {"cust": 5, "card": 5, "dp": "Windows|other|chrome 61.0|1280x720"},
    "HHG-020": {"cust": 253, "card": 253, "dp": "Trident/7.0|Windows 10|ie 11.0 for desktop|1920x1080"},
}

with open("cases/dry_run_uncertainty_assessment.json") as f:
    benchmarks = json.load(f)

results = []
print(f"{'Case ID':<8} | {'Txn ID':<8} | {'Orig Cust':<9} | {'New Cust':<9} | {'Orig Card':<9} | {'New Card':<9} | {'Changed?':<8} | {'Resolved DeviceProfile'}")
print("-" * 105)

for b in benchmarks:
    case_id = b["case_id"]
    txn_id = b["flagged_txn_id"]
    res = conn.runInstalledQuery("detect_device_sharing", {"txn_id": txn_id, "device_profile_id": ""})
    
    dp_data = res[0].get("target_dp", [])
    new_cust = res[0].get("sharing_customers_count", 0)
    new_card = res[0].get("sharing_cards_count", 0)
    dp_v_id = dp_data[0]["v_id"] if dp_data else "NO_DEVICE"
    
    orig = original_counts[case_id]
    orig_cust = orig["cust"]
    orig_card = orig["card"]
    
    changed = "YES" if (orig_cust != new_cust or orig_card != new_card) else "NO"
    print(f"{case_id:<8} | {txn_id:<8} | {orig_cust:<9} | {new_cust:<9} | {orig_card:<9} | {new_card:<9} | {changed:<8} | {dp_v_id}")
    
    results.append({
        "case_id": case_id,
        "txn_id": txn_id,
        "orig_cust": orig_cust,
        "new_cust": new_cust,
        "orig_card": orig_card,
        "new_card": new_card,
        "changed": changed,
        "dp_v_id": dp_v_id
    })

with open("agent/scripts/comparison_results.json", "w") as f:
    json.dump(results, f, indent=2)
