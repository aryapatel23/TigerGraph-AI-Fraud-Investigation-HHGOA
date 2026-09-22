import json

with open("cases/dry_run_uncertainty_assessment.json") as f:
    data = json.load(f)

for c in data:
    ra = c["risk_assessment"]
    print(f"{c['case_id']} | Txn: {c['flagged_txn_id']} | Pattern: {ra.get('pattern_matched')} | Risk: {ra.get('risk_level')} | Conf: {ra.get('confidence')} | NeedsMore: {ra.get('needs_more_evidence')}")
