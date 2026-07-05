# 🚀 Quick Start Guide - YT Shorts Converter

## ⚡ Fast Setup (2 minutes)

### Step 1: Get Your Free Groq API Key
1. Visit: https://console.groq.com
2. Sign up with Google or GitHub
3. Go to "API Keys" and copy your key (starts with `gsk_`)

### Step 2: Create `.env` File
Create a new file `backend/.env` with:
```
GROQ_API_KEY=gsk_your_key_here_paste_here
```

### Step 3: Install Dependencies (First Time Only)
**Windows:**
```bash
setup.bat
```

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Run the App

**Windows:**
```bash
run.bat
```

**Mac/Linux:**
```bash
python run.py
```

### Step 5: Open in Browser
```
http://localhost:5000
```

---

## 🎯 What to Expect

1. **Paste a YouTube URL** → Supports any video link
2. **Choose options** → Crop to vertical (9:16) or keep landscape
3. **Watch progress** → Real-time updates as AI processes
4. **Download shorts** → Ready-to-upload vertical videos

---

## 📊 Processing Times

- **Download**: 30s - 2 minutes
- **Transcribe**: 1-10 minutes (depends on video length)
- **AI Analysis**: 5-10 seconds
- **Export**: 1-5 minutes
- **Total**: Roughly 5-20 minutes per video

---

## ⚠️ Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY not set` | Create `.env` file with your key |
| `ModuleNotFoundError: No module named 'FFmpeg'` | Already included via imageio-ffmpeg |
| Server won't start | Try running `run.py` instead of `run.bat` |
| Port 5000 in use | Kill the process or change PORT in .env |
| Slow transcription | Try `WHISPER_MODEL = "tiny"` in processor.py |

---

## 🎬 Test Video

First-time users: try this short video:
```
https://www.youtube.com/watch?v=aircAruvnKk
```
(3Blue1Brown Neural Networks - Perfect demo!)

---

## 📱 Output Files

All generated shorts appear in:
```
backend/output_shorts/
```

Ready for direct upload to TikTok, Instagram Reels, or YouTube Shorts!

---

## 🔧 Advanced

### Change Whisper Model (Faster Transcription)
Edit `backend/processor.py` line 41:
```python
WHISPER_MODEL = "tiny"  # tiny | base | small | medium
```
- `tiny`: ~30s per hour (lower quality)
- `base`: ~2 min per hour (default, good quality)

### Change Groq Model
Edit `backend/processor.py` line 151:
```python
model="mixtral-8x7b-32768"  # Good for longer videos
```

---

## 📞 Support

Check the README.md for detailed documentation and architecture details.

---

**Happy short-making! 🎉**
