from flask import Flask, request, redirect, url_for
import requests
import json

FHIR_BASE = "http://localhost:8080/fhir"
app = Flask(__name__)

active_patient = None


# ==========================
# GLOBAL PAGE TEMPLATE
# ==========================
def render_page(page_id, content, page_title=""):
    nav_items = [
        ("dashboard",    "ti-layout-dashboard",  "Dashboard"),
        ("create",       "ti-user-plus",          "Create patient"),
        ("select",       "ti-users",              "Select patient"),
        ("upload",       "ti-file-upload",         "Upload questionnaire"),
        ("questionnaire","ti-clipboard-text",     "Start questionnaire"),
    ]

    nav_html = ""
    for nid, icon, label in nav_items:
        active_cls = "active" if nid == page_id else ""
        href = f"/{nid}" if nid != "dashboard" else "/"
        nav_html += f"""
        <a href="{href}" class="nav-item {active_cls}">
            <i class="ti {icon}" aria-hidden="true"></i>
            <span>{label}</span>
        </a>"""

    patient_info = "None selected"
    patient_name = ""
    if active_patient:
        try:
            r = requests.get(f"{FHIR_BASE}/Patient/{active_patient}", timeout=3)
            if r.ok:
                p = r.json()
                name = p.get("name", [{}])[0]
                given = " ".join(name.get("given", []))
                family = name.get("family", "")
                patient_name = f"{given} {family}".strip()
                patient_info = f"{patient_name}"
        except Exception:
            patient_info = f"ID {active_patient}"
            patient_name = patient_info

    patient_dot = '<span class="status-dot"></span>' if active_patient else ""

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FHIR Demo{' – ' + page_title if page_title else ''}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css">
    <style>
        :root {{
            --bg:       #f4f6f9;
            --surface:  #ffffff;
            --sidebar:  #0f1923;
            --accent:   #2563eb;
            --accent2:  #06b6d4;
            --text:     #0f1923;
            --muted:    #6b7280;
            --border:   #e5e7eb;
            --success:  #10b981;
            --radius:   10px;
            --radius-lg:14px;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'DM Sans', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
        }}

        /* ── SIDEBAR ── */
        .sidebar {{
            width: 240px;
            background: var(--sidebar);
            display: flex;
            flex-direction: column;
            padding: 0;
            position: fixed;
            top: 0; left: 0; bottom: 0;
            z-index: 100;
        }}
        .sidebar-logo {{
            padding: 1.5rem 1.25rem 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.07);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .logo-icon {{
            width: 32px; height: 32px;
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; color: #fff;
        }}
        .logo-text {{
            font-size: 14px;
            font-weight: 600;
            color: #fff;
            letter-spacing: 0.01em;
        }}
        .logo-sub {{
            font-size: 10px;
            color: rgba(255,255,255,0.35);
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        .nav-section {{
            padding: 1rem 0.75rem 0.5rem;
        }}
        .nav-label {{
            font-size: 10px;
            color: rgba(255,255,255,0.3);
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 0 0.5rem;
            margin-bottom: 4px;
        }}
        .nav-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 9px 12px;
            border-radius: var(--radius);
            font-size: 13px;
            color: rgba(255,255,255,0.55);
            text-decoration: none;
            transition: background 0.15s, color 0.15s;
            margin-bottom: 2px;
        }}
        .nav-item i {{ font-size: 17px; flex-shrink: 0; }}
        .nav-item:hover {{ background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.9); }}
        .nav-item.active {{ background: rgba(37,99,235,0.25); color: #fff; }}
        .nav-item.active i {{ color: #60a5fa; }}

        .patient-card {{
            margin: auto 0.75rem 1rem;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: var(--radius);
            padding: 12px 14px;
        }}
        .patient-card .pc-label {{
            font-size: 10px;
            color: rgba(255,255,255,0.3);
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 5px;
        }}
        .patient-card .pc-name {{
            font-size: 13px;
            font-weight: 500;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 7px;
        }}
        .status-dot {{
            width: 6px; height: 6px;
            border-radius: 50%;
            background: var(--success);
            flex-shrink: 0;
        }}

        /* ── MAIN ── */
        .main {{
            margin-left: 240px;
            flex: 1;
            padding: 2rem 2.5rem;
            min-height: 100vh;
        }}
        .topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2rem;
        }}
        .page-heading {{
            font-size: 22px;
            font-weight: 600;
            color: var(--text);
        }}
        .page-sub {{
            font-size: 13px;
            color: var(--muted);
            margin-top: 2px;
        }}

        /* ── CARDS ── */
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
        }}
        .action-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 14px;
            margin-bottom: 2rem;
        }}
        .action-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.25rem;
            text-decoration: none;
            display: flex;
            flex-direction: column;
            gap: 12px;
            transition: border-color 0.15s, box-shadow 0.15s;
            cursor: pointer;
        }}
        .action-card:hover {{
            border-color: #93c5fd;
            box-shadow: 0 4px 16px rgba(37,99,235,0.08);
        }}
        .ac-icon {{
            width: 40px; height: 40px;
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
        }}
        .ac-title {{ font-size: 13px; font-weight: 600; color: var(--text); }}
        .ac-sub   {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}

        /* ── FORMS ── */
        .form-wrap {{ max-width: 480px; }}
        .form-group {{ margin-bottom: 1.1rem; }}
        .form-group label {{
            display: block;
            font-size: 12px;
            font-weight: 500;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
        }}
        .form-group input, .form-group select {{
            width: 100%;
            padding: 9px 13px;
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            background: var(--surface);
            color: var(--text);
            outline: none;
            transition: border-color 0.15s;
        }}
        .form-group input:focus, .form-group select:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 9px 18px;
            border-radius: var(--radius);
            font-family: 'DM Sans', sans-serif;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            border: none;
            transition: background 0.15s, transform 0.1s;
            text-decoration: none;
        }}
        .btn:active {{ transform: scale(0.98); }}
        .btn-primary {{ background: var(--accent); color: #fff; }}
        .btn-primary:hover {{ background: #1d4ed8; }}
        .btn-ghost {{
            background: transparent;
            color: var(--muted);
            border: 1px solid var(--border);
        }}
        .btn-ghost:hover {{ background: var(--bg); }}

        /* ── BADGES ── */
        .badge {{
            display: inline-flex; align-items: center;
            font-size: 11px; font-weight: 500;
            padding: 3px 9px; border-radius: 20px;
            gap: 4px;
        }}
        .badge-blue   {{ background: #eff6ff; color: #1d4ed8; }}
        .badge-green  {{ background: #f0fdf4; color: #15803d; }}
        .badge-teal   {{ background: #ecfeff; color: #0e7490; }}

        /* ── RECENT LIST ── */
        .recent-list {{ display: flex; flex-direction: column; gap: 8px; }}
        .recent-item {{
            display: flex; align-items: center; gap: 14px;
            padding: 12px 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
        }}
        .ri-icon {{
            width: 34px; height: 34px; border-radius: 8px;
            background: #eff6ff;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; color: var(--accent);
            flex-shrink: 0;
        }}
        .ri-label {{ font-size: 13px; font-weight: 500; color: var(--text); }}
        .ri-sub   {{ font-size: 12px; color: var(--muted); }}

        /* ── UPLOAD ZONE ── */
        .upload-zone {{
            border: 2px dashed var(--border);
            border-radius: var(--radius-lg);
            padding: 2.5rem;
            text-align: center;
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 1rem;
            cursor: pointer;
            transition: border-color 0.15s, background 0.15s;
        }}
        .upload-zone:hover {{ border-color: var(--accent); background: #f0f7ff; }}
        .upload-zone i {{ font-size: 32px; color: #93c5fd; display: block; margin-bottom: 10px; }}
        .upload-zone strong {{ display: block; font-size: 14px; color: var(--text); margin-bottom: 4px; }}

        /* ── QUESTIONNAIRE ITEMS ── */
        .q-block {{
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 14px 16px;
            margin-bottom: 10px;
        }}
        .q-block label {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 500;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 7px;
        }}
        .q-block input {{
            width: 100%;
            padding: 9px 13px;
            font-family: 'DM Sans', sans-serif;
            font-size: 14px;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            background: var(--surface);
            color: var(--text);
            outline: none;
            transition: border-color 0.15s;
        }}
        .q-block input:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(37,99,235,0.08);
        }}

        /* ── ALERT ── */
        .alert {{
            padding: 12px 16px;
            border-radius: var(--radius);
            font-size: 13px;
            margin-bottom: 1.25rem;
            display: flex; align-items: center; gap: 10px;
        }}
        .alert-success {{ background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }}
        .alert-error   {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}
        .alert-info    {{ background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}

        .section-label {{
            font-size: 11px;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 10px;
        }}
        .divider {{ height: 1px; background: var(--border); margin: 1.5rem 0; }}
        .mono {{ font-family: 'DM Mono', monospace; }}
    </style>
</head>
<body>

<aside class="sidebar">
    <div class="sidebar-logo">
        <div class="logo-icon"><i class="ti ti-heartbeat" aria-hidden="true"></i></div>
        <div>
            <div class="logo-text">FHIR Questionnaire Tool</div>
            <div class="logo-sub">Prototyp</div>
        </div>
    </div>
    <div class="nav-section">
        <div class="nav-label">Navigation</div>
        {nav_html}
    </div>
    <div class="patient-card">
        <div class="pc-label">Active patient</div>
        <div class="pc-name">
            {patient_dot}
            {patient_info if active_patient else '<span style="color:rgba(255,255,255,0.3)">None selected</span>'}
        </div>
        {'<div style="font-size:11px;color:rgba(255,255,255,0.3);margin-top:3px;" class="mono">ID ' + str(active_patient) + '</div>' if active_patient else ''}
    </div>
</aside>

<main class="main">
    {content}
</main>

</body>
</html>"""


# ==========================
# DASHBOARD
# ==========================
@app.route("/")
def dashboard():
    content = f"""
    <div class="topbar">
        <div>
            <div class="page-heading">Dashboard</div>
            <div class="page-sub">FHIR Questionnaire Prototyp</div>
        </div>
    </div>

    <div class="action-grid">
        <a href="/create" class="action-card">
            <div class="ac-icon" style="background:#eff6ff;color:#1d4ed8;">
                <i class="ti ti-user-plus" aria-hidden="true"></i>
            </div>
            <div>
                <div class="ac-title">Create patient</div>
                <div class="ac-sub">Register a new patient</div>
            </div>
        </a>
        <a href="/select" class="action-card">
            <div class="ac-icon" style="background:#ecfeff;color:#0e7490;">
                <i class="ti ti-users" aria-hidden="true"></i>
            </div>
            <div>
                <div class="ac-title">Select patient</div>
                <div class="ac-sub">Set active patient by ID</div>
            </div>
        </a>
        <a href="/upload" class="action-card">
            <div class="ac-icon" style="background:#fefce8;color:#a16207;">
                <i class="ti ti-file-upload" aria-hidden="true"></i>
            </div>
            <div>
                <div class="ac-title">Upload questionnaire</div>
                <div class="ac-sub">Add a FHIR Questionnaire</div>
            </div>
        </a>
        <a href="/questionnaire" class="action-card">
            <div class="ac-icon" style="background:#fdf4ff;color:#7e22ce;">
                <i class="ti ti-clipboard-text" aria-hidden="true"></i>
            </div>
            <div>
                <div class="ac-title">Start questionnaire</div>
                <div class="ac-sub">Fill form for patient</div>
            </div>
        </a>
    </div>

    <div class="section-label">Recent activity</div>
    <div class="recent-list">
        <div class="recent-item">
            <div class="ri-icon"><i class="ti ti-clipboard-check" aria-hidden="true"></i></div>
            <div style="flex:1">
                <div class="ri-label">Questionnaire #1042</div>
                <div class="ri-sub">Response saved successfully</div>
            </div>
            <span class="badge badge-green"><i class="ti ti-check" style="font-size:11px;"></i> Saved</span>
        </div>
        <div class="recent-item">
            <div class="ri-icon"><i class="ti ti-user" aria-hidden="true"></i></div>
            <div style="flex:1">
                <div class="ri-label">Patient created</div>
                <div class="ri-sub">Anna Müller · ID 1000</div>
            </div>
            <span class="badge badge-blue">New</span>
        </div>
    </div>
    """
    return render_page("dashboard", content, "Dashboard")


# ==========================
# CREATE PATIENT
# ==========================
@app.route("/create", methods=["GET", "POST"])
def create_patient():
    global active_patient

    if request.method == "POST":
        given  = request.form["given"]
        family = request.form["family"]

        patient = {
            "resourceType": "Patient",
            "name": [{"given": [given], "family": family}]
        }

        r = requests.post(
            f"{FHIR_BASE}/Patient",
            headers={"Content-Type": "application/fhir+json"},
            json=patient
        )

        pid = r.json()["id"]
        active_patient = pid

        content = f"""
        <div class="topbar"><div>
            <div class="page-heading">Create patient</div>
        </div></div>
        <div class="alert alert-success">
            <i class="ti ti-circle-check" style="font-size:18px;"></i>
            Patient <strong>{given} {family}</strong> successfully created.
        </div>
        <div class="card" style="max-width:360px;">
            <div class="section-label">Patient details</div>
            <div style="display:flex;flex-direction:column;gap:8px;font-size:13px;">
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:var(--muted);">Name</span>
                    <span style="font-weight:500;">{given} {family}</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:var(--muted);">Patient ID</span>
                    <span class="mono" style="font-weight:500;">{pid}</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:var(--muted);">Status</span>
                    <span class="badge badge-green"><i class="ti ti-check" style="font-size:11px;"></i> Active</span>
                </div>
            </div>
        </div>
        <div style="margin-top:1.25rem;display:flex;gap:8px;">
            <a href="/" class="btn btn-ghost"><i class="ti ti-arrow-left" style="font-size:15px;"></i> Dashboard</a>
            <a href="/questionnaire" class="btn btn-primary"><i class="ti ti-clipboard-text" style="font-size:15px;"></i> Start questionnaire</a>
        </div>
        """
        return render_page("create", content, "Patient created")

    content = """
    <div class="topbar"><div>
        <div class="page-heading">Create patient</div>
        <div class="page-sub">Register a new FHIR Patient resource</div>
    </div></div>
    <div class="card form-wrap">
        <form method="post">
            <div class="form-group">
                <label>First name</label>
                <input name="given" placeholder="e.g. Anna" required>
            </div>
            <div class="form-group">
                <label>Last name</label>
                <input name="family" placeholder="e.g. Müller" required>
            </div>
            <div style="display:flex;gap:8px;margin-top:0.5rem;">
                <a href="/" class="btn btn-ghost">Cancel</a>
                <button type="submit" class="btn btn-primary">
                    <i class="ti ti-user-plus" style="font-size:15px;"></i> Create patient
                </button>
            </div>
        </form>
    </div>
    """
    return render_page("create", content, "Create patient")


# ==========================
# SELECT PATIENT
# ==========================
@app.route("/select", methods=["GET", "POST"])
def select_patient():
    global active_patient

    if request.method == "POST":
        active_patient = request.form["patient_id"]
        return redirect("/")

    content = """
    <div class="topbar"><div>
        <div class="page-heading">Select patient</div>
        <div class="page-sub">Set the active patient by FHIR ID</div>
    </div></div>
    <div class="card form-wrap">
        <form method="post">
            <div class="form-group">
                <label>Patient ID</label>
                <input name="patient_id" placeholder="e.g. 1000" required class="mono">
            </div>
            <div style="display:flex;gap:8px;margin-top:0.5rem;">
                <a href="/" class="btn btn-ghost">Cancel</a>
                <button type="submit" class="btn btn-primary">
                    <i class="ti ti-arrow-right" style="font-size:15px;"></i> Set active
                </button>
            </div>
        </form>
    </div>
    """
    return render_page("select", content, "Select patient")


# ==========================
# UPLOAD QUESTIONNAIRE
# ==========================
@app.route("/upload", methods=["GET", "POST"])
def upload_questionnaire():
    if request.method == "POST":
        file   = request.files["file"]
        q_json = json.load(file)

        r   = requests.post(
            f"{FHIR_BASE}/Questionnaire",
            headers={"Content-Type": "application/fhir+json"},
            json=q_json
        )
        qid = r.json()["id"]

        content = f"""
        <div class="topbar"><div>
            <div class="page-heading">Upload questionnaire</div>
        </div></div>
        <div class="alert alert-success">
            <i class="ti ti-circle-check" style="font-size:18px;"></i>
            Questionnaire successfully uploaded.
        </div>
        <div class="card" style="max-width:360px;">
            <div class="section-label">Questionnaire details</div>
            <div style="display:flex;justify-content:space-between;font-size:13px;">
                <span style="color:var(--muted);">FHIR ID</span>
                <span class="mono" style="font-weight:500;">{qid}</span>
            </div>
        </div>
        <div style="margin-top:1.25rem;display:flex;gap:8px;">
            <a href="/" class="btn btn-ghost"><i class="ti ti-arrow-left" style="font-size:15px;"></i> Dashboard</a>
            <a href="/questionnaire" class="btn btn-primary">
                <i class="ti ti-clipboard-text" style="font-size:15px;"></i> Start questionnaire
            </a>
        </div>
        """
        return render_page("upload", content, "Uploaded")

    content = """
    <div class="topbar"><div>
        <div class="page-heading">Upload questionnaire</div>
        <div class="page-sub">Upload a FHIR Questionnaire JSON file</div>
    </div></div>
    <div class="card form-wrap">
        <form method="post" enctype="multipart/form-data">
            <div class="upload-zone" onclick="document.getElementById('ffile').click()">
                <i class="ti ti-file-upload" aria-hidden="true"></i>
                <strong>Click to select a file</strong>
                Questionnaire JSON (.json)
            </div>
            <input type="file" id="ffile" name="file" accept=".json"
                   style="display:none;"
                   onchange="document.getElementById('fname').textContent = this.files[0]?.name || ''">
            <div id="fname" style="font-size:12px;color:var(--muted);margin-bottom:1rem;min-height:16px;"></div>
            <div style="display:flex;gap:8px;">
                <a href="/" class="btn btn-ghost">Cancel</a>
                <button type="submit" class="btn btn-primary">
                    <i class="ti ti-upload" style="font-size:15px;"></i> Upload
                </button>
            </div>
        </form>
    </div>
    """
    return render_page("upload", content, "Upload questionnaire")


# ==========================
# START QUESTIONNAIRE (pick ID)
# ==========================
@app.route("/questionnaire", methods=["GET", "POST"])
def start_questionnaire():
    if request.method == "POST":
        qid = request.form["qid"]
        return redirect(f"/questionnaire/{qid}")

    content = """
    <div class="topbar"><div>
        <div class="page-heading">Start questionnaire</div>
        <div class="page-sub">Enter the FHIR Questionnaire ID to open</div>
    </div></div>
    <div class="card form-wrap">
        <form method="post">
            <div class="form-group">
                <label>Questionnaire ID</label>
                <input name="qid" placeholder="e.g. 1042" required class="mono">
            </div>
            <div style="display:flex;gap:8px;margin-top:0.5rem;">
                <a href="/" class="btn btn-ghost">Cancel</a>
                <button type="submit" class="btn btn-primary">
                    <i class="ti ti-arrow-right" style="font-size:15px;"></i> Open
                </button>
            </div>
        </form>
    </div>
    """
    return render_page("questionnaire", content, "Start questionnaire")


# ==========================
# QUESTIONNAIRE RENDERING
# ==========================
@app.route("/questionnaire/<qid>", methods=["GET", "POST"])
def questionnaire(qid):
    global active_patient

    if not active_patient:
        return redirect("/select")

    # ── GET → $populate ──
    if request.method == "GET":
        parameters = {
            "resourceType": "Parameters",
            "parameter": [{
                "name": "subject",
                "valueReference": {"reference": f"Patient/{active_patient}"}
            }]
        }

        r = requests.post(
            f"{FHIR_BASE}/Questionnaire/{qid}/$populate",
            headers={"Content-Type": "application/fhir+json"},
            json=parameters
        )

        if not r.ok:
            content = f"""
            <div class="topbar"><div><div class="page-heading">Questionnaire</div></div></div>
            <div class="alert alert-error">
                <i class="ti ti-alert-circle" style="font-size:18px;"></i>
                $populate failed: {r.status_code}
            </div>
            <a href="/" class="btn btn-ghost"><i class="ti ti-arrow-left" style="font-size:15px;"></i> Back</a>
            """
            return render_page("questionnaire", content, "Error")

        qr    = r.json()
        items = qr.get("item", [])

        # Build form
        fields_html = ""
        populated_count = 0
        for item in items:
            value = ""
            is_populated = False
            if "answer" in item and item["answer"]:
                answer = item["answer"][0]
                value  = str(list(answer.values())[0])
                is_populated = True
                populated_count += 1

            input_type = "text"
            if item.get("type") == "date":
                input_type = "date"
            elif item.get("type") == "integer":
                input_type = "number"

            badge = '<span class="badge badge-teal" style="font-size:10px;padding:2px 7px;">populated</span>' if is_populated else ""
            fields_html += f"""
            <div class="q-block">
                <label>{item.get('text', item['linkId'])} {badge}</label>
                <input type="{input_type}" name="{item['linkId']}" value="{value}" placeholder="Enter value...">
            </div>"""

        content = f"""
        <div class="topbar">
            <div>
                <div class="page-heading">Questionnaire <span class="mono" style="font-size:18px;">#{qid}</span></div>
                <div class="page-sub">Patient ID <span class="mono">{active_patient}</span></div>
            </div>
            <span class="badge badge-teal" style="font-size:12px;padding:5px 12px;">
                <i class="ti ti-wand" style="font-size:13px;"></i>
                {populated_count} field(s) auto-populated
            </span>
        </div>
        <form method="post">
            {fields_html}
            <div style="display:flex;gap:8px;margin-top:1.25rem;">
                <a href="/" class="btn btn-ghost"><i class="ti ti-x" style="font-size:15px;"></i> Cancel</a>
                <button type="submit" class="btn btn-primary">
                    <i class="ti ti-device-floppy" style="font-size:15px;"></i> Save response
                </button>
            </div>
        </form>
        """
        return render_page("questionnaire", content, f"Questionnaire #{qid}")

    # ── POST → save ──
    items = []
    for key in request.form:
        value = request.form.get(key)
        items.append({
            "linkId": key,
            "answer": [{"valueString": value}]
        })

    qr = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "questionnaire": f"{FHIR_BASE}/Questionnaire/{qid}",
        "subject": {"reference": f"Patient/{active_patient}"},
        "item": items
    }

    save = requests.post(
        f"{FHIR_BASE}/QuestionnaireResponse",
        headers={"Content-Type": "application/fhir+json"},
        json=qr
    )

    if save.ok:
        saved_id = save.json().get("id", "")
        content = f"""
        <div class="topbar"><div>
            <div class="page-heading">Response saved</div>
        </div></div>
        <div class="alert alert-success">
            <i class="ti ti-circle-check" style="font-size:18px;"></i>
            QuestionnaireResponse successfully saved to FHIR server.
        </div>
        <div class="card" style="max-width:360px;">
            <div class="section-label">Details</div>
            <div style="display:flex;flex-direction:column;gap:8px;font-size:13px;">
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:var(--muted);">Response ID</span>
                    <span class="mono" style="font-weight:500;">{saved_id}</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:var(--muted);">Questionnaire</span>
                    <span class="mono">{qid}</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="color:var(--muted);">Patient</span>
                    <span class="mono">{active_patient}</span>
                </div>
            </div>
        </div>
        <div style="margin-top:1.25rem;display:flex;gap:8px;">
            <a href="/" class="btn btn-ghost"><i class="ti ti-arrow-left" style="font-size:15px;"></i> Dashboard</a>
            <a href="/questionnaire/{qid}" class="btn btn-primary">
                <i class="ti ti-refresh" style="font-size:15px;"></i> Open again
            </a>
        </div>
        """
        return render_page("questionnaire", content, "Saved")
    else:
        content = f"""
        <div class="topbar"><div><div class="page-heading">Error</div></div></div>
        <div class="alert alert-error">
            <i class="ti ti-alert-circle" style="font-size:18px;"></i>
            Save failed: {save.status_code}
        </div>
        <a href="/questionnaire/{qid}" class="btn btn-ghost">
            <i class="ti ti-arrow-left" style="font-size:15px;"></i> Back
        </a>
        """
        return render_page("questionnaire", content, "Error")


# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(debug=True)