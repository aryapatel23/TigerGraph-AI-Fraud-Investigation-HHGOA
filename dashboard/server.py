import os
import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8080
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = PROJECT_ROOT / "cases"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

class CaseReviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def do_GET(self):
        # API route: list all cases
        if self.path == "/api/cases" or self.path == "/api/cases/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            dry_run_file = CASES_DIR / "dry_run_uncertainty_assessment.json"
            benchmarks_by_id = {}
            if dry_run_file.exists():
                try:
                    with open(dry_run_file, "r", encoding="utf-8") as f:
                        for b in json.load(f):
                            benchmarks_by_id[b.get("case_id")] = b
                except Exception:
                    pass

            cases_data = []
            for i in range(1, 21):
                case_id = f"HHG-{i:03d}"
                case_file = CASES_DIR / f"{case_id}_answer.json"
                if case_file.exists():
                    try:
                        with open(case_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            bm = benchmarks_by_id.get(case_id, {})
                            if bm:
                                data["trigger_type"] = bm.get("trigger_type")
                                data["trigger_text"] = bm.get("trigger_text")
                                data["trigger_risk_score"] = bm.get("trigger_risk_score")
                            cases_data.append(data)
                    except Exception as e:
                        cases_data.append({"case_id": case_id, "error": str(e)})
                else:
                    cases_data.append({"case_id": case_id, "error": "file_not_found"})

            self.wfile.write(json.dumps(cases_data, indent=2).encode("utf-8"))
            return

        # API route: get single case
        if self.path.startswith("/api/cases/"):
            case_id = self.path.split("/api/cases/")[1].split("?")[0].strip("/")
            case_file = CASES_DIR / f"{case_id}_answer.json"
            if case_file.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(case_file, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Case {case_id} not found"}).encode("utf-8"))
            return

        # Default: serve static files from dashboard directory
        super().do_GET()

def run_server(port=PORT):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CaseReviewHandler)
    print("=" * 70)
    print(f"  TigerGraph Fraud Agent — Case Review Dashboard")
    print(f"  Running locally at: http://localhost:{port}")
    print("=" * 70)
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    import sys
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(p)
