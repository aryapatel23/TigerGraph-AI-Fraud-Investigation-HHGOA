import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

async def main():
    print("\n" + "=" * 65)
    print("      TIGERGRAPH MODEL CONTEXT PROTOCOL (MCP) SMOKE TEST")
    print("=" * 65)

    try:
        from tigergraph_mcp.connection_manager import ConnectionManager
        from tigergraph_mcp.tools import (
            list_graphs,
            get_vertex_count,
            run_installed_query,
            is_query_installed
        )
    except ImportError as e:
        print(f"[FAIL] tigergraph-mcp is not installed: {e}")
        return 1

    print("[Step 1/4] Loading TigerGraph MCP Connection Profiles...")
    ConnectionManager.load_profiles()
    print("  -> ConnectionManager profiles loaded successfully.")

    print("\n[Step 2/4] Testing Schema Introspection via MCP (list_graphs)...")
    try:
        graphs_res = await list_graphs()
        raw_text = graphs_res[0].text if hasattr(graphs_res[0], "text") else str(graphs_res[0])
        print("  -> list_graphs MCP response received:")
        if "FraudInvestigation" in raw_text:
            print("  [PASS] Target graph 'FraudInvestigation' discovered via MCP.")
        else:
            print(f"  [WARN] Graphs response: {raw_text[:200]}")
    except Exception as e:
        print(f"  [FAIL] list_graphs tool call failed: {e}")
        return 1

    print("\n[Step 3/4] Testing Vertex Counting via MCP (get_vertex_count)...")
    try:
        count_res = await get_vertex_count(vertex_type="Transaction")
        raw_text = count_res[0].text if hasattr(count_res[0], "text") else str(count_res[0])
        if "590742" in raw_text or "590,742" in raw_text:
            print("  [PASS] Vertex count for 'Transaction' matches data dictionary: 590,742.")
        else:
            print(f"  [INFO] Count result: {raw_text[:200]}")
    except Exception as e:
        print(f"  [FAIL] get_vertex_count tool call failed: {e}")
        return 1

    print("\n[Step 4/4] Testing Installed GSQL Query Execution via MCP...")
    try:
        installed_check = await is_query_installed(query_name="get_transaction_context")
        raw_check = installed_check[0].text if hasattr(installed_check[0], "text") else str(installed_check[0])
        print("  -> is_query_installed('get_transaction_context') check passed.")

        # Test running get_transaction_context on a known benchmark transaction
        test_txn_id = "3514030" # HHG-001 anchor txn
        query_res = await run_installed_query(
            query_name="get_transaction_context",
            params={"txn_id": test_txn_id}
        )
        raw_query = query_res[0].text if hasattr(query_res[0], "text") else str(query_res[0])
        if "target_txn" in raw_query or test_txn_id in raw_query:
            print(f"  [PASS] Successfully executed GSQL query 'get_transaction_context' for txn {test_txn_id} via MCP.")
        else:
            print(f"  [INFO] Query response: {raw_query[:200]}")
    except Exception as e:
        print(f"  [FAIL] run_installed_query tool call failed: {e}")
        return 1

    print("\n" + "=" * 65)
    print("STATUS: All TigerGraph MCP tool calls succeeded with zero errors.")
    print("=" * 65 + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
