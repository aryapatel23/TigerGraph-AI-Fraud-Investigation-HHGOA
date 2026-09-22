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

    # Check the 20 benchmark cases and their INVOLVES_TXN edges
    query = """
    USE GRAPH FraudInvestigation
    INTERPRET QUERY () FOR GRAPH FraudInvestigation {
        TYPEDEF TUPLE<STRING case_id, STRING flagged_txn_id, STRING edge_txn_id, STRING edge_role> CASE_INFO;
        ListAccum<CASE_INFO> @@cases;

        start = {FraudCase.*};
        cases = SELECT s FROM start:s
                WHERE s.case_source == "benchmark";

        # Traverse INVOLVES_TXN edges
        edges = SELECT t FROM cases:s -(INVOLVES_TXN:e)-> Transaction:t
                ACCUM @@cases += CASE_INFO(s.case_id, s.flagged_txn_id, t.transaction_id, e.role);

        PRINT @@cases;
    }
    """
    res = conn.gsql(query)
    print(res)

if __name__ == "__main__":
    main()
