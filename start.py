"""
GD GOENKA UNIVERSITY - VIDWAN FACULTY RESEARCH INTELLIGENCE
Unified Single-Trigger Launcher & Full-Stack Backend
============================================================
Launches the full-stack system:
- High-performance Flask REST API & SSE event stream
- Apple-inspired React Frontend (Officer Blue & White UI)
- OpenXML Native Hyperlink Engine & Bibliometrics Pipeline
- Automatic Port Conflict Resolution & Browser Auto-Launch

Usage:
    python start.py
"""

import os
import sys
import json
import time
import socket
import glob
import re
import subprocess
import threading
import queue
import webbrowser
from flask import Flask, request, jsonify, send_from_directory, send_file, Response
import pandas as pd
import openpyxl

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIST_DIR = os.path.join(BASE_DIR, "client", "dist")
EXCEL_INPUT = os.path.join(BASE_DIR, "faculty_input.xlsx")
EXCEL_OUTPUT = os.path.join(BASE_DIR, "faculty_publications_output.xlsx")
COLUMN_NAME = "Faculty Name"

app = Flask(__name__, static_folder=None)

# Thread-safe queue for real-time SSE logs
log_queue = queue.Queue()
pipeline_lock = threading.Lock()
pipeline_running = False


def find_latest_output_file() -> str | None:
    """Finds the most recent publication output file (including fallback numbered files)."""
    candidates = []
    if os.path.exists(EXCEL_OUTPUT):
        candidates.append((os.path.getmtime(EXCEL_OUTPUT), EXCEL_OUTPUT))
    
    # Also look for numbered variants like 'faculty_publications_output (3).xlsx'
    pattern = os.path.join(BASE_DIR, "faculty_publications_output*.xlsx")
    for f in glob.glob(pattern):
        if os.path.isfile(f):
            candidates.append((os.path.getmtime(f), f))
            
    if not candidates:
        return None
    # Sort by modification time descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def is_port_available(port: int) -> bool:
    """Checks if a local TCP port is free to bind."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except socket.error:
            return False


def get_available_port(start_port: int = 5000) -> int:
    """Finds an available port starting from start_port."""
    ports_to_try = [5000, 5050, 5051, 5052, 8000, 8080, 8888]
    for p in ports_to_try:
        if is_port_available(p):
            return p
    # Fallback to any random open port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def load_faculty_names() -> list[str]:
    """Reads faculty names from faculty_input.xlsx safely."""
    if not os.path.exists(EXCEL_INPUT):
        df = pd.DataFrame({COLUMN_NAME: ["Faculty Member 1", "Faculty Member 2", "Faculty Member 3"]})
        df.to_excel(EXCEL_INPUT, index=False)
        return ["Faculty Member 1", "Faculty Member 2", "Faculty Member 3"]
    try:
        df = pd.read_excel(EXCEL_INPUT)
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
        print(f"[Error loading faculty input]: {e}")
        return []


def save_faculty_names(names: list[str]) -> list[str]:
    """Saves cleaned faculty names to faculty_input.xlsx."""
    seen = set()
    cleaned = []
    for n in names:
        val = str(n).strip()
        if val and val not in seen:
            seen.add(val)
            cleaned.append(val)
    df = pd.DataFrame({COLUMN_NAME: cleaned})
    df.to_excel(EXCEL_INPUT, index=False)
    return cleaned


# ==========================================
# Static Files & React Frontend Delivery
# ==========================================

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path):
    """Serves the React Vite SPA and static assets from client/dist."""
    # Check if the requested file exists in dist
    full_path = os.path.join(CLIENT_DIST_DIR, path)
    if path and os.path.exists(full_path) and os.path.isfile(full_path):
        return send_from_directory(CLIENT_DIST_DIR, path)
    
    # Specific logo fallback
    if path in ["logo.png", "image.png"]:
        local_logo = os.path.join(BASE_DIR, "image.png")
        if os.path.exists(local_logo):
            return send_file(local_logo, mimetype="image/png")

    # Serve index.html for client-side routing
    index_file = os.path.join(CLIENT_DIST_DIR, "index.html")
    if os.path.exists(index_file):
        return send_from_directory(CLIENT_DIST_DIR, "index.html")

    return (
        "<h2>Frontend bundle not found. Please run 'npm run build' inside client/</h2>",
        404,
    )


# ==========================================
# REST API Endpoints
# ==========================================

@app.route("/api/faculty", methods=["GET"])
def get_faculty_api():
    """Returns the list of faculty currently registered in Excel."""
    names = load_faculty_names()
    return jsonify({"faculty": names, "total": len(names)})


@app.route("/api/faculty/add", methods=["POST"])
def add_faculty_api():
    """Adds one or more faculty names to the Excel sheet."""
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
    """Removes a faculty name from the Excel sheet."""
    data = request.json or {}
    target = data.get("name", "").strip()
    current = load_faculty_names()
    matched = [x for x in current if x.lower() == target.lower()]
    if not matched:
        return jsonify({"success": False, "message": "Faculty member not found"}), 404

    current.remove(matched[0])
    save_faculty_names(current)
    return jsonify({"success": True, "total": len(current)})


@app.route("/api/faculty/clear", methods=["POST"])
def clear_faculty_api():
    """Clears all faculty names from the Excel sheet."""
    save_faculty_names([])
    return jsonify({"success": True, "total": 0})


@app.route("/api/download-input", methods=["GET"])
def download_input():
    """Allows direct download of the faculty_input.xlsx file."""
    if not os.path.exists(EXCEL_INPUT):
        save_faculty_names([])
    return send_file(EXCEL_INPUT, as_attachment=True, download_name="faculty_input.xlsx")


@app.route("/api/download-output", methods=["GET"])
def download_output():
    """Allows direct download of the latest generated publications report."""
    latest_file = find_latest_output_file()
    if not latest_file or not os.path.exists(latest_file):
        return jsonify({"error": "Output report not generated yet. Run pipeline first!"}), 404
    return send_file(latest_file, as_attachment=True, download_name=os.path.basename(latest_file))


@app.route("/api/publications/clear", methods=["POST"])
def clear_publications_api():
    """
    Clears all generated publication output workbooks and resets the report.
    Returns confirmation of deleted files.
    """
    try:
        deleted_files = []
        pattern = os.path.join(BASE_DIR, "faculty_publications_output*.xlsx")
        for f in glob.glob(pattern):
            if os.path.isfile(f):
                try:
                    os.remove(f)
                    deleted_files.append(os.path.basename(f))
                except Exception as ex:
                    print(f"[Warning] Could not remove {f}: {ex}")

        return jsonify({
            "success": True,
            "message": "All publication records and generated workbooks cleared.",
            "deleted_files": deleted_files
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to clear publications: {e}"}), 500


@app.route("/api/system-info", methods=["GET"])
def system_info_api():
    """System information & engineering signature."""
    return jsonify({
        "platform": "GD Goenka University Vidwan Research Intelligence Platform",
        "version": "2.4.0-production",
        "system_engineer": "Sarthak Singh- 3096-2023-27",
        "signature": "Sarthak Singh- 3096-2023-27"
    })


@app.route("/api/publications-preview", methods=["GET"])
def get_publications_preview():
    """
    Parses the generated Excel report using openpyxl, extracting cell values
    and resolving native hyperlinks and formula URLs for interactive preview.
    """
    latest_file = find_latest_output_file()
    if not latest_file or not os.path.exists(latest_file):
        return jsonify({"records": [], "message": "No publication output generated yet."})

    try:
        wb = openpyxl.load_workbook(latest_file, data_only=False, read_only=False)
        ws = wb.active
        
        headers = [str(ws.cell(1, col).value or "").strip() for col in range(1, ws.max_column + 1)]
        
        # Header mapping to clean JSON keys
        key_map = {
            "Faculty Name": "Faculty_Name",
            "Qualifications": "Qualifications",
            "Vidwan Profile Link": "Vidwan_Profile_Link",
            "Article Title": "Article_Title",
            "Authors & Affiliation": "Authors_and_Affiliations",
            "Journal Name": "Journal_Name",
            "ISSN": "ISSN",
            "Year": "Year",
            "Month": "Month",
            "Vol": "Volume",
            "Issue": "Issue",
            "Page No.": "Page_No",
            "Journal Homepage": "Journal_Homepage",
            "Indexing Status (Scopus + SCI/SCIE)": "Indexing_Status",
            "Scopus Quartile (Q1-Q4)": "Scopus_Quartile",
            "Journal H-Index": "Journal_H_Index",
            "Article Citations": "Article_Citations",
            "Clarivate MJL Proof (SCI/SCIE)": "Clarivate_MJL_Proof_Link",
            "Scopus Proof Link": "Scopus_Proof_Link",
            "SCImago Proof Link": "SCImago_Proof_Link",
            "Article DOI": "DOI",
            "Original Input Link": "Input_URL",
            "Status": "Fetch_Status"
        }

        records = []
        for row_idx in range(2, ws.max_row + 1):
            row_data = {}
            for col_idx, raw_header in enumerate(headers, start=1):
                clean_key = key_map.get(raw_header, raw_header.replace(" ", "_"))
                cell = ws.cell(row_idx, col_idx)
                
                # Check for native hyperlink target
                link_target = cell.hyperlink.target if cell.hyperlink else None
                cell_val = cell.value

                # Parse formula hyperlinks if present in older files
                if isinstance(cell_val, str) and cell_val.startswith("=HYPERLINK("):
                    match = re.search(r'=HYPERLINK\("([^"]+)"(?:,\s*"([^"]+)")?\)', cell_val, re.IGNORECASE)
                    if match:
                        link_target = match.group(1)
                        cell_val = match.group(2) or match.group(1)

                # Assign appropriate value based on whether it is a link field
                if "Link" in clean_key or "Homepage" in clean_key:
                    row_data[clean_key] = link_target or (str(cell_val) if str(cell_val).startswith("http") else "")
                elif clean_key == "DOI":
                    row_data["DOI"] = cell_val if cell_val else "-"
                    row_data["DOI_Link"] = link_target or (f"https://doi.org/{cell_val}" if cell_val and cell_val != "-" else "")
                else:
                    row_data[clean_key] = cell_val if cell_val is not None else "-"

            records.append(row_data)

        wb.close()
        return jsonify({
            "source_file": os.path.basename(latest_file),
            "total_records": len(records),
            "records": records
        })
    except Exception as e:
        print(f"[Error parsing publications report]: {e}")
        return jsonify({"records": [], "error": str(e)}), 500


# ==========================================
# Pipeline Execution & SSE Streaming
# ==========================================

def run_pipeline_worker(institution="GD Goenka University", delay=0.5):
    """Background worker executing fetch_faculty_publications.py with live logging."""
    global pipeline_running
    try:
        script_path = os.path.join(BASE_DIR, "fetch_faculty_publications.py")
        cmd = [
            sys.executable,
            "-u",
            script_path,
            "--input", EXCEL_INPUT,
            "--output", EXCEL_OUTPUT,
            "--institution", institution,
            "--delay", str(delay)
        ]

        log_queue.put(f"[START] Executing extraction engine for: {institution}")
        log_queue.put(f"[COMMAND] {' '.join(cmd)}\n")

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

        if proc.returncode == 0:
            log_queue.put("\n[SUCCESS] Pipeline completed successfully!")
        else:
            log_queue.put(f"\n[WARNING] Process terminated with code {proc.returncode}")

    except Exception as e:
        log_queue.put(f"\n[ERROR] Pipeline exception: {e}")
    finally:
        with pipeline_lock:
            pipeline_running = False
        log_queue.put("[[PIPELINE_COMPLETE]]")


@app.route("/api/run-pipeline", methods=["POST"])
def run_pipeline_api():
    """Starts the publication extraction pipeline in a background thread."""
    global pipeline_running
    with pipeline_lock:
        if pipeline_running:
            return jsonify({"success": False, "message": "Pipeline is already running"}), 400
        pipeline_running = True

    data = request.json or {}
    institution = data.get("institution", "GD Goenka University")
    delay = float(data.get("delay", 0.5))

    # Clear previous logs from queue
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break

    thread = threading.Thread(
        target=run_pipeline_worker,
        args=(institution, delay),
        daemon=True
    )
    thread.start()
    return jsonify({"success": True, "message": "Extraction pipeline initiated"})


@app.route("/api/pipeline-logs")
def stream_pipeline_logs():
    """Server-Sent Events (SSE) endpoint for real-time console streaming."""
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


# ==========================================
# Main Single-Trigger Entrypoint
# ==========================================

def print_banner(url: str, port: int):
    """Prints a styled terminal banner."""
    print("\n" + "=" * 68)
    print("      GD GOENKA UNIVERSITY - VIDWAN RESEARCH INTELLIGENCE")
    print("      Apple-Inspired Officer Blue & White Research Portal")
    print("=" * 68)
    print(f"  * Web Portal URL:    {url}")
    print(f"  * Port Assigned:     {port}")
    print(f"  * Input Template:    {os.path.abspath(EXCEL_INPUT)}")
    print(f"  * Output Excel:      {os.path.abspath(EXCEL_OUTPUT)}")
    print("  * Browser Launch:    Opening default web browser automatically...")
    print("  * Server Status:     ACTIVE (Press Ctrl+C to stop)")
    print("=" * 68 + "\n")


def main():
    # 1. Ensure input file exists with generic placeholders
    load_faculty_names()

    # 2. Resolve port
    port = get_available_port(start_port=5000)
    url = f"http://localhost:{port}"

    # 3. Print terminal banner
    print_banner(url, port)

    # 4. Auto-launch browser
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    # 5. Start Flask web server
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
