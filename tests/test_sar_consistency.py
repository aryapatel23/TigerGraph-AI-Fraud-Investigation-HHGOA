import json
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
CASES_DIR = project_root / "cases"
CASE_IDS = [f"HHG-{i:03d}" for i in range(1, 21)]

@pytest.mark.parametrize("case_id", CASE_IDS)
def test_sar_verdict_coincidence_per_case(case_id):
    """
    Assert that sar.file=True ONLY coincides with final verdict='fraud'.
    Under no circumstances should an 'uncertain' or 'legitimate' case file a SAR.
    Catches regressions where uncertain/escalated cases prematurely file SARs.
    """
    answer_path = CASES_DIR / f"{case_id}_answer.json"
    assert answer_path.exists(), f"Missing answer file: {answer_path.name}"

    with open(answer_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    case_obj = data.get("case", {})
    sar_obj = data.get("sar", {})

    verdict = case_obj.get("verdict")
    status = case_obj.get("status")
    sar_file = sar_obj.get("file")

    if sar_file is True:
        assert verdict == "fraud", (
            f"Rule Violation in {case_id}: sar.file is True, but verdict is '{verdict}'. "
            f"SAR can only be filed on substantiated cases with final verdict='fraud'."
        )
        assert status == "closed_fraud", (
            f"Status mismatch in {case_id}: sar.file is True, but status is '{status}'"
        )
    else:
        assert sar_file is False, f"sar.file must be a boolean in {case_id}"

    if verdict in ["uncertain", "pending_verification"]:
        assert sar_file is False, (
            f"Bug detected in {case_id}: verdict is '{verdict}' (needs more evidence), "
            f"so sar.file must be False. Found sar.file={sar_file}."
        )

    if verdict == "legitimate":
        assert sar_file is False, (
            f"Bug detected in {case_id}: verdict is 'legitimate', so sar.file must be False."
        )

def test_aggregate_sar_distribution():
    """
    Assert the overall benchmark SAR distribution matches policy constraints:
    Exactly 3 substantiated high-risk cases (HHG-010, HHG-011, HHG-014) file SARs,
    and all 17 uncertain/escalated cases defer SAR filing.
    """
    sars_filed = []
    sars_deferred = []

    for case_id in CASE_IDS:
        answer_path = CASES_DIR / f"{case_id}_answer.json"
        with open(answer_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("sar", {}).get("file") is True:
            sars_filed.append(case_id)
        else:
            sars_deferred.append(case_id)

    assert len(sars_filed) == 3, f"Expected exactly 3 SARs filed, got {len(sars_filed)}: {sars_filed}"
    assert sorted(sars_filed) == ["HHG-010", "HHG-011", "HHG-014"]
    assert len(sars_deferred) == 17, f"Expected 17 deferred SARs, got {len(sars_deferred)}"
