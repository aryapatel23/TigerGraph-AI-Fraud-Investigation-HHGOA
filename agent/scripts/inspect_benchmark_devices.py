import os
import csv
import json
from pathlib import Path
from dotenv import load_dotenv
import pyTigerGraph as tg

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(project_root / ".env")

    conn = tg.TigerGraphConnection(
        host=os.getenv("TG_HOST", "http://localhost"),
        graphname=os.getenv("TG_GRAPH_NAME", "FraudInvestigation"),
        username=os.getenv("TG_USERNAME", "tigergraph"),
        password=os.getenv("TG_PASSWORD", "tigergraph"),
        restppPort="14240",
        gsPort="14240"
    )

    case_pack_path = project_root / "data" / "HHGOA_IEEE" / "case_pack.csv"
    with open(case_pack_path, "r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

    print("Checking exact DeviceProfile details for all 20 benchmark cases:")
    for c in cases:
        case_id = c["case_id"]
        txn_id = c["flagged_txn_id"]
        edges = conn.getEdges("Transaction", txn_id)
        dev_edges = [e for e in edges if "DEVICE" in e.get("e_type", "")]
        dev_id = dev_edges[0]["to_id"] if dev_edges else None

        if dev_id:
            dp_vert = conn.getVerticesById("DeviceProfile", dev_id)
            attrs = dp_vert[0]["attributes"] if dp_vert else {}
            dev_info = attrs.get("device_info", "")
            os_val = attrs.get("os", "")
            browser = attrs.get("browser", "")
            screen = attrs.get("screen", "")
            is_placeholder = (dev_info == "" and os_val == "")
            print(f"[{case_id}] Txn {txn_id} | dev_info='{dev_info}' | os='{os_val}' | browser='{browser}' | screen='{screen}' | is_placeholder={is_placeholder}")
        else:
            print(f"[{case_id}] Txn {txn_id} | NO DEVICE PROFILE (in_person)")

if __name__ == "__main__":
    main()
