from flask import Flask, request, redirect
import json

from fhir_client import (
    get_patient, create_patient, get_all_patients,
    upload_questionnaire, populate_questionnaire,
    save_questionnaire_response, get_questionnaire_response,
    get_responses_for_patient
)
from terminology import validate_code, translate_code, CODED_FIELDS

app = Flask(__name__)
active_patient = None


# ==========================
# GLOBAL PAGE TEMPLATE
# ==========================
def render_page(title, content):
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .bg-mint      {{ background-color: #96bcb4 !important; }}
            .bg-lightmint {{ background-color: #bbdcd3 !important; }}
            .bg-softblue  {{ background-color: #b2ced6 !important; }}
            .bg-steelblue {{ background-color: #9dbbc9 !important; }}
            .btn-mint     {{ background-color: #96bcb4; color: white; border: none; }}
            .btn-mint:hover {{ background-color: #91accb; }}
        </style>
    </head>
    <body class="bg-lightmint">
        <nav class="navbar bg-mint px-4">
            <span class="navbar-brand text-white fw-bold">Mini FHIR Website</span>
        </nav>
        <div class="container mt-5">
            <div class="card shadow-lg border-0 rounded-4 p-5">
                <h2 class="mb-4">{title}</h2>
                {content}
            </div>
        </div>
    </body>
    </html>
    """


# ==========================
# DASHBOARD
# ==========================
@app.route("/")
def dashboard():
    patient_info = "None selected"

    if active_patient:
        given, family = get_patient(active_patient)
        if given or family:
            patient_info = f"{active_patient} – {given} {family}"
        else:
            patient_info = active_patient

    content = f"""
    <div class="d-grid gap-3">
        <a href="/select_patient"      class="btn bg-softblue  text-dark btn-lg rounded-3 shadow-sm">Select Patient</a>
        <a href="/start_questionnaire" class="btn bg-softblue  text-dark btn-lg rounded-3 shadow-sm">Start Questionnaire</a>
        <a href="/create_patient"      class="btn bg-softblue  text-dark btn-lg rounded-3 shadow-sm">Create Patient</a>
        <a href="/upload_questionnaire"class="btn bg-softblue  text-dark btn-lg rounded-3 shadow-sm">Upload Questionnaire</a>
        <a href="/history"             class="btn bg-steelblue text-dark btn-lg rounded-3 shadow-sm"> Patient History</a>
    </div>
    <hr class="my-4">
    <div class="alert bg-light border">
        <strong>Active Patient:</strong> {patient_info}
    </div>
    """
    return render_page("Dashboard", content)


# ==========================
# CREATE PATIENT
# ==========================
@app.route("/create_patient", methods=["GET", "POST"])
def create_patient_route():
    global active_patient

    if request.method == "POST":
        given  = request.form["given"]
        family = request.form["family"]
        pid    = create_patient(given, family)
        active_patient = pid
        return render_page("Patient Created", f"""
            <div class="alert alert-success">Patient successfully created!</div>
            <h4>ID: {pid}</h4>
            <a href="/" class="btn btn-primary mt-3">Back to Dashboard</a>
        """)

    content = """
        <form method="post">
            <div class="mb-3">
                <label class="form-label">Firstname</label>
                <input name="given" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Lastname</label>
                <input name="family" class="form-control" required>
            </div>
            <button class="btn btn-primary">Create Patient</button>
        </form>
    """
    return render_page("Create Patient", content)


# ==========================
# SELECT PATIENT
# ==========================
@app.route("/select_patient", methods=["GET", "POST"])
def select_patient():
    global active_patient

    if request.method == "POST":
        active_patient = request.form["patient_id"]
        return redirect("/")

    content = """
        <form method="post">
            <div class="mb-3">
                <label class="form-label">Patient ID</label>
                <input name="patient_id" class="form-control" required>
            </div>
            <button class="btn btn-outline-dark">Set Active</button>
        </form>
    """
    return render_page("Select Patient", content)


# ==========================
# UPLOAD QUESTIONNAIRE
# ==========================
@app.route("/upload_questionnaire", methods=["GET", "POST"])
def upload_questionnaire_route():
    if request.method == "POST":
        file    = request.files["file"]
        q_json  = json.load(file)
        qid     = upload_questionnaire(q_json)
        return render_page("Questionnaire Uploaded", f"""
            <div class="alert alert-success">Questionnaire uploaded successfully!</div>
            <h4>ID: {qid}</h4>
            <a href="/" class="btn btn-primary mt-3">Back to Dashboard</a>
        """)

    content = """
        <form method="post" enctype="multipart/form-data">
            <div class="mb-3">
                <label class="form-label">Select JSON File</label>
                <input type="file" name="file" class="form-control" required>
            </div>
            <button class="btn btn-info text-white">Upload</button>
        </form>
    """
    return render_page("Upload Questionnaire", content)


# ==========================
# START QUESTIONNAIRE
# ==========================
@app.route("/start_questionnaire", methods=["GET", "POST"])
def start_questionnaire():
    if request.method == "POST":
        qid = request.form["qid"]
        return redirect(f"/questionnaire/{qid}")

    content = """
        <form method="post">
            <div class="mb-3">
                <label class="form-label">Questionnaire ID</label>
                <input name="qid" class="form-control" required>
            </div>
            <button class="btn btn-success">Start</button>
        </form>
    """
    return render_page("Start Questionnaire", content)


# ==========================
# QUESTIONNAIRE
# ==========================
@app.route("/questionnaire/<qid>", methods=["GET", "POST"])
def questionnaire(qid):
    global active_patient

    if not active_patient:
        return redirect("/")

    # ── GET: $populate ──
    if request.method == "GET":
        qr, error = populate_questionnaire(qid, active_patient)
        if error:
            return render_page("Error", f"<div class='alert alert-danger'>Populate failed: {error}</div>")
        items = qr.get("item", [])

    # ── POST: Validieren, Übersetzen, Speichern ──
    else:
        items             = []
        validation_errors = []

        for key in request.form:
            value = request.form.get(key)

            if key in CODED_FIELDS and value:
                is_valid, msg = validate_code(value)
                if not is_valid:
                    validation_errors.append(
                        f"Feld '{key}': Code '{value}' ist ungültig. Erlaubt sind 1–6. {msg}"
                    )
                    continue
                translated = translate_code(value)
                if translated:
                    value = translated

            items.append({"linkId": key, "answer": [{"valueString": value}]})

        if validation_errors:
            error_html = "".join(f"<div class='alert alert-danger'>{e}</div>" for e in validation_errors)
            error_html += f"<a href='/questionnaire/{qid}' class='btn btn-secondary mt-2'>Zurück</a>"
            return render_page("Validierungsfehler", error_html)

        qr_id, error = save_questionnaire_response(qid, active_patient, items)
        if qr_id:
            return redirect(f"/response_summary/{qr_id}")
        return render_page("Error", f"<div class='alert alert-danger'>Save failed: {error}</div>")

    # ── Formular rendern ──
    form_html = "<form method='post'>"
    for item in items:
        value = ""
        if "answer" in item:
            answer = item["answer"][0]
            value  = list(answer.values())[0]

        input_type = "text"
        if item.get("type") == "date":
            input_type = "date"
        elif item.get("type") == "integer":
            input_type = "number"

        form_html += f"""
            <div class="mb-3">
                <label class="form-label">{item.get('text', item['linkId'])}</label>
                <input type="{input_type}" name="{item['linkId']}" value="{value}" class="form-control">
            </div>
        """
    form_html += "<button class='btn bg-softblue text-dark btn-lg rounded-3 shadow-sm'>Submit</button></form>"
    return render_page(f"Questionnaire {qid}", form_html)


# ==========================
# RESPONSE SUMMARY
# ==========================
@app.route("/response_summary/<qr_id>")
def response_summary(qr_id):
    qr = get_questionnaire_response(qr_id)
    if not qr:
        return render_page("Fehler", "<div class='alert alert-danger'>Antwort nicht gefunden.</div>")

    pid   = qr.get("subject", {}).get("reference", "").replace("Patient/", "")
    items = qr.get("item", [])

    given, family  = get_patient(pid)
    patient_name   = f"{given} {family}" if given or family else pid

    rows = ""
    for item in items:
        label  = item.get("text", item.get("linkId", ""))
        answer = item.get("answer", [{}])[0]
        value  = list(answer.values())[0] if answer else "–"
        rows  += f"<tr><td class='fw-semibold'>{label}</td><td>{value}</td></tr>"

    content = f"""
        <div class="alert bg-light border mb-4">
            <strong>Patient:</strong> {patient_name} (ID: {pid})<br>
            <strong>Response ID:</strong> {qr_id}
        </div>
        <table class="table table-bordered table-hover rounded">
            <thead class="bg-softblue"><tr><th>Feld</th><th>Gespeicherter Wert</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="d-flex gap-3 mt-4">
            <a href="/"        class="btn bg-softblue  text-dark rounded-3 shadow-sm">🏠 Dashboard</a>
            <a href="/history" class="btn bg-steelblue text-dark rounded-3 shadow-sm">📋 Patient History</a>
        </div>
    """
    return render_page("✅ Gespeichert", content)


# ==========================
# PATIENT HISTORY
# ==========================
@app.route("/history")
def history():
    patients = get_all_patients()

    if not patients:
        return render_page("Patient History", "<div class='alert alert-info'>Keine Patienten gefunden.</div>")

    accordion = ""
    for i, patient in enumerate(patients):
        pid   = patient["id"]
        pname = patient["name"]

        responses     = get_responses_for_patient(pid)
        responses_html = ""

        if responses:
            for qr in responses:
                qr_id     = qr["id"]
                date      = qr.get("meta", {}).get("lastUpdated", "")[:10]
                item_rows = ""
                for item in qr.get("item", []):
                    label     = item.get("text", item.get("linkId", ""))
                    answer    = item.get("answer", [{}])[0]
                    value     = list(answer.values())[0] if answer else "–"
                    item_rows += f"<tr><td class='fw-semibold'>{label}</td><td>{value}</td></tr>"

                responses_html += f"""
                    <div class="card mb-3 border-0 shadow-sm">
                        <div class="card-header bg-lightmint d-flex justify-content-between">
                            <span>📄 Response ID: {qr_id}</span>
                            <span class="text-muted">{date}</span>
                        </div>
                        <div class="card-body p-0">
                            <table class="table table-sm table-bordered mb-0">
                                <thead class="bg-softblue"><tr><th>Feld</th><th>Wert</th></tr></thead>
                                <tbody>{item_rows}</tbody>
                            </table>
                        </div>
                    </div>
                """
        else:
            responses_html = "<p class='text-muted ps-2'>Keine Antworten vorhanden.</p>"

        accordion += f"""
            <div class="accordion-item border-0 mb-2 shadow-sm rounded-3 overflow-hidden">
                <h2 class="accordion-header">
                    <button class="accordion-button collapsed bg-softblue text-dark fw-semibold"
                            type="button" data-bs-toggle="collapse" data-bs-target="#p{i}">
                        👤 {pname} <span class="text-muted ms-2 fw-normal">ID: {pid}</span>
                    </button>
                </h2>
                <div id="p{i}" class="accordion-collapse collapse">
                    <div class="accordion-body">{responses_html}</div>
                </div>
            </div>
        """

    content = f"""
        <div class="accordion" id="historyAccordion">{accordion}</div>
        <a href="/" class="btn bg-softblue text-dark rounded-3 shadow-sm mt-4">🏠 Dashboard</a>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    """
    return render_page("Patient History", content)


# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(debug=True)