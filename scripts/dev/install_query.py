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

query_gsql = """
USE GRAPH FraudInvestigation

CREATE OR REPLACE QUERY detect_device_sharing(STRING txn_id, STRING device_profile_id) FOR GRAPH FraudInvestigation {
    TYPEDEF TUPLE<STRING txn_id, DATETIME ts, DOUBLE amt, STRING card_id, STRING customer_id, DOUBLE risk_score> SHARING_TXN;

    SetAccum<STRING> @@connected_cards;
    SetAccum<STRING> @@connected_customers;
    ListAccum<SHARING_TXN> @@sample_txns;
    OrAccum @@is_shared_device;
    SumAccum<INT> @@total_device_txns;

    DP = {DeviceProfile.*};
    target_dp = {};

    // 1. If device_profile_id is explicitly supplied, validate and ensure it is not empty/null/placeholder
    IF device_profile_id != "" 
       AND device_profile_id != "null" 
       AND device_profile_id != "NULL" 
       AND device_profile_id != "None" 
       AND device_profile_id != "|||" THEN
        target_dp = SELECT dp FROM DP:dp WHERE dp.device_profile_id == device_profile_id;
    END;

    // 2. If target_dp not found and txn_id is provided, find connected DeviceProfile excluding empty/null/placeholder
    IF target_dp.size() == 0 AND txn_id != "" THEN
        T = {Transaction.*};
        target_txn = SELECT t FROM T:t WHERE t.transaction_id == txn_id;
        target_dp = SELECT dp FROM target_txn:t -(FROM_DEVICE:e)-> DeviceProfile:dp
                    WHERE dp.device_profile_id != "" 
                      AND dp.device_profile_id != "null" 
                      AND dp.device_profile_id != "NULL" 
                      AND dp.device_profile_id != "None" 
                      AND dp.device_profile_id != "|||";
    END;

    // 3. Only calculate sharing if a valid DeviceProfile was resolved
    IF target_dp.size() > 0 THEN
        txns = SELECT t FROM target_dp:dp -(DEVICE_USED_IN:e)-> Transaction:t
               ACCUM @@total_device_txns += 1;

        cards = SELECT c FROM txns:t -(MADE_BY:e)-> Card:c
                ACCUM @@connected_cards += c.card_id;

        custs = SELECT cust FROM cards:c -(OWNED_BY:e)-> Customer:cust
                ACCUM @@connected_customers += cust.customer_id;

        sample_set = SELECT t FROM txns:t LIMIT 30;
        sample_acc = SELECT t FROM sample_set:t -(MADE_BY:e)-> Card:c
                     ACCUM @@sample_txns += SHARING_TXN(t.transaction_id, t.ts, t.transaction_amt, c.card_id, "", t.risk_score);

        IF @@connected_customers.size() > 1 OR @@connected_cards.size() > 1 THEN
            @@is_shared_device += true;
        END;
    END;

    PRINT target_dp, @@is_shared_device, @@connected_customers.size() AS sharing_customers_count,
          @@connected_cards.size() AS sharing_cards_count, @@total_device_txns,
          @@connected_customers, @@connected_cards, @@sample_txns;
}

INSTALL QUERY detect_device_sharing
"""

print("Compiling and installing detect_device_sharing...")
res = conn.gsql(query_gsql)
print(res)
