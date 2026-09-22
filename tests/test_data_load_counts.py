import pytest

EXPECTED_COUNTS = {
    "Transaction": 590742,      # Exactly 590,742 transactions from transactions.csv
    "IdentityRecord": 144432,   # Exactly 144,432 identity records from identity.csv
    "FraudCase": 5585,          # 5,565 historical cases + 20 benchmark cases
    "FraudPattern": 7,          # 7 reference fraud patterns (card_testing, account_takeover, etc.)
    "Customer": 13564,          # Deduplicated customer entities derived from card issuers
    "Card": 13944,              # Deduplicated payment card entities
    "DeviceProfile": 9705,      # Deduplicated device fingerprints
    "BillingRegion": 332,       # Distinct geographic billing regions
    "EmailDomain": 60,          # Distinct email domains
}

def test_transaction_count(tg_conn):
    """Assert Transaction count matches data dictionary: exactly 590,742 rows."""
    count = tg_conn.getVertexCount("Transaction")
    assert count == 590742, f"Transaction count mismatch: expected 590,742, got {count}"

def test_identity_record_count(tg_conn):
    """Assert IdentityRecord count matches data dictionary: exactly 144,432 rows."""
    count = tg_conn.getVertexCount("IdentityRecord")
    assert count == 144432, f"IdentityRecord count mismatch: expected 144,432, got {count}"

def test_fraud_case_count(tg_conn):
    """Assert FraudCase count matches 5,565 historical + 20 benchmark = 5,585 cases."""
    count = tg_conn.getVertexCount("FraudCase")
    assert count == 5585, f"FraudCase count mismatch: expected 5,585, got {count}"

def test_fraud_pattern_count(tg_conn):
    """Assert FraudPattern reference definitions count matches 7 standard typologies."""
    count = tg_conn.getVertexCount("FraudPattern")
    assert count == 7, f"FraudPattern count mismatch: expected 7, got {count}"

@pytest.mark.parametrize("vertex_type,expected_count", [
    ("Customer", 13564),
    ("Card", 13944),
    ("DeviceProfile", 9705),
    ("BillingRegion", 332),
    ("EmailDomain", 60),
])
def test_derived_entity_counts(tg_conn, vertex_type, expected_count):
    """Assert entity counts match data dictionary and reconciliation baseline."""
    count = tg_conn.getVertexCount(vertex_type)
    assert count == expected_count, f"{vertex_type} count mismatch: expected {expected_count}, got {count}"
