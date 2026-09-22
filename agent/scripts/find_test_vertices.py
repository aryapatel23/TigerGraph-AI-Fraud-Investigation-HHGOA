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
        SetAccum<STRING> @@test_txns;
        SetAccum<STRING> @@test_cases;
        
        start_t = {Transaction.*};
        res_t = SELECT s FROM start_t:s
                WHERE s.product_cd == "" OR s.product_cd == "test" OR length(s.transaction_id) < 6 OR s.transaction_id LIKE "test%" OR s.transaction_id LIKE "TX%" OR s.transaction_id LIKE "%test%"
                ACCUM @@test_txns += s.transaction_id;
                
        start_c = {FraudCase.*};
        res_c = SELECT s FROM start_c:s
                WHERE s.case_source == "test" OR s.case_id LIKE "%TEST%" OR s.case_id LIKE "%test%"
                ACCUM @@test_cases += s.case_id;

        PRINT @@test_txns, @@test_cases;
    }
    """
    print("Running interpret query...")
    res = conn.gsql(query)
    print(res)

if __name__ == "__main__":
    main()
