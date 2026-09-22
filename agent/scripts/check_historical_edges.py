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
        OrAccum @has_edge;
        SumAccum<INT> @@total_historical;
        SumAccum<INT> @@with_edge;
        SumAccum<INT> @@missing_edge;
        SumAccum<INT> @@empty_first_fraud;
        SumAccum<INT> @@non_empty_first_fraud_missing;

        start = {FraudCase.*};
        cases = SELECT s FROM start:s
                WHERE s.case_source == "historical"
                ACCUM @@total_historical += 1;

        edge_check = SELECT s FROM cases:s -(INVOLVES_TXN:e)-> Transaction:t
                     ACCUM s.@has_edge += true;

        count_check = SELECT s FROM cases:s
                      ACCUM
                          IF s.@has_edge THEN
                              @@with_edge += 1
                          ELSE
                              @@missing_edge += 1,
                              IF s.first_fraud_txn_id == "" THEN
                                  @@empty_first_fraud += 1
                              ELSE
                                  @@non_empty_first_fraud_missing += 1
                              END
                          END;

        PRINT @@total_historical, @@with_edge, @@missing_edge, @@empty_first_fraud, @@non_empty_first_fraud_missing;
    }
    """
    res = conn.gsql(query)
    print(res)

if __name__ == "__main__":
    main()
