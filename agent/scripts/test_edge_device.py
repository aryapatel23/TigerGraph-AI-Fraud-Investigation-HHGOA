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

res = conn.runInstalledQuery("detect_device_sharing", {"txn_id": "", "device_profile_id": ""})
print("Empty inputs detect_device_sharing:", res)

res_null = conn.runInstalledQuery("detect_device_sharing", {"txn_id": "", "device_profile_id": "null"})
print("Null string detect_device_sharing:", res_null)

res_bars = conn.runInstalledQuery("detect_device_sharing", {"txn_id": "", "device_profile_id": "|||"})
print("Bars detect_device_sharing:", res_bars)
