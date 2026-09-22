import json
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
dry_run_path = project_root / "cases" / "dry_run_uncertainty_assessment.json"

with open(dry_run_path, "r", encoding="utf-8") as f:
    benchmarks = json.load(f)

rows = []
mismatches = []
match_count = 0

for item in benchmarks:
    case_id = item["case_id"]
    upstream_pattern = item.get("risk_assessment", {}).get("pattern_matched", "none")
    
    answer_file = project_root / "cases" / f"{case_id}_answer.json"
    if answer_file.exists():
        with open(answer_file, "r", encoding="utf-8") as af:
            ans_data = json.load(af)
            final_pattern = ans_data.get("case", {}).get("pattern", "none")
    else:
        final_pattern = "FILE_NOT_FOUND"

    is_match = (upstream_pattern == final_pattern)
    match_str = "YES" if is_match else "NO"
    if is_match:
        match_count += 1
    else:
        mismatches.append(case_id)

    rows.append((case_id, upstream_pattern, final_pattern, match_str))

print("=" * 75)
print(f"| {'case_id':<8} | {'upstream_pattern':<26} | {'final_pattern':<26} | {'match':<5} |")
print("|" + "-" * 10 + "|" + "-" * 28 + "|" + "-" * 28 + "|" + "-" * 7 + "|")
for r in rows:
    print(f"| {r[0]:<8} | {r[1]:<26} | {r[2]:<26} | {r[3]:<5} |")
print("=" * 75)

print(f"\n{match_count} of {len(benchmarks)} cases match")
if mismatches:
    print(f"Mismatched case_ids: {', '.join(mismatches)}")
else:
    print("Mismatched case_ids: None")
