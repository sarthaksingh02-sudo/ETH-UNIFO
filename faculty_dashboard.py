"""
Vidwan Faculty Manager & Pipeline Web Dashboard
================================================
A modern, zero-dependency-on-MS-Office web application to manage faculty names
in 'faculty_input.xlsx' and execute the Vidwan publication extraction pipeline
with live log streaming.

Usage:
    python faculty_dashboard.py
"""

import os
import sys
import json
import time
import subprocess
import threading
import queue
import webbrowser
from flask import Flask, request, jsonify, render_template_string, Response, send_file
import pandas as pd

app = Flask(__name__)

EXCEL_FILE = "faculty_input.xlsx"
OUTPUT_FILE = "faculty_publications_output.xlsx"
COLUMN_NAME = "Faculty Name"

# Queue for real-time log streaming
log_queue = queue.Queue()
pipeline_running = False


def get_excel_path() -> str:
    return os.path.abspath(EXCEL_FILE)


def load_faculty_names() -> list[str]:
    path = get_excel_path()
    if not os.path.exists(path):
        df = pd.DataFrame(columns=[COLUMN_NAME])
        df.to_excel(path, index=False)
        return []
    try:
        df = pd.read_excel(path)
        col = None
        for c in df.columns:
            if any(k in str(c).lower() for k in ["faculty", "name", "author"]):
                col = c
                break
        if not col and len(df.columns) > 0:
            col = df.columns[0]
        if col:
            return [str(x).strip() for x in df[col].dropna() if str(x).strip()]
        return []
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return []


def save_faculty_names(names: list[str]) -> list[str]:
    path = get_excel_path()
    seen = set()
    cleaned = []
    for n in names:
        val = str(n).strip()
        if val and val not in seen:
            seen.add(val)
            cleaned.append(val)
    df = pd.DataFrame({COLUMN_NAME: cleaned})
    df.to_excel(path, index=False)
    return cleaned


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vidwan Faculty Publication Intelligence</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --card-bg: #131b2e;
            --card-border: #1e293b;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --success: #10b981;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #6366f1;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        body {
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem 1.5rem;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--card-border);
            flex-wrap: wrap;
            gap: 1rem;
        }

        .brand-title {
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .badge-inst {
            font-size: 0.8rem;
            background: rgba(99, 102, 241, 0.2);
            color: #818cf8;
            padding: 0.3rem 0.8rem;
            border-radius: 9999px;
            border: 1px solid rgba(99, 102, 241, 0.4);
            font-weight: 500;
        }

        .grid-layout {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        @media (max-width: 860px) {
            .grid-layout {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.2rem;
        }

        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .form-group {
            margin-bottom: 1rem;
        }

        label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
        }

        input[type="text"], textarea {
            width: 100%;
            padding: 0.75rem 1rem;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            color: var(--text-main);
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        input[type="text"]:focus, textarea:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.7rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            border: none;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
        }

        .btn-primary {
            background: var(--primary);
            color: #fff;
        }
        .btn-primary:hover {
            background: var(--primary-hover);
        }

        .btn-success {
            background: var(--success);
            color: #fff;
        }
        .btn-success:hover {
            background: #059669;
        }

        .btn-danger {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .btn-danger:hover {
            background: var(--danger);
            color: #fff;
        }

        .btn-outline {
            background: transparent;
            border: 1px solid #475569;
            color: var(--text-muted);
        }
        .btn-outline:hover {
            border-color: var(--text-main);
            color: var(--text-main);
        }

        .btn-sm {
            padding: 0.35rem 0.7rem;
            font-size: 0.8rem;
        }

        .badge-count {
            background: #1e293b;
            color: #38bdf8;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* Search input */
        .search-box {
            margin-bottom: 1rem;
        }

        /* Table */
        .table-wrap {
            max-height: 380px;
            overflow-y: auto;
            border: 1px solid #1e293b;
            border-radius: 8px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            background: #1e293b;
            padding: 0.8rem 1rem;
            font-size: 0.85rem;
            color: var(--text-muted);
            font-weight: 600;
            position: sticky;
            top: 0;
        }

        td {
            padding: 0.8rem 1rem;
            font-size: 0.9rem;
            border-bottom: 1px solid #1e293b;
            color: #e2e8f0;
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }

        /* Pipeline Console */
        .console-box {
            background: #060911;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
            color: #38bdf8;
            height: 220px;
            overflow-y: auto;
            white-space: pre-wrap;
            margin-top: 1rem;
        }

        .action-row {
            display: flex;
            gap: 0.8rem;
            align-items: center;
            margin-top: 1rem;
            flex-wrap: wrap;
        }

        /* Toast notifications */
        #toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            padding: 0.9rem 1.4rem;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 500;
            display: none;
            z-index: 1000;
            box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        }
        .toast-success { background: #065f46; color: #a7f3d0; border: 1px solid #059669; }
        .toast-error { background: #7f1d1d; color: #fecaca; border: 1px solid #dc2626; }
    </style>
</head>
<body>

<div class="container">
    <header>
        <div>
            <div class="brand-title">
                <span>🎓 Vidwan Faculty Intelligence Dashboard</span>
            </div>
            <p style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.3rem;">
                Manage faculty input for GD Goenka University & run publication bibliometrics without Microsoft Excel
            </p>
        </div>
        <div style="display: flex; gap: 0.8rem; align-items: center;">
            <span class="badge-inst">🏛 GD Goenka University</span>
            <a href="/api/download-input" class="btn btn-outline btn-sm">📥 Download faculty_input.xlsx</a>
        </div>
    </header>

    <div class="grid-layout">
        <!-- Add Faculty Panel -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">➕ Add Faculty Member</span>
                <span style="font-size: 0.8rem; color: var(--text-muted);">Auto-saves to Excel</span>
            </div>

            <div class="form-group">
                <label for="singleName">Single Faculty Name</label>
                <div style="display: flex; gap: 0.5rem;">
                    <input type="text" id="singleName" placeholder="e.g. Dr. Firstname Lastname" onkeydown="if(event.key==='Enter') addSingleFaculty()">
                    <button class="btn btn-primary" onclick="addSingleFaculty()">Add</button>
                </div>
            </div>

            <hr style="border: 0; border-top: 1px dashed var(--card-border); margin: 1.5rem 0;">

            <div class="form-group">
                <label for="bulkNames">Bulk Paste Faculty Names (one per line or comma-separated)</label>
                <textarea id="bulkNames" rows="5" placeholder="Faculty Member 1&#10;Faculty Member 2&#10;Faculty Member 3"></textarea>
            </div>
            <button class="btn btn-outline" style="width: 100%;" onclick="addBulkFaculty()">📥 Add All to Faculty List</button>
        </div>

        <!-- Faculty List Panel -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">
                    📋 Registered Faculty
                    <span class="badge-count" id="facultyCount">0</span>
                </span>
                <button class="btn btn-danger btn-sm" onclick="clearAllFaculty()">Clear All</button>
            </div>

            <div class="search-box">
                <input type="text" id="searchFilter" placeholder="🔍 Filter faculty names..." oninput="filterFacultyTable()">
            </div>

            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50px;">#</th>
                            <th>Faculty Name</th>
                            <th style="width: 80px; text-align: center;">Action</th>
                        </tr>
                    </thead>
                    <tbody id="facultyTableBody">
                        <tr><td colspan="3" style="text-align:center; color:var(--text-muted);">Loading faculty...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Pipeline Execution Card -->
    <div class="card">
        <div class="card-header">
            <div>
                <span class="card-title">⚡ Run Vidwan Extraction & Metrics Pipeline</span>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.3rem;">
                    Searches Vidwan portal, scrapes qualifications & publication DOIs, calculates Scopus Quartiles, H-Index & generates styled Excel.
                </p>
            </div>
            <div id="pipelineStatusBadge"></div>
        </div>

        <div class="action-row">
            <button class="btn btn-success" id="runPipelineBtn" onclick="runPipeline()">
                ▶ Launch Extraction Pipeline
            </button>
            <a href="/api/download-output" class="btn btn-outline" id="downloadOutputBtn">
                📊 Download faculty_publications_output.xlsx
            </a>
            <span id="pipelineIndicator" style="font-size: 0.85rem; color: #38bdf8; display: none;">
                ⏳ Pipeline running... Output streaming below.
            </span>
        </div>

        <div class="console-box" id="consoleBox">Console ready. Click "Launch Extraction Pipeline" to begin.</div>
    </div>
</div>

<div id="toast"></div>

<script>
    let allFaculty = [];

    function showToast(msg, isError = false) {
        const t = document.getElementById('toast');
        t.innerText = msg;
        t.className = isError ? 'toast-error' : 'toast-success';
        t.style.display = 'block';
        setTimeout(() => { t.style.display = 'none'; }, 3500);
    }

    async function loadFaculty() {
        try {
            const res = await fetch('/api/faculty');
            const data = await res.json();
            allFaculty = data.faculty || [];
            renderTable(allFaculty);
        } catch (e) {
            showToast('Failed to load faculty list', true);
        }
    }

    function renderTable(list) {
        document.getElementById('facultyCount').innerText = list.length;
        const tbody = document.getElementById('facultyTableBody');
        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--text-muted); padding: 1.5rem;">No faculty registered yet. Add some on the left!</td></tr>';
            return;
        }

        tbody.innerHTML = list.map((name, idx) => `
            <tr>
                <td style="color: var(--text-muted);">${idx + 1}</td>
                <td style="font-weight: 500;">
                    ${escapeHtml(name)}
                    <a href="https://vidwan.inflibnet.ac.in/profiles/init-filters?q=${encodeURIComponent(name + ' GD Goenka University')}" target="_blank" style="font-size:0.75rem; color:#60a5fa; margin-left: 0.5rem; text-decoration:none;">↗ Vidwan</a>
                </td>
                <td style="text-align: center;">
                    <button class="btn btn-danger btn-sm" onclick="deleteFaculty('${encodeURIComponent(name)}')">✕</button>
                </td>
            </tr>
        `).join('');
    }

    function escapeHtml(str) {
        return str.replace(/[&<>"']/g, m => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]));
    }

    function filterFacultyTable() {
        const query = document.getElementById('searchFilter').value.toLowerCase().trim();
        const filtered = allFaculty.filter(name => name.toLowerCase().includes(query));
        renderTable(filtered);
    }

    async function addSingleFaculty() {
        const input = document.getElementById('singleName');
        const name = input.value.trim();
        if (!name) return;
        try {
            const res = await fetch('/api/faculty/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ names: [name] })
            });
            const data = await res.json();
            if (data.success) {
                input.value = '';
                showToast(`Added: ${name}`);
                loadFaculty();
            } else {
                showToast(data.message || 'Already exists', true);
            }
        } catch (e) {
            showToast('Error adding faculty', true);
        }
    }

    async function addBulkFaculty() {
        const area = document.getElementById('bulkNames');
        const raw = area.value.trim();
        if (!raw) return;
        const names = raw.replace(/,/g, '\\n').split('\\n').map(x => x.trim()).filter(x => x.length > 0);
        if (names.length === 0) return;

        try {
            const res = await fetch('/api/faculty/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ names: names })
            });
            const data = await res.json();
            if (data.success) {
                area.value = '';
                showToast(`Added ${data.added_count} faculty members!`);
                loadFaculty();
            } else {
                showToast(data.message, true);
            }
        } catch (e) {
            showToast('Error adding bulk faculty', true);
        }
    }

    async function deleteFaculty(encodedName) {
        const name = decodeURIComponent(encodedName);
        try {
            const res = await fetch('/api/faculty/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name })
            });
            const data = await res.json();
            if (data.success) {
                showToast(`Removed: ${name}`);
                loadFaculty();
            }
        } catch (e) {
            showToast('Error deleting faculty', true);
        }
    }

    async function clearAllFaculty() {
        if (!confirm('Are you sure you want to clear all registered faculty?')) return;
        try {
            const res = await fetch('/api/faculty/clear', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Cleared all faculty.');
                loadFaculty();
            }
        } catch (e) {
            showToast('Error clearing faculty', true);
        }
    }

    // --- Pipeline Execution with Live SSE Logs ---
    let eventSource = null;

    async function runPipeline() {
        const btn = document.getElementById('runPipelineBtn');
        const ind = document.getElementById('pipelineIndicator');
        const box = document.getElementById('consoleBox');

        btn.disabled = true;
        btn.innerText = '⏳ Processing...';
        ind.style.display = 'inline';
        box.innerText = 'Initializing extraction pipeline...\\n';

        try {
            const res = await fetch('/api/run-pipeline', { method: 'POST' });
            const data = await res.json();
            if (!data.success) {
                showToast(data.message, true);
                btn.disabled = false;
                btn.innerText = '▶ Launch Extraction Pipeline';
                ind.style.display = 'none';
                return;
            }

            // Connect to SSE log stream
            if (eventSource) eventSource.close();
            eventSource = new EventSource('/api/pipeline-logs');
            eventSource.onmessage = function(event) {
                if (event.data === '[[PIPELINE_COMPLETE]]') {
                    eventSource.close();
                    btn.disabled = false;
                    btn.innerText = '▶ Launch Extraction Pipeline';
                    ind.style.display = 'none';
                    box.innerText += '\\n=========================================\\nPipeline finished! Output Excel generated.\\n=========================================\\n';
                    box.scrollTop = box.scrollHeight;
                    showToast('Extraction pipeline completed successfully!');
                } else {
                    box.innerText += event.data + '\\n';
                    box.scrollTop = box.scrollHeight;
                }
            };
            eventSource.onerror = function() {
                eventSource.close();
                btn.disabled = false;
                btn.innerText = '▶ Launch Extraction Pipeline';
                ind.style.display = 'none';
            };

        } catch (e) {
            showToast('Failed to start pipeline', true);
            btn.disabled = false;
            btn.innerText = '▶ Launch Extraction Pipeline';
            ind.style.display = 'none';
        }
    }

    // Initialize
    loadFaculty();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/faculty", methods=["GET"])
def get_faculty():
    names = load_faculty_names()
    return jsonify({"faculty": names})


@app.route("/api/faculty/add", methods=["POST"])
def add_faculty_api():
    data = request.json or {}
    new_names = data.get("names", [])
    if not new_names:
        return jsonify({"success": False, "message": "No names provided"}), 400

    current = load_faculty_names()
    added = 0
    for n in new_names:
        clean = str(n).strip()
        if clean and clean not in current:
            current.append(clean)
            added += 1

    save_faculty_names(current)
    return jsonify({"success": True, "added_count": added, "total": len(current)})


@app.route("/api/faculty/delete", methods=["POST"])
def delete_faculty_api():
    data = request.json or {}
    target = data.get("name", "").strip()
    current = load_faculty_names()
    matched = [x for x in current if x.lower() == target.lower()]
    if not matched:
        return jsonify({"success": False, "message": "Faculty not found"}), 404

    current.remove(matched[0])
    save_faculty_names(current)
    return jsonify({"success": True, "total": len(current)})


@app.route("/api/faculty/clear", methods=["POST"])
def clear_faculty_api():
    save_faculty_names([])
    return jsonify({"success": True, "total": 0})


@app.route("/api/download-input", methods=["GET"])
def download_input():
    path = get_excel_path()
    if not os.path.exists(path):
        save_faculty_names([])
    return send_file(path, as_attachment=True, download_name="faculty_input.xlsx")


@app.route("/api/download-output", methods=["GET"])
def download_output():
    path = os.path.abspath(OUTPUT_FILE)
    if not os.path.exists(path):
        return jsonify({"error": "Output report not generated yet. Run pipeline first!"}), 404
    return send_file(path, as_attachment=True, download_name="faculty_publications_output.xlsx")


@app.route("/api/publications/clear", methods=["POST"])
def clear_publications_api():
    try:
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        return jsonify({"success": True, "message": "Cleared publication output report"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def run_pipeline_worker():
    global pipeline_running
    pipeline_running = True
    try:
        script_path = os.path.abspath("fetch_faculty_publications.py")
        cmd = [sys.executable, "-u", script_path, "--input", EXCEL_FILE, "--output", OUTPUT_FILE]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        for line in iter(proc.stdout.readline, ""):
            clean_line = line.rstrip()
            if clean_line:
                log_queue.put(clean_line)

        proc.stdout.close()
        proc.wait()
    except Exception as e:
        log_queue.put(f"[ERROR]: {e}")
    finally:
        pipeline_running = False
        log_queue.put("[[PIPELINE_COMPLETE]]")


@app.route("/api/run-pipeline", methods=["POST"])
def run_pipeline_api():
    global pipeline_running
    if pipeline_running:
        return jsonify({"success": False, "message": "Pipeline is already running"}), 400

    # Clear log queue
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break

    thread = threading.Thread(target=run_pipeline_worker, daemon=True)
    thread.start()
    return jsonify({"success": True, "message": "Pipeline started"})


@app.route("/api/pipeline-logs")
def stream_pipeline_logs():
    def event_stream():
        while True:
            try:
                line = log_queue.get(timeout=25)
                yield f"data: {line}\n\n"
                if line == "[[PIPELINE_COMPLETE]]":
                    break
            except queue.Empty:
                yield ": keep-alive\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


def main():
    port = 5000
    url = f"http://127.0.0.1:{port}"
    print("\n" + "=" * 60)
    print("   VIDWAN FACULTY INTELLIGENCE WEB DASHBOARD")
    print("=" * 60)
    print(f" * Dashboard URL: {url}")
    print(f" * Input File:    {os.path.abspath(EXCEL_FILE)}")
    print(f" * Output Report: {os.path.abspath(OUTPUT_FILE)}")
    print(" * Press Ctrl+C in terminal to stop server.")
    print("=" * 60 + "\n")

    # Automatically open default browser after a brief delay
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    # Run Flask server
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
