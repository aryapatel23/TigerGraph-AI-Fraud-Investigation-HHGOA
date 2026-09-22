import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("cases/dry_run_uncertainty_assessment.json", encoding="utf-8") as f:
    cases = json.load(f)

for c in cases:
    ra = c["risk_assessment"]
    needs = "Yes" if c["needs_more_evidence"] else "No"
    print(f"| **{c['case_id']}** | {c['flagged_txn_id']} | `{ra['pattern_matched']}` | `{ra['risk_level']}` | {ra['confidence']:.2f} | {needs} | {ra['reasoning']} |")
