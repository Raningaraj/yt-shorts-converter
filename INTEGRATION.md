# 🔗 Frontend-Backend Integration Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Browser (http://localhost:5000)                       │
│  ┌────────────────────────────────────────────────────┐│
│  │  Frontend (index.html)                             ││
│  │  ├── HTML/CSS/JavaScript                           ││
│  │  └── API Calls to /api/*                           ││
│  └────────────────┬─────────────────────────────────┬─┘
│                   │                                 │
│                   └─────────────────┬───────────────┘
│                                     │
│  ┌─────────────────────────────────▼──────────────────┐
│  │  Flask Backend (http://localhost:5000/api)        │
│  │  ├── /api/convert       (POST)  - Start job       │
│  │  ├── /api/status/<id>   (GET)   - Check progress  │
│  │  ├── /api/download/*    (GET)   - Download video  │
│  │  └── /api/health        (GET)   - Health check    │
│  └─────────────────────────────────┬──────────────────┘
│                                     │
│  ┌─────────────────────────────────▼──────────────────┐
│  │  Python Pipeline (processor.py)                    │
│  │  ├── 1. Download video (yt-dlp)                   │
│  │  ├── 2. Transcribe audio (Whisper)                │
│  │  ├── 3. Analyze segments (Groq/LLaMA-3)           │
│  │  └── 4. Export shorts (MoviePy)                   │
│  └─────────────────────────────────┬──────────────────┘
│                                     │
│  ┌─────────────────────────────────▼──────────────────┐
│  │  File System                                       │
│  │  ├── backend/downloads/      ← Downloaded videos  │
│  │  └── backend/output_shorts/  ← Generated shorts   │
│  └────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Start Conversion
**Endpoint:** `POST /api/convert`

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "crop": true
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Flow:**
1. Frontend sends YouTube URL
2. Backend creates unique job ID
3. Starts background thread to process video
4. Returns job ID immediately (202 Accepted)

---

### 2. Poll Job Status
**Endpoint:** `GET /api/status/<job_id>`

**Response (While Processing):**
```json
{
  "status": "processing",
  "files": [],
  "error": null
}
```

**Response (When Done):**
```json
{
  "status": "done",
  "files": [
    "short_1_introduction.mp4",
    "short_2_concept.mp4",
    "short_3_examples.mp4"
  ],
  "error": null
}
```

**Response (On Error):**
```json
{
  "status": "error",
  "files": [],
  "error": "GROQ_API_KEY not set error message"
}
```

---

### 3. Download Short Video
**Endpoint:** `GET /api/download/<filename>`

**Response:** Binary MP4 file with proper headers:
- `Content-Type: video/mp4`
- `Content-Disposition: attachment; filename=...`

**Security:** 
- Prevents path traversal attacks
- Only allows files from `output_shorts/` directory

---

### 4. Health Check
**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "ok",
  "service": "yt-shorts-converter"
}
```

---

## Frontend-Backend Communication

### JavaScript Fetch Calls

**1. Start Conversion:**
```javascript
const response = await fetch("/api/convert", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    url: "https://www.youtube.com/watch?v=...",
    crop: true
  })
});
const data = await response.json();
const jobId = data.job_id;
```

**2. Poll Status (Every 3 seconds):**
```javascript
const response = await fetch(`/api/status/${jobId}`);
const data = await response.json();

if (data.status === "done") {
  // All shorts ready for download
  renderResults(data.files);
} else if (data.status === "error") {
  // Show error message
  showError(data.error);
}
```

**3. Download File:**
```javascript
window.open(`/api/download/${filename}`, "_blank");
```

---

## File Paths

### Backend Directory Structure
```
backend/
├── app.py              ← Flask server with API routes
├── processor.py        ← AI pipeline (download, transcribe, analyze, export)
├── .env                ← Groq API key (created by user)
├── .env.example        ← Template
├── downloads/          ← Temporary downloaded videos
├── output_shorts/      ← Generated clips (served by download endpoint)
└── __pycache__/        ← Python cache
```

### How Paths Work
1. **Backend directory detection:**
   ```python
   BACKEND_DIR = Path(__file__).parent  # C:\...\backend
   ```

2. **Output directory:**
   ```python
   OUTPUT_DIR = BACKEND_DIR / "output_shorts"  # Absolute path
   ```

3. **Frontend referenced from backend:**
   ```python
   FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
   ```

---

## Error Handling

### Client-Side (Frontend)
Only shows user-friendly messages:
- "YouTube URL is invalid"
- "Lost connection to server"
- "Video processing failed"

### Server-Side (Backend)
Detailed error messages in logs:
```
[Job abc123] Starting conversion for: https://youtube.com/...
[Job abc123] Downloaded: "Video Title" (234.5 MB)
[Job abc123] Transcribing...
[Job abc123] LLaMA-3 identified 5 key segments
[Job abc123] Generating 5 shorts...
[Job abc123] Completed! Generated 5 shorts
```

### Error Recovery
- Invalid URL: Caught by Flask validation
- Missing API key: Caught at module load time
- Network error: Frontend retries every 3 seconds
- Timeout: Frontend shows "Lost connection"

---

## CORS (Cross-Origin Resource Sharing)

**Why it's needed:**
Frontend and backend run on same origin `localhost:5000`, so CORS is technically not needed, but configured for:
- Flexibility if deployed separately
- Security best practices
- API compatibility

**Configuration:**
```python
from flask_cors import CORS
CORS(app)  # Allows all origins
```

---

## Static File Serving

### How Frontend is Served
1. Flask `static_folder` points to `frontend/` directory
2. Requests to `/` are routed to `index.html`
3. CSS/JS files are auto-served from `frontend/` 
4. API requests to `/api/*` bypass static serving

### URL Mapping
```
GET /                  → frontend/index.html
GET /api/*             → Flask API routes
GET /download/*        → Video files from output_shorts/
```

---

## Testing Connection

### Quick Test
```bash
# Terminal 1: Start server
python run.py

# Terminal 2: Test endpoints
curl http://localhost:5000/              # Should return HTML
curl http://localhost:5000/api/health    # Should return {"status": "ok"}
```

### Health Check Script
```python
import requests

try:
    response = requests.get("http://localhost:5000/api/health")
    print("✓ Backend is running:", response.json())
except Exception as e:
    print("✗ Backend error:", e)
```

---

## Deployment Notes

### Development (Current)
- Frontend served from same Flask instance
- In-memory job storage (data lost on restart)
- Debug mode enabled

### Production (Future)
- Frontend could be served by CDN or separate web server
- Use database (PostgreSQL) instead of in-memory `jobs` dict
- Redis for caching and job queuing
- SSL/HTTPS for security
- Environment variables for configuration

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| 404 on `/` | Frontend folder not found | Check `FRONTEND_DIR` path |
| API 500 error | Missing Groq API key | Create `.env` with GROQ_API_KEY |
| Download fails | File not in `output_shorts/` | Check export completed successfully |
| Slow responses | FFmpeg encoding | Use faster Whisper model |
| Port 5000 in use | Another service running | Change PORT in `.env` |

---

**Everything is now connected! 🎉**
