import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import pyTigerGraph as tg

FRAUD_PATTERNS = [
    {
        "pattern_code": "card_testing",
        "description": "Rapid sequence of low-value transactions followed by high-value attempt",
        "policy_rules": "R5"
    },
    {
        "pattern_code": "card_not_present_fraud",
        "description": "High-value online transaction with mismatched billing region",
        "policy_rules": "R1"
    },
    {
        "pattern_code": "card_not_present_new_device",
        "description": "Online purchase on previously unseen device with anonymous proxy",
        "policy_rules": "R2,R4"
    },
    {
        "pattern_code": "out_of_region_use",
        "description": "Transaction from billing region different from cardholder home region",
        "policy_rules": "R1"
    },
    {
        "pattern_code": "account_takeover",
        "description": "Multiple identity changes followed by rapid high-risk transactions",
        "policy_rules": "R3"
    },
    {
        "pattern_code": "undocumented",
        "description": "Uncategorized historical fraud pattern",
        "policy_rules": "R1,R2,R3,R4,R5"
    },
    {
        "pattern_code": "none",
        "description": "Cleared or legitimate non-fraud activity",
        "policy_rules": ""
    }
]

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)

    host = os.getenv("TG_HOST", "http://localhost")
    port = os.getenv("TG_PORT", "14240")
    username = os.getenv("TG_USERNAME", "tigergraph")
    password = os.getenv("TG_PASSWORD", "tigergraph")
    graph_name = os.getenv("TG_GRAPH_NAME", "FraudInvestigation")

    print("==================================================")
    print("      TigerGraph Data Ingestion & Count Verification")
    print("==================================================")
    print(f"Target: {host}:{port}")
    print(f"User:   {username}")
    print(f"Graph:  {graph_name}")

    conn = tg.TigerGraphConnection(
        host=host,
        restppPort=port,
        username=username,
        password=password,
        graphname=graph_name
    )

    # 1. Seed FraudPattern vertices
    print("\n[Step 1/4] Seeding reference FraudPattern vertices (7 patterns)...")
    for pattern in FRAUD_PATTERNS:
        code = pattern["pattern_code"]
        attrs = {
            "description": pattern["description"],
            "policy_rules": pattern["policy_rules"]
        }
        conn.upsertVertex("FraudPattern", code, attributes=attrs)
    print("  -> Seeded 7 FraudPattern vertices successfully.")

    # 2. Check/Apply loading jobs
    print("\n[Step 2/4] Ensuring loading jobs are compiled in graph...")
    jobs_file = project_root / "gsql" / "loading_jobs.gsql"
    with open(jobs_file, "r", encoding="utf-8") as f:
        jobs_gsql = f.read()
    
    # Check if jobs already exist in graph catalog
    graph_ls = conn.gsql(f"USE GRAPH {graph_name}\nls")
    if "load_transactions_job" not in graph_ls:
        print("  Compiling loading jobs from gsql/loading_jobs.gsql...")
        compile_res = conn.gsql(jobs_gsql)
        print(compile_res)
    else:
        print("  Loading jobs already compiled and present in catalog.")

    # 3. Execute loading jobs in dependency order
    print("\n[Step 3/4] Running loading jobs...")
    jobs_to_run = [
        ("load_transactions_job", "Transactions & Base Entities (transactions.csv)"),
        ("load_identity_job", "Identity Records & Device Profiles (identity.csv)"),
        ("load_cases_job", "Historical & Benchmark Cases (closed_cases_history.csv + case_pack.csv)")
    ]

    for job_name, job_desc in jobs_to_run:
        print(f"\n>>> Running: {job_name} ({job_desc})")
        t0 = time.time()
        run_gsql = f"USE GRAPH {graph_name}\nRUN LOADING JOB {job_name}"
        res = conn.gsql(run_gsql)
        elapsed = time.time() - t0
        print(f"--- Output for {job_name} ({elapsed:.1f}s) ---")
        sys.stdout.buffer.write((res + "\n").encode("utf-8", errors="replace"))

        # Check for errors / capacity limits
        lower_res = res.lower()
        if "error" in lower_res or "fail" in lower_res or "limit" in lower_res or "capacity" in lower_res:
            if "not found" in lower_res or "exception" in lower_res:
                print(f"[!] Warning/Error detected in {job_name}:")
                sys.exit(1)

    # 4. STEP 4 — Count Verification
    print("\n[Step 4/4] Querying catalog counts to verify loaded graph data...")
    time.sleep(2) # Give GPE a moment to sync counts

    v_counts = conn.getVertexCount("*")
    e_counts = conn.getEdgeCount("*")

    print("\n" + "="*65)
    print("                VERTEX COUNTS VERIFICATION")
    print("="*65)
    print(f"{'Vertex Type':<20} | {'Loaded Count':>15} | {'Notes / Expected':<25}")
    print("-" * 65)

    for v_type, cnt in sorted(v_counts.items()):
        notes = ""
        if v_type == "Transaction":
            notes = "Expected: 590,742"
        elif v_type == "IdentityRecord":
            notes = "Expected: 144,432"
        elif v_type == "FraudCase":
            notes = "Expected: 5,585 (5,565 + 20)"
        elif v_type == "FraudPattern":
            notes = "Expected: 7"
        elif v_type in ("Customer", "Card", "DeviceProfile", "BillingRegion", "EmailDomain"):
            notes = "Deduplicated entities"
        elif v_type in ("Evidence", "Decision"):
            notes = "0 (Populated by agent)"
        print(f"{v_type:<20} | {cnt:>15,d} | {notes:<25}")

    print("\n" + "="*65)
    print("                EDGE COUNTS VERIFICATION")
    print("="*65)
    print(f"{'Edge Type':<25} | {'Loaded Count':>15} | {'Notes':<20}")
    print("-" * 65)

    for e_type, cnt in sorted(e_counts.items()):
        print(f"{e_type:<25} | {cnt:>15,d} |")

    print("\n" + "="*65)
    print("CONFIRMATION SUMMARY:")
    print(f"  Total Transactions:   {v_counts.get('Transaction', 0):,d} / 590,742")
    print(f"  Total Identity:       {v_counts.get('IdentityRecord', 0):,d} / 144,432")
    print(f"  Total FraudCases:     {v_counts.get('FraudCase', 0):,d} / 5,585 (5,565 historical + 20 benchmark)")
    print(f"  Total Customers:      {v_counts.get('Customer', 0):,d}")
    print(f"  Total Cards:          {v_counts.get('Card', 0):,d}")
    print(f"  Total DeviceProfiles: {v_counts.get('DeviceProfile', 0):,d}")
    print("==================================================")

if __name__ == "__main__":
    main()
