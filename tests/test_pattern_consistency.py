import json
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
dry_run_path = project_root / "cases" / "dry_run_uncertainty_assessment.json"

with open(dry_run_path, "r", encoding="utf-8") as f:
    benchmarks = json.load(f)

BENCHMARK_CASES = {b["case_id"]: b.get("risk_assessment", {}).get("pattern_matched", "none") for b in benchmarks}
CASE_IDS = [f"HHG-{i:03d}" for i in range(1, 21)]

@pytest.mark.parametrize("case_id", CASE_IDS)
def test_pattern_consistency_per_case(case_id):
    """
    Assert that the pattern_matched in dry_run_uncertainty_assessment.json
    matches the 'pattern' field in cases/HHG-0XX_answer.json verbatim.
    """
    assert case_id in BENCHMARK_CASES, f"Case {case_id} missing from dry run benchmark assessment"
    upstream_pattern = BENCHMARK_CASES[case_id]

    answer_path = project_root / "cases" / f"{case_id}_answer.json"
    assert answer_path.exists(), f"Answer file {answer_path.name} not found"

    with open(answer_path, "r", encoding="utf-8") as f:
        answer_data = json.load(f)

    final_pattern = answer_data.get("case", {}).get("pattern")
    assert final_pattern == upstream_pattern, (
        f"Pattern mismatch for {case_id}: upstream assessed pattern='{upstream_pattern}', "
        f"but final answer file contains pattern='{final_pattern}'"
    )

def test_all_20_cases_present():
    """Assert all 20 benchmark case answer files exist and are populated."""
    for case_id in CASE_IDS:
        answer_path = project_root / "cases" / f"{case_id}_answer.json"
        assert answer_path.exists(), f"Missing answer file: {answer_path.name}"
        with open(answer_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "case" in data and "pattern" in data["case"]
