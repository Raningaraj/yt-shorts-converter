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
CORS(app, expose_headers=["Content-Disposition"])

jobs: dict[str, dict] = {}


def run_job(job_id: str, url: str, crop: bool, download_path: str = ""):
    try:
        jobs[job_id]["status"] = "processing"
        print(f"[Job {job_id}] Starting conversion for: {url}")
        paths = convert(url, crop_to_vert=crop)
        
        # If custom download_path is provided, copy/move completed shorts there!
        if download_path:
            import shutil
            dest_dir = Path(download_path)
            dest_dir.mkdir(parents=True, exist_ok=True)
            print(f"[Job {job_id}] Copying files to custom download path: {download_path}")
            for p in paths:
                orig_file = Path(p)
                dest_file = dest_dir / orig_file.name
                shutil.copy2(orig_file, dest_file)
                
        jobs[job_id]["status"] = "done"
        jobs[job_id]["files"] = [Path(p).name for p in paths]
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
    jobs[job_id] = {"status": "queued", "files": [], "error": None, "saved_to": None}

    t = threading.Thread(target=run_job, args=(job_id, url, crop, download_path), daemon=True)
    t.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/api/status/<job_id>")
def job_status(job_id: str):
    """Poll for job completion."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404

    resp = {
        "status": job["status"],      # queued | processing | done | error
        "files": [Path(f).name for f in job.get("files", [])],
        "error": job.get("error"),
        "saved_to": job.get("saved_to"),
    }
    return jsonify(resp)


@app.route("/api/download/<filename>")
def download_short(filename: str):
    """Serve a generated short video."""
    safe_name = Path(filename).name          
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists():
        return jsonify({"error": "file not found"}), 404
    return send_file(str(file_path), mimetype="video/mp4", as_attachment=True)


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
