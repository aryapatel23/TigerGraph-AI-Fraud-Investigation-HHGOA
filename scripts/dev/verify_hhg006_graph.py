import os
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

v = conn.getVerticesById("FraudCase", "HHG-006")[0]["attributes"]
print("FraudCase HHG-006 in Graph:")
for k in ["case_id", "agent_verdict", "agent_fraud_probability", "case_status", "pattern_code", "exposure_usd", "written_to_graph", "agent_stop_reason"]:
    print(f"  {k}: {v.get(k)}")

edges = conn.getEdges("FraudCase", "HHG-006")
print("\nEdges connected to FraudCase HHG-006:")
for e in edges:
    print(f"  {e.get('e_type')} -> {e.get('to_type')}: {e.get('to_id')}")
