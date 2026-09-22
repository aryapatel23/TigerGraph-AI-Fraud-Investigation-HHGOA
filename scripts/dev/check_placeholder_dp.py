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

res = conn.gsql("""
USE GRAPH FraudInvestigation
INTERPRET QUERY () FOR GRAPH FraudInvestigation {
    SumAccum<INT> @@empty_count;
    SumAccum<INT> @@null_count;
    SumAccum<INT> @@triple_pipe_count;
    SumAccum<INT> @@no_info_no_os_count;
    
    DP = {DeviceProfile.*};
    res = SELECT dp FROM DP:dp
          ACCUM 
            IF dp.device_profile_id == "" THEN @@empty_count += 1 END,
            IF dp.device_profile_id == "null" OR dp.device_profile_id == "NULL" THEN @@null_count += 1 END,
            IF dp.device_profile_id == "|||" THEN @@triple_pipe_count += 1 END,
            IF dp.device_info == "" AND dp.os == "" THEN @@no_info_no_os_count += 1 END;
            
    PRINT @@empty_count, @@null_count, @@triple_pipe_count, @@no_info_no_os_count;
}
""")
print(res)
