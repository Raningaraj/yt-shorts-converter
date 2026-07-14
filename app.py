import os
import threading
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

from processor import convert


BACKEND_DIR = Path(__file__).parent
FRONTEND_DIR = BACKEND_DIR / "frontend"
OUTPUT_DIR = BACKEND_DIR / "output_shorts"
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/")
CORS(app, expose_headers=["Content-Disposition", "Content-Range", "Accept-Ranges", "Content-Length"])

jobs: dict[str, dict] = {}


def run_job(job_id: str, url: str, crop: bool, download_path: str = ""):
    try:
        jobs[job_id]["status"] = "processing"
        print(f"[Job {job_id}] Starting conversion for: {url}")

        # ── Streaming callback: called right after each short is saved ──
        def on_short_ready(filename: str, index: int, total: int):
            jobs[job_id]["total_shorts"] = total
            if filename not in jobs[job_id]["files"]:
                jobs[job_id]["files"].append(filename)
            print(f"[Job {job_id}] Short {index}/{total} ready: {filename}")

        paths = convert(url, crop_to_vert=crop, on_short_ready=on_short_ready)

        # Copy to custom path if requested
        if download_path:
            import shutil
            dest_dir = Path(download_path)
            dest_dir.mkdir(parents=True, exist_ok=True)
            print(f"[Job {job_id}] Copying files to custom download path: {download_path}")
            for p in paths:
                orig_file = Path(p)
                shutil.copy2(orig_file, dest_dir / orig_file.name)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["saved_to"] = download_path if download_path else None
        print(f"[Job {job_id}] Completed! Generated {len(paths)} shorts")
    except Exception as e:
        print(f"[Job {job_id}] ERROR: {str(e)}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@app.route("/api/select-directory")
def select_directory():
    """Trigger a native directory selector dialog via a subprocess."""
    import subprocess
    import sys
    
    code = """
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
path = filedialog.askdirectory(title="Select Save Directory")
root.destroy()
print(path)
"""
    try:
        # Run subprocess to avoid tkinter blocking the Flask main loop or thread restrictions
        res = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=120
        )
        if res.returncode == 0:
            selected_path = res.stdout.strip()
            return jsonify({"directory": selected_path})
        return jsonify({"directory": "", "error": res.stderr})
    except Exception as e:
        return jsonify({"directory": "", "error": str(e)}), 500


@app.route("/api/convert", methods=["POST"])
def start_conversion():
    """
    Body JSON: { "url": "<youtube_url>", "crop": true, "download_path": "..." }
    Returns:   { "job_id": "..." }
    """
    data = request.get_json(force=True)
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400

    crop = bool(data.get("crop", True))
    download_path = data.get("download_path", "").strip()
    
    if download_path:
        p = Path(download_path)
        if not p.exists():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return jsonify({"error": f"Invalid download path: {str(e)}"}), 400
        elif not p.is_dir():
            return jsonify({"error": "Download path must be a directory"}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "files": [], "error": None, "saved_to": None, "total_shorts": 0}

    t = threading.Thread(target=run_job, args=(job_id, url, crop, download_path), daemon=True)
    t.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/api/status/<job_id>")
def job_status(job_id: str):
    """Poll for job completion. Returns partial files list during processing."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404

    resp = {
        "status": job["status"],           # queued | processing | done | error
        "files": list(job.get("files", [])),  # grows in real-time as shorts finish
        "total_shorts": job.get("total_shorts", 0),
        "error": job.get("error"),
        "saved_to": job.get("saved_to"),
    }
    return jsonify(resp)


@app.route("/api/download/<filename>")
def download_short(filename: str):
    """Serve a generated short video with range-request support for browser preview."""
    import mimetypes
    from flask import Response
    
    safe_name = Path(filename).name
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        return jsonify({"error": "file not found"}), 404

    file_size = file_path.stat().st_size
    range_header = request.headers.get("Range", None)

    # Support for partial content (required for HTML5 <video> seek support)
    if range_header:
        byte1, byte2 = 0, None
        match = __import__("re").search(r"(\d+)-(\d*)", range_header)
        if match:
            g = match.groups()
            byte1 = int(g[0])
            byte2 = int(g[1]) if g[1] else file_size - 1

        byte2 = min(byte2, file_size - 1)
        length = byte2 - byte1 + 1

        with open(file_path, "rb") as f:
            f.seek(byte1)
            data = f.read(length)

        resp = Response(
            data,
            206,
            mimetype="video/mp4",
            direct_passthrough=True,
        )
        resp.headers["Content-Range"] = f"bytes {byte1}-{byte2}/{file_size}"
        resp.headers["Accept-Ranges"] = "bytes"
        resp.headers["Content-Length"] = str(length)
        resp.headers["Content-Disposition"] = f"inline; filename=\"{safe_name}\""
        return resp

    # Regular full file response
    resp = send_file(str(file_path), mimetype="video/mp4", as_attachment=False)
    resp.headers["Accept-Ranges"] = "bytes"
    resp.headers["Content-Length"] = str(file_size)
    resp.headers["Content-Disposition"] = f"inline; filename=\"{safe_name}\""
    return resp



@app.route("/api/export", methods=["POST"])
def export_shorts():
    """
    Body JSON: { "files": ["filename1.mp4", "filename2.mp4"], "download_path": "..." }
    Returns:   { "status": "success", "copied": N, "saved_to": "..." }
    """
    data = request.get_json(force=True)
    files = data.get("files", [])
    download_path = data.get("download_path", "").strip()
    
    if not files:
        return jsonify({"error": "No files specified to export"}), 400
    if not download_path:
        return jsonify({"error": "Export path is required"}), 400
        
    p = Path(download_path)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({"error": f"Invalid export path: {str(e)}"}), 400
        
    if not p.is_dir():
        return jsonify({"error": "Export path must be a directory"}), 400
        
    imported_files = []
    import shutil
    for filename in files:
        safe_name = Path(filename).name
        src_file = OUTPUT_DIR / safe_name
        dest_file = p / safe_name
        if src_file.exists():
            try:
                shutil.copy2(src_file, dest_file)
                imported_files.append(safe_name)
            except Exception as e:
                return jsonify({"error": f"Failed to copy {safe_name}: {str(e)}"}), 500
        else:
            return jsonify({"error": f"File {safe_name} not found on server"}), 404
            
    return jsonify({"status": "success", "copied": len(imported_files), "saved_to": str(p)})


@app.route("/api/download-zip", methods=["POST"])
def download_zip():
    """
    Body JSON: { "files": ["filename1.mp4", "filename2.mp4"] }
    Returns:   Zip file stream
    """
    import io
    import zipfile
    data = request.get_json(force=True)
    files = data.get("files", [])
    if not files:
        return jsonify({"error": "No files specified"}), 400
        
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in files:
            safe_name = Path(filename).name
            file_path = OUTPUT_DIR / safe_name
            if file_path.exists():
                zip_file.write(str(file_path), arcname=safe_name)
                
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name="generated_shorts.zip"
    )



@app.route("/")
def index():
    """Serve the frontend index.html"""
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/api/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "yt-shorts-converter"})


@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
