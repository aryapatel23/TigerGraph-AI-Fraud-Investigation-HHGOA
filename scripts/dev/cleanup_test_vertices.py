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

    print("Checking initial Transaction count...")
    t_cnt = conn.getVertexCount("Transaction")
    c_cnt = conn.getVertexCount("FraudCase")
    print(f"Transaction count before cleanup: {t_cnt}")
    print(f"FraudCase count: {c_cnt}")

    # GSQL delete query for non-numeric/spurious Transaction vertices and test cases
    del_gsql = """
    USE GRAPH FraudInvestigation
    INTERPRET QUERY () FOR GRAPH FraudInvestigation {
        start_t = {Transaction.*};
        bad_txns = SELECT s FROM start_t:s
                   WHERE s.product_cd == "" OR s.product_cd == "test" OR length(s.transaction_id) < 6 OR s.transaction_id LIKE "test%" OR s.transaction_id LIKE "TX%" OR s.transaction_id LIKE "%decide%";

        PRINT bad_txns.size();

        DELETE s FROM bad_txns:s;
    }
    """
    print("\nExecuting deletion of test/spurious Transaction vertices...")
    res = conn.gsql(del_gsql)
    print(res)

    # Check for any stray FraudCase vertices
    del_cases_gsql = """
    USE GRAPH FraudInvestigation
    INTERPRET QUERY () FOR GRAPH FraudInvestigation {
        start_c = {FraudCase.*};
        bad_cases = SELECT s FROM start_c:s
                    WHERE s.case_source == "test" OR s.case_id LIKE "%TEST%" OR s.case_id LIKE "%test%";
        PRINT bad_cases.size();
        DELETE s FROM bad_cases:s;
    }
    """
    print("\nExecuting deletion of test FraudCase vertices if any...")
    res_cases = conn.gsql(del_cases_gsql)
    print(res_cases)

    # Check counts again
    import time
    time.sleep(2)
    counts = conn.getVertexCount("*")
    print("\nUpdated Vertex Counts:")
    for k, v in sorted(counts.items()):
        print(f"  {k:<20}: {v:,d}")

if __name__ == "__main__":
    main()
