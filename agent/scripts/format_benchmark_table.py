import os
import json
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
        TYPEDEF TUPLE<STRING case_id, STRING flagged_txn_id, STRING edge_txn_id> BENCH_ROW;
        ListAccum<BENCH_ROW> @@rows;

        start = {FraudCase.*};
        cases = SELECT s FROM start:s
                WHERE s.case_source == "benchmark";

        edges = SELECT t FROM cases:s -(INVOLVES_TXN:e)-> Transaction:t
                ACCUM @@rows += BENCH_ROW(s.case_id, s.flagged_txn_id, t.transaction_id);

        PRINT @@rows;
    }
    """
    res = conn.gsql(query)
    data = json.loads(res[res.find('{'):])
    rows = data["results"][0]["@@rows"]
    rows = sorted(rows, key=lambda x: int(x["case_id"].split("-")[1]))

    print(f"| {'case_id':<10} | {'has_INVOLVES_TXN_edge':<23} | {'flagged_txn_id field value':<27} |")
    print("|" + "-"*12 + "|" + "-"*25 + "|" + "-"*29 + "|")
    for r in rows:
        has_edge = "yes" if r["edge_txn_id"] and r["edge_txn_id"] == r["flagged_txn_id"] else "no"
        print(f"| {r['case_id']:<10} | {has_edge:<23} | {r['flagged_txn_id']:<27} |")

if __name__ == "__main__":
    main()
