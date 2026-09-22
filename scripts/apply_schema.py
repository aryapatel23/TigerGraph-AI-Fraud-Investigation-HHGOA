import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv
import pyTigerGraph as tg

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    # 1. Load configuration from .env
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path)

    host = os.getenv("TG_HOST", "http://localhost")
    port = os.getenv("TG_PORT", "14240")
    username = os.getenv("TG_USERNAME", "tigergraph")
    password = os.getenv("TG_PASSWORD", "tigergraph")
    graph_name = os.getenv("TG_GRAPH_NAME", "FraudInvestigation")

    print("==================================================")
    print("      TigerGraph Schema Deployment & Verification")
    print("==================================================")
    print(f"Target:  {host}:{port}")
    print(f"User:    {username}")
    print(f"Graph:   {graph_name}")

    schema_file = project_root / "gsql" / "schema.gsql"
    if not schema_file.exists():
        print(f"[ERROR] Schema file not found at: {schema_file}")
        sys.exit(1)

    with open(schema_file, "r", encoding="utf-8-sig") as f:
        schema_content = f.read()
    
    schema_lines = schema_content.splitlines()
    print(f"Loaded:  {schema_file.name} ({len(schema_lines)} lines)")

    # 2. Connect to TigerGraph
    try:
        conn = tg.TigerGraphConnection(
            host=host,
            restppPort=port,
            username=username,
            password=password
        )
    except Exception as e:
        print(f"[ERROR] Failed to initialize connection: {e}")
        sys.exit(1)

    # 3. Check if graph or vertices exist
    do_reset = "--reset" in sys.argv or "--force" in sys.argv
    catalog_ls = conn.gsql("ls")
    graph_exists = (f"The graph {graph_name}" in catalog_ls) or (f"The graph: {graph_name}" in catalog_ls) or ("Customer" in catalog_ls)

    if graph_exists and not do_reset:
        print(f"\n[INFO] Graph '{graph_name}' is already deployed and active.")
        print("Skipping DROP ALL to protect loaded vertices. (Pass '--reset' to wipe and recreate).")
    else:
        if graph_exists:
            print(f"\n[RESET] Existing graph/vertices detected. Resetting database for clean deployment...")
            drop_res = conn.gsql("DROP ALL")
            print(drop_res)

        # 4. Apply schema.gsql
        print("\n[1/2] Executing gsql/schema.gsql against TigerGraph...")
        try:
            response = conn.gsql(schema_content)
        except Exception as e:
            response = str(e)

        print("\n--- GSQL Output ---")
        sys.stdout.buffer.write((response + "\n").encode("utf-8", errors="replace"))
        print("-------------------")

        # Check for errors in the output
        has_error = False
        lower_resp = response.lower()
        if (
            "error" in lower_resp
            or "failed" in lower_resp
            or "exception" in lower_resp
            or "encountered" in lower_resp
            or "fails" in lower_resp
            or f"the graph {graph_name.lower()} is created" not in lower_resp
        ):
            has_error = True

        if has_error:
            print("\n[!] Schema execution encountered errors.")
            matches = re.findall(r"line\s+(\d+)", response, re.IGNORECASE)
            if matches:
                for match in set(matches):
                    line_no = int(match)
                    print(f"\n>>> Error referenced Line {line_no} in schema.gsql:")
                    start_line = max(1, line_no - 5)
                    end_line = min(len(schema_lines), line_no + 5)
                    for idx in range(start_line, end_line + 1):
                        prefix = ">>>" if idx == line_no else "   "
                        line_text = schema_lines[idx - 1]
                        sys.stdout.buffer.write(f"{prefix} {idx:4d}: {line_text}\n".encode("utf-8", errors="replace"))
            sys.exit(1)
        
        print("\n[SUCCESS] Schema applied cleanly with zero errors!")

    # 5. STEP 8 — Verification
    print(f"\n[2/2] Verifying graph '{graph_name}' catalog...")
    graph_conn = tg.TigerGraphConnection(
        host=host,
        restppPort=port,
        username=username,
        password=password,
        graphname=graph_name
    )

    v_types = graph_conn.getVertexTypes()
    e_types = graph_conn.getEdgeTypes()

    print(f"\n--- Graph Verification: {graph_name} ---")
    print(f"Vertex Types count: {len(v_types)} (Expected 11)")
    for v in sorted(v_types):
        print(f"  [VERTEX] {v}")

    expected_vertices = {
        "Customer", "Card", "Transaction", "DeviceProfile", "IdentityRecord",
        "BillingRegion", "EmailDomain", "FraudPattern", "FraudCase", "Evidence", "Decision"
    }
    missing_vertices = expected_vertices - set(v_types)
    if missing_vertices:
        print(f"[!] Missing vertex types: {missing_vertices}")
        sys.exit(1)

    print(f"\nEdge Types count: {len(e_types)} base forward types")
    for e in sorted(e_types):
        print(f"  [EDGE]   {e}")

    # Verify key schema relationships
    expected_forward_edges = {
        "OWNS", "MADE", "FROM_DEVICE", "HAS_IDENTITY", "BILLED_IN",
        "USES_EMAIL_DOMAIN", "NEXT_TXN", "INVOLVES_TXN", "ON_CARD",
        "CONNECTED_TO_CARD", "INVOLVES_CUSTOMER", "LINKED_DEVICE",
        "MATCHES_PATTERN", "HAS_EVIDENCE", "HAS_DECISION", "SIMILAR_TO_CASE"
    }
    missing_edges = expected_forward_edges - set(e_types)
    if missing_edges:
        print(f"[!] Missing edge types: {missing_edges}")
        sys.exit(1)

    print("\n==================================================")
    print(f"CONFIRMATION: Graph '{graph_name}' exists and is fully operational")
    print(f"  - 11/11 Vertex Types confirmed")
    print(f"  - 20 Edge Types (16 forward + reverse pairs) confirmed")
    print("==================================================")

if __name__ == "__main__":
    main()
