from pathlib import Path
import pytest

EXPECTED_VERTEX_TYPES = {
    "Customer", "Card", "Transaction", "DeviceProfile", "IdentityRecord",
    "BillingRegion", "EmailDomain", "FraudPattern", "FraudCase", "Evidence", "Decision"
}

EXPECTED_FORWARD_EDGE_TYPES = {
    "OWNS", "MADE", "FROM_DEVICE", "HAS_IDENTITY", "BILLED_IN",
    "USES_EMAIL_DOMAIN", "NEXT_TXN", "INVOLVES_TXN", "ON_CARD",
    "CONNECTED_TO_CARD", "INVOLVES_CUSTOMER", "LINKED_DEVICE",
    "MATCHES_PATTERN", "HAS_EVIDENCE", "HAS_DECISION", "SIMILAR_TO_CASE"
}

def test_schema_vertex_counts(tg_conn):
    """Assert the graph has exactly 11 vertex types matching schema.gsql."""
    vertex_types = set(tg_conn.getVertexTypes())
    assert len(vertex_types) == 11, f"Expected exactly 11 vertex types, got {len(vertex_types)}: {vertex_types}"
    assert vertex_types == EXPECTED_VERTEX_TYPES, f"Vertex types mismatch. Difference: {vertex_types ^ EXPECTED_VERTEX_TYPES}"

def test_schema_edge_counts(tg_conn):
    """
    Assert the graph schema has the edge types as defined in schema.gsql.
    schema.gsql defines 16 forward edge types (with 14 reverse edge pairs,
    totaling the 20 edge relationship specifications).
    """
    edge_types = set(tg_conn.getEdgeTypes())
    assert len(edge_types) == 16, f"Expected 16 registered forward edge types, got {len(edge_types)}: {edge_types}"
    assert edge_types == EXPECTED_FORWARD_EDGE_TYPES, f"Edge types mismatch. Difference: {edge_types ^ EXPECTED_FORWARD_EDGE_TYPES}"

def test_schema_gsql_file_specifications():
    """Assert gsql/schema.gsql explicitly defines the 11 vertex types and 20 edge types."""
    schema_path = Path(__file__).resolve().parent.parent / "gsql" / "schema.gsql"
    assert schema_path.exists(), "gsql/schema.gsql file does not exist"
    content = schema_path.read_text(encoding="utf-8")

    # Assert 11 vertex types defined
    for v in EXPECTED_VERTEX_TYPES:
        assert f"CREATE VERTEX {v}" in content, f"Missing definition for vertex type: {v}"

    # Assert 20 edge types specification in schema
    assert "VERTEX TYPES (11 Types)" in content or "Vertices (11)" in content
    assert "EDGE TYPES (20" in content or "Edges (20 Directed types)" in content
