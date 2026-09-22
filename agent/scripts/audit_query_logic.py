import os
import pyTigerGraph as tg
from dotenv import load_dotenv

def main():
    load_dotenv()
    conn = tg.TigerGraphConnection(
        host=os.getenv("TG_HOST", "http://localhost"),
        graphname=os.getenv("TG_GRAPH_NAME", "FraudInvestigation"),
        username=os.getenv("TG_USERNAME", "tigergraph"),
        password=os.getenv("TG_PASSWORD", "tigergraph"),
        restppPort="14240",
        gsPort="14240"
    )

    query = """
    USE GRAPH FraudInvestigation
    INTERPRET QUERY () FOR GRAPH FraudInvestigation {
        DP = {DeviceProfile.*};
        empty_dp = SELECT dp FROM DP:dp
                   WHERE dp.device_profile_id == "" OR dp.device_profile_id == "|||" OR dp.device_profile_id == "null";
        PRINT empty_dp.size();

        # Check top generic or partial fingerprints
        partial_dp = SELECT dp FROM DP:dp
                     WHERE dp.device_profile_id LIKE "%||%";
        PRINT partial_dp.size();
    }
    """
    res = conn.gsql(query)
    print(res)

if __name__ == "__main__":
    main()
