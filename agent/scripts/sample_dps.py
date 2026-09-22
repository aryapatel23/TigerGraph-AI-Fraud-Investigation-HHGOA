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

# Sample some DeviceProfiles
dps = conn.getVertices("DeviceProfile", limit=50)
print(f"Sampled {len(dps)} DeviceProfiles:")
for dp in dps[:10]:
    print(dp)
