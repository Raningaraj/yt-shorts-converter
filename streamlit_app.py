import streamlit as st
import requests
import time
import os
import subprocess
import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# Start Flask backend in the background (only once)
# ═══════════════════════════════════════════════════════════════════════════

if "flask_started" not in st.session_state:
    try:
        # Check if Flask is already running
        requests.get("http://localhost:5000/api/convert", timeout=1)
        st.session_state.flask_started = True
    except:
        # Flask not running, start it
        print("[STREAMLIT] Starting Flask backend...", flush=True)
        flask_env = os.environ.copy()
        flask_env["FLASK_ENV"] = "production"
        flask_env["FLASK_APP"] = "backend/app.py"
        subprocess.Popen(
            [sys.executable, "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"],
            cwd=".",
            env=flask_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)  # Give Flask time to start
        st.session_state.flask_started = True

# ═══════════════════════════════════════════════════════════════════════════
# Streamlit Frontend for YouTube to Shorts Converter
# ═══════════════════════════════════════════════════════════════════════════

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")

# Page config
st.set_page_config(
    page_title="YT → Shorts Converter",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a0533 50%, #001a33 100%);
    }
    .main {
        background: transparent;
    }
    h1 {
        color: #ff6b6b;
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 0.5em;
    }
    .subtitle {
        text-align: center;
        color: #888;
        margin-bottom: 2em;
        font-size: 1.1em;
    }
    .stButton > button {
        background: linear-gradient(90deg, #ff0000, #e94560);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #e94560, #ff0000);
        box-shadow: 0 8px 32px rgba(255, 0, 0, 0.3);
    }
    .status-box {
        padding: 16px;
        border-radius: 8px;
        margin: 12px 0;
    }
    .status-processing {
        background: rgba(255, 107, 107, 0.2);
        border-left: 4px solid #ff6b6b;
    }
    .status-done {
        background: rgba(76, 175, 80, 0.2);
        border-left: 4px solid #4caf50;
    }
    .status-error {
        background: rgba(244, 67, 54, 0.2);
        border-left: 4px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("# 🎬 YouTube to Shorts Converter", help="Convert any YouTube video into vertical TikTok-style shorts")
st.markdown('<p class="subtitle">Powered by AI • 100% Free • Runs Locally</p>', unsafe_allow_html=True)

# Session state for job tracking
if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "status" not in st.session_state:
    st.session_state.status = None

# ═══════════════════════════════════════════════════════════════════════════
# Input Section
# ═══════════════════════════════════════════════════════════════════════════

col1, col2 = st.columns([4, 1])

with col1:
    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    crop_mode = st.checkbox("🎯 Crop to Vertical", value=True, help="Auto-crop to 9:16 aspect ratio")

# Convert button
if st.button("🚀 Convert to Shorts", use_container_width=True):
    if not youtube_url.strip():
        st.error("❌ Please enter a YouTube URL")
    else:
        # Call backend API
        with st.spinner("📤 Sending to backend..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/convert",
                    json={"url": youtube_url, "crop": crop_mode},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.job_id = data.get("job_id")
                    st.session_state.status = "processing"
                    st.success("✅ Conversion started!")
                else:
                    st.error(f"❌ Backend error: {response.json().get('error', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure it's running.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ═══════════════════════════════════════════════════════════════════════════
# Status Tracking Section
# ═══════════════════════════════════════════════════════════════════════════

if st.session_state.job_id:
    st.divider()
    st.markdown("### 📊 Conversion Status")
    
    # Auto-refresh placeholder
    status_placeholder = st.empty()
    files_placeholder = st.empty()
    
    max_wait = 600  # 10 minutes timeout
    elapsed = 0
    poll_interval = 2  # Check every 2 seconds
    
    while elapsed < max_wait:
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/status/{st.session_state.job_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                job_data = response.json()
                status = job_data.get("status", "unknown")
                
                # Update status display
                if status == "processing":
                    with status_placeholder.container():
                        st.markdown(
                            f'<div class="status-box status-processing">⏳ **Processing...**</div>',
                            unsafe_allow_html=True
                        )
                    time.sleep(poll_interval)
                    elapsed += poll_interval
                    st.rerun()
                
                elif status == "done":
                    with status_placeholder.container():
                        st.markdown(
                            f'<div class="status-box status-done">✅ **Conversion Complete!**</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Show download links
                    files = job_data.get("files", [])
                    if files:
                        with files_placeholder.container():
                            st.markdown("#### 📥 Download Shorts:")
                            for file in files:
                                if st.button(f"⬇️ {file}", key=file, use_container_width=True):
                                    try:
                                        dl_response = requests.get(
                                            f"{BACKEND_URL}/api/download/{st.session_state.job_id}/{file}",
                                            timeout=30
                                        )
                                        if dl_response.status_code == 200:
                                            st.download_button(
                                                label=f"Download {file}",
                                                data=dl_response.content,
                                                file_name=file,
                                                mime="video/mp4"
                                            )
                                        else:
                                            st.error(f"Failed to download {file}")
                                    except Exception as e:
                                        st.error(f"Download error: {str(e)}")
                    break
                
                elif status == "error":
                    with status_placeholder.container():
                        error_msg = job_data.get("error", "Unknown error")
                        st.markdown(
                            f'<div class="status-box status-error">❌ **Error:** {error_msg}</div>',
                            unsafe_allow_html=True
                        )
                    break
        
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot reach backend. Conversion may still be running.")
            break
        except Exception as e:
            st.error(f"❌ Error checking status: {str(e)}")
            break
    
    if elapsed >= max_wait:
        st.warning("⏱️ Conversion timed out. Please try again.")
        st.session_state.job_id = None

# ═══════════════════════════════════════════════════════════════════════════
# Footer
# ═══════════════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<p style="text-align: center; color: #888; font-size: 0.9em; margin-top: 2em;">
    🎯 Built with <b>Streamlit</b> + <b>Flask</b> + <b>AI</b> | 
    <a href="https://github.com/Raningaraj/yt-shorts-converter" target="_blank">GitHub</a>
</p>
""", unsafe_allow_html=True)
