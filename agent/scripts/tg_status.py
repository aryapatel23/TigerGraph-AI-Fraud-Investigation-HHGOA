import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import pyTigerGraph as tg

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(project_root / ".env")

    host = os.getenv("TG_HOST", "http://localhost")
    port = os.getenv("TG_PORT", "14240")
    username = os.getenv("TG_USERNAME", "tigergraph")
    password = os.getenv("TG_PASSWORD", "tigergraph")
    graph_name = os.getenv("TG_GRAPH_NAME", "FraudInvestigation")

    print("\n" + "="*60)
    print("       TIGERGRAPH SERVICE & GRAPH STATUS CHECK")
    print("="*60)
    print(f"Target Host:     {host}:{port}")
    print(f"Target Graph:    {graph_name}")
    print(f"Connecting user: {username}")

    try:
        conn = tg.TigerGraphConnection(
            host=host,
            restppPort=port,
            username=username,
            password=password,
            graphname=graph_name
        )
        echo = conn.echo()
        print(f"RESTPP Echo:     [OK] ({echo})")
    except Exception as e:
        print(f"[FAIL] Unable to connect to TigerGraph: {e}")
        print("Tip: Run 'docker ps' or 'docker exec -it tigergraph-hhgoa gadmin status'")
        sys.exit(1)

    try:
        v_counts = conn.getVertexCount("*")
        total_v = sum(v_counts.values()) if isinstance(v_counts, dict) else "N/A"
        print(f"Active Vertices: {total_v:,} across {len(v_counts)} vertex types")
        print("\nVertex Counts Breakdown:")
        for v_type, cnt in sorted(v_counts.items()):
            print(f"  - {v_type:<18}: {cnt:>10,}")
    except Exception as e:
        print(f"[WARN] Error fetching vertex counts: {e}")

    try:
        e_counts = conn.getEdgeCount("*")
        total_e = sum(e_counts.values()) if isinstance(e_counts, dict) else "N/A"
        print(f"\nActive Edges:    {total_e:,} across {len(e_counts)} edge types")
    except Exception as e:
        print(f"[WARN] Error fetching edge counts: {e}")

    print("="*60)
    print("STATUS: TigerGraph is healthy and ready for queries.\n")

if __name__ == "__main__":
    main()
