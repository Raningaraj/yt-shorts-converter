# 🎬 YouTube Long Video → Shorts Converter
### B.Tech AI — 6th Semester Project | 100% FREE Stack

> **Goal:** Paste any long YouTube video link → get 5–6 smart vertical short clips
> that together cover the full concept of the topic — like YouTube Shorts / Reels.

---

## 📁 Project Structure

```
yt-shorts-converter/
│
├── backend/
│   ├── processor.py        ← Core AI pipeline (main logic)
│   ├── app.py              ← Flask REST API (serves frontend + API)
│   ├── .env.example        ← Copy to .env and add your Groq key
│   ├── downloads/          ← Auto-created: downloaded videos
│   └── output_shorts/      ← Auto-created: generated shorts
│
├── frontend/
│   └── index.html          ← Beautiful web UI (auto-served by Flask)
│
├── run.bat                 ← 🚀 Windows: One-click launcher
├── run.py                  ← 🚀 Mac/Linux: One-click launcher
├── setup.bat               ← Setup script (Windows)
├── requirements.txt        ← All Python dependencies
├── .env.example            ← Copy this to backend/.env
└── README.md               ← This file
```

---

## 🆓 Tech Stack (All Free)

| Step | Tool | Cost |
|------|------|------|
| Download YouTube video | `yt-dlp` | Free |
| Transcribe audio → text | `Whisper` (runs locally) | Free |
| AI find key segments | `LLaMA-3` via Groq API | Free |
| Cut + export short clips | `MoviePy` + `FFmpeg` | Free |
| Web interface | `Flask` + HTML | Free |

---

## ⚙️ SETUP — Step by Step

### ✅ Step 1 — Install Python
Download Python 3.9 or above from https://www.python.org/downloads/

Check it is installed:
```bash
python --version
```

---

### ✅ Step 2 — Install FFmpeg

FFmpeg is required for video processing.

**Windows:**
1. Go to https://ffmpeg.org/download.html
2. Download the Windows build
3. Extract and add the `bin` folder to your System PATH
4. Test: open CMD and type `ffmpeg -version`

**Mac:**
```bash
brew install ffmpeg
```

**Ubuntu / Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

---

### ✅ Step 3 — Get Your FREE Groq API Key

1. Go to → **https://console.groq.com**
2. Sign up with Google or GitHub (no credit card needed)
3. Click **"API Keys"** in left sidebar
4. Click **"Create API Key"** → copy the key (starts with `gsk_...`)

---

### ✅ Step 4 — Set Up the Project

```bash
# 1. Navigate into the project folder
cd yt-shorts-converter

# 2. (Recommended) Create a virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt
```

> ⚠️ First run will also download the Whisper model (~140MB). This happens automatically.

---

### ✅ Step 5 — Add Your Groq API Key

Create a file called `.env` inside the `backend/` folder:

```
GROQ_API_KEY=gsk_your_key_here
```

**Or** set it directly in terminal:

```bash
# Mac/Linux
export GROQ_API_KEY="gsk_your_key_here"

# Windows CMD
set GROQ_API_KEY=gsk_your_key_here

# Windows PowerShell
$env:GROQ_API_KEY="gsk_your_key_here"
```

---

## ▶️ HOW TO RUN

### ⚡ EASIEST — One-Click Runner (Recommended!)

**Windows:**
```bash
# First time setup (installs dependencies):
setup.bat

# Then just run:
run.bat
```

**Mac/Linux:**
```bash
python run.py
```

That's it! The script will:
1. ✅ Auto-activate the virtual environment
2. ✅ Auto-detect and use the correct Python
3. ✅ Start the Flask server
4. ✅ Open your browser to `http://localhost:5000`

---

### 📋 Manual Setup (If preferred)

```bash
# Navigate to project folder
cd yt-shorts-converter

# Create virtual environment (one time only)
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies:
pip install -r requirements.txt

# Run backend server:
cd backend
python app.py
```

---

### 🌐 Access the Web App

Once the server is running, open your browser to:
```
http://localhost:5000
```

You'll see the interactive web interface where you can:
1. Paste a YouTube URL
2. Choose cropping preference
3. Watch real-time progress
4. Download your generated shorts

---

### 📺 Command Line Option (If you prefer terminal)

```bash
cd backend
python processor.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Your shorts will appear in the `output_shorts/` folder.

---

## 🧪 Test with a Sample Video

Try it with a short educational video first (under 10 minutes):
```bash
python processor.py "https://www.youtube.com/watch?v=aircAruvnKk"
```
(3Blue1Brown Neural Networks video — perfect for testing)

---

## ⏱️ How Long Does It Take?

| Video Length | Download | Whisper (base) | Groq AI | Export |
|---|---|---|---|---|
| 10 min | ~30s | ~2 min | ~5s | ~1 min |
| 30 min | ~1 min | ~5 min | ~5s | ~3 min |
| 60 min | ~2 min | ~10 min | ~5s | ~5 min |

> 💡 Use `WHISPER_MODEL = "tiny"` in `processor.py` for faster transcription while testing.

---

## 🔧 Customization

In `backend/processor.py` you can change:

```python
# Whisper model size (line 42)
WHISPER_MODEL = "base"    # tiny | base | small | medium

# Groq model (line 133)
model="llama3-70b-8192"   # or "mixtral-8x7b-32768" for longer videos
```

---

## ❓ Common Errors and Fixes

| Error | Fix |
|---|---|
| `GROQ_API_KEY not set` | Add key to `.env` file or set in terminal |
| `ffmpeg not found` | Install FFmpeg and add to PATH |
| `No module named whisper` | Run `pip install openai-whisper` |
| `No module named groq` | Run `pip install groq` |
| `moviepy error` | Run `pip install moviepy imageio-ffmpeg` |
| Video not downloading | Update yt-dlp: `pip install -U yt-dlp` |

---

## 📊 Pipeline Architecture

```
YouTube URL
    │
    ▼
┌─────────────────────────────────┐
│  yt-dlp — Download MP4          │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Whisper (local) — Transcribe   │
│  Output: [{start, end, text}]   │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  Groq LLaMA-3 — Pick Segments   │
│  Finds 5-6 key 30-90s clips     │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  MoviePy — Cut + Crop + Export  │
│  9:16 vertical + captions       │
└────────────────┬────────────────┘
                 │
                 ▼
        5-6 Short MP4 Files
```

---

## 📝 Project Notes (For Viva)

- **Whisper** is OpenAI's open-source ASR model — runs entirely offline after first download
- **Groq** provides free inference for LLaMA-3 (Meta's open-source LLM) at very high speed
- **MoviePy** wraps FFmpeg for Python — handles all video cutting, cropping, and text overlays
- The AI selects segments based on: concepts, formulas, examples, and summaries — ensuring full topic coverage

---

*Made for B.Tech Artificial Intelligence — 6th Semester*
