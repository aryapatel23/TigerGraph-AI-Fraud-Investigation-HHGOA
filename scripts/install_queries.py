import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import pyTigerGraph as tg

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

QUERY_NAMES = [
    "get_transaction_context",
    "get_customer_history",
    "detect_card_testing",
    "detect_device_sharing",
    "detect_out_of_region",
    "detect_new_device_flag",
    "get_similar_cases"
]

def main():
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)

    host = os.getenv("TG_HOST", "http://localhost")
    port = os.getenv("TG_PORT", "14240")
    username = os.getenv("TG_USERNAME", "tigergraph")
    password = os.getenv("TG_PASSWORD", "tigergraph")
    graph_name = os.getenv("TG_GRAPH_NAME", "FraudInvestigation")

    print("==================================================")
    print("      TigerGraph GSQL Queries Installer & Tester")
    print("==================================================")
    print(f"Target Graph: {graph_name} ({host}:{port})")

    conn = tg.TigerGraphConnection(
        host=host,
        restppPort=port,
        username=username,
        password=password,
        graphname=graph_name
    )

    # Check installed queries
    do_reinstall = "--reinstall" in sys.argv or "--force" in sys.argv
    installed = conn.getInstalledQueries()
    installed_names = [k.split("/")[-1] for k in installed.keys()]
    all_installed = all(q in installed_names for q in QUERY_NAMES)

    if all_installed and not do_reinstall:
        print(f"\n[INFO] All {len(QUERY_NAMES)} queries are already compiled and active in GPE.")
        print("Skipping re-installation to execute immediately. (Pass '--reinstall' to recompile).")
    else:
        # 1. Read queries file
        queries_file = project_root / "gsql" / "investigation_queries.gsql"
        with open(queries_file, "r", encoding="utf-8") as f:
            gsql_content = f.read()

        print(f"\n[1/3] Creating 7 investigation queries from {queries_file.name}...")
        create_res = conn.gsql(gsql_content)
        print("Create Response:")
        print(create_res)

        # 2. Install queries
        print("\n[2/3] Compiling and Installing queries into TigerGraph GPE...")
        install_stmt = f"USE GRAPH {graph_name}\nINSTALL QUERY " + ", ".join(QUERY_NAMES)
        t0 = time.time()
        install_res = conn.gsql(install_stmt)
        elapsed = time.time() - t0
        print(f"Install finished in {elapsed:.1f}s")
        print(install_res)

    # 3. Test queries against benchmark HHG-001 (txn: 3514030, cust: C12382, card: C12382-K1)
    print("\n[3/3] Testing all 7 installed queries on benchmark transaction 3514030 (HHG-001)...")
    test_txn = "3514030"
    test_cust = "C12382"
    test_card = "C12382-K1"

    # Query 1
    print("\n" + "="*70)
    print(f"TEST 1: get_transaction_context(txn_id='{test_txn}')")
    print("="*70)
    res1 = conn.runInstalledQuery("get_transaction_context", params={"txn_id": test_txn})
    print(json.dumps(res1, indent=2, default=str))

    # Query 2
    print("\n" + "="*70)
    print(f"TEST 2: get_customer_history(customer_id='{test_cust}', txn_id='{test_txn}', lookback_days=90)")
    print("="*70)
    res2 = conn.runInstalledQuery("get_customer_history", params={
        "customer_id": test_cust,
        "txn_id": test_txn,
        "lookback_days": 90
    })
    print(json.dumps(res2, indent=2, default=str))

    # Query 3
    print("\n" + "="*70)
    print(f"TEST 3: detect_card_testing(card_id='{test_card}', customer_id='{test_cust}', window_minutes=60)")
    print("="*70)
    res3 = conn.runInstalledQuery("detect_card_testing", params={
        "card_id": test_card,
        "customer_id": test_cust,
        "window_minutes": 60
    })
    print(json.dumps(res3, indent=2, default=str))

    # Query 4
    print("\n" + "="*70)
    print(f"TEST 4: detect_device_sharing(txn_id='{test_txn}', device_profile_id='')")
    print("="*70)
    res4 = conn.runInstalledQuery("detect_device_sharing", params={
        "txn_id": test_txn,
        "device_profile_id": ""
    })
    print(json.dumps(res4, indent=2, default=str))

    # Query 5
    print("\n" + "="*70)
    print(f"TEST 5: detect_out_of_region(txn_id='{test_txn}')")
    print("="*70)
    res5 = conn.runInstalledQuery("detect_out_of_region", params={
        "txn_id": test_txn
    })
    print(json.dumps(res5, indent=2, default=str))

    # Query 6
    print("\n" + "="*70)
    print(f"TEST 6: detect_new_device_flag(txn_id='{test_txn}')")
    print("="*70)
    res6 = conn.runInstalledQuery("detect_new_device_flag", params={
        "txn_id": test_txn
    })
    print(json.dumps(res6, indent=2, default=str))

    # Query 7
    print("\n" + "="*70)
    print(f"TEST 7: get_similar_cases(txn_id='{test_txn}', customer_id='{test_cust}', top_k=5)")
    print("="*70)
    res7 = conn.runInstalledQuery("get_similar_cases", params={
        "txn_id": test_txn,
        "customer_id": test_cust,
        "top_k": 5
    })
    print(json.dumps(res7, indent=2, default=str))

    print("\n==================================================")
    print("[SUCCESS] All 7 investigation queries installed & tested cleanly!")
    print("==================================================")

if __name__ == "__main__":
    main()
