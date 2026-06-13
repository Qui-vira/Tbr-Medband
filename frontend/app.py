"""Flask web form backend for MedBand case intake."""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, redirect, render_template, request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from core.reports import build_patient_report
from core.sector_loader import SECTOR_META, get_active_sector, human_role, load_institutions, sector_meta, set_active_sector
from core.workflow import load_case, run_case, run_case_stream

app = Flask(__name__, template_folder=".")


def _form_raw(data) -> tuple[str, str]:
    sector = data.get("sector", "pharmacy")
    set_active_sector(sector)

    lines = [f"Sector: {sector}"]

    name = data.get("name", "")
    issue = data.get("issue", "")
    service = data.get("service", "")

    if sector == "emergency":
        service = data.get("emergency_type", service)
        lines.extend([
            f"Caller name: {name}",
            f"Emergency type: {service}",
            f"Location: {data.get('location', '')}",
            f"Additional details: {issue}",
        ])
    elif sector == "mental_health":
        self_harm = data.get("self_harm_flag") in ("true", "on", "1", True)
        lines.extend([
            f"Name: {name}",
            f"Presenting concern: {issue}",
            f"Duration: {data.get('duration', '')}",
            f"Self harm flag: {self_harm}",
            f"Requested service: {service or issue}",
            f"Urgency: {data.get('urgency', 'medium')}",
        ])
    elif sector == "hospital_triage":
        lines.extend([
            f"Name: {name}",
            f"Chief complaint: {issue}",
            f"Vitals description: {data.get('vitals_description', '')}",
            f"Requested service: {service or issue}",
            f"Urgency: {data.get('urgency', 'high')}",
        ])
    elif sector == "lab":
        lines.extend([
            f"Name: {name}",
            f"Test requested: {service}",
            f"Referral number: {data.get('referral_number', '')}",
            f"Patient ID: {data.get('patient_id', '')}",
            f"Clinical notes: {issue}",
            f"Urgency: {data.get('urgency', 'medium')}",
        ])
    elif sector == "hmo_claims":
        lines.extend([
            f"Requester name: {name}",
            f"Procedure code: {service}",
            f"Policy number: {data.get('policy_number', '')}",
            f"Provider name: {data.get('provider_name', '')}",
            f"Claim notes: {issue}",
            f"Urgency: {data.get('urgency', 'low')}",
        ])
    else:
        lines.extend([
            f"Name: {name}",
            f"Issue: {issue}",
            f"Requested service: {service}",
            f"Urgency: {data.get('urgency', 'high')}",
        ])
        if data.get("prescription_code"):
            lines.append(f"Prescription code: {data.get('prescription_code')}")

    return "\n".join(lines), sector


@app.route("/")
def index():
    return render_template("index.html", sectors=SECTOR_META)


@app.route("/status")
def status_page():
    return render_template("status.html")


@app.route("/api/sectors")
def api_sectors():
    return jsonify(SECTOR_META)


@app.route("/api/case/<case_id>")
def api_case(case_id):
    case = load_case(case_id.upper())
    if not case:
        return jsonify({"error": "Case not found"}), 404
    return jsonify(case)


@app.route("/submit", methods=["POST"])
def submit():
    raw, sector = _form_raw(request.form)
    institution_id = request.form.get("institution_id") or None
    try:
        result = run_case(raw, sector=sector, institution_id=institution_id)
        result["patient_report"] = build_patient_report(result)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc), "status": "ERROR"}), 500


@app.route("/submit/stream", methods=["POST"])
def submit_stream():
    raw, sector = _form_raw(request.form)
    institution_id = request.form.get("institution_id") or None

    def generate():
        try:
            for event in run_case_stream(raw, sector=sector, institution_id=institution_id):
                yield json.dumps(event) + "\n"
        except Exception as exc:
            yield json.dumps({"type": "error", "error": str(exc)}) + "\n"

    return Response(generate(), mimetype="application/x-ndjson")


@app.route("/api/lookup/<case_id>")
def lookup(case_id):
    case = load_case(case_id.upper())
    if not case:
        return jsonify({"error": "Case not found"}), 404
    report = build_patient_report(case)
    return jsonify({"case": case, "report": report, "sector": sector_meta(case.get("sector"))})


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/api/institutions/<sector>")
def get_institutions(sector):
    return jsonify(load_institutions(sector))


@app.route("/api/register", methods=["POST"])
def register_institution():
    data = request.get_json(silent=True) or {}
    data["timestamp"] = datetime.now(timezone.utc).isoformat()
    data["status"] = "pending"
    data["id"] = str(uuid.uuid4())[:8].upper()

    reg_path = ROOT / "data" / "registrations.json"
    registrations = []
    if reg_path.exists():
        with open(reg_path, encoding="utf-8") as f:
            registrations = json.load(f)
    registrations.append(data)
    reg_path.parent.mkdir(exist_ok=True)
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(registrations, f, indent=2)

    return jsonify({
        "success": True,
        "message": "Registration received",
        "id": data["id"],
    })


@app.route("/api/admin/registrations")
def view_registrations():
    reg_path = ROOT / "data" / "registrations.json"
    if reg_path.exists():
        with open(reg_path, encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route("/landing")
def landing_redirect():
    return redirect("https://medband-landing.vercel.app")


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "MedBand",
        "landing": "https://medband-landing.vercel.app",
        "form": "https://web-production-6d13b.up.railway.app",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
