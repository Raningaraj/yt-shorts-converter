import os
import json
import re
import textwrap
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # Loads from the root directory .env or environment variables

import yt_dlp
import cv2
import numpy as np
from groq import Groq

BACKEND_DIR   = Path(__file__).parent
OUTPUT_DIR   = BACKEND_DIR / "output_shorts"
DOWNLOAD_DIR = BACKEND_DIR / "downloads"
OUTPUT_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
if not GROQ_API_KEY:
    print("\n" + "="*60)
    print("⚠️  ERROR: GROQ_API_KEY not set!")
    print("="*60)
    print("\nSteps to fix:")
    print("1. Get a FREE Groq API key from: https://console.groq.com")
    print("2. Create a .env file in project root with:")
    print("   GROQ_API_KEY=gsk_your_key_here")
    print("3. Or set it in terminal/deployment variables:")
    print("   export GROQ_API_KEY='gsk_your_key_here'")
    print("="*60 + "\n")
    raise ValueError("GROQ_API_KEY environment variable is not set")

groq_client = Groq(api_key=GROQ_API_KEY)






def get_cookiefile_path():
    """
    Check if a cookies.txt file exists in the directory, or if a YOUTUBE_COOKIES
    environment variable is set containing Netscape cookie file content.
    Returns (path_str, is_temp).
    """
    # 1. Check if cookies.txt exists in the backend directory
    root_cookies = BACKEND_DIR / "cookies.txt"
    if root_cookies.exists():
        return str(root_cookies), False

    # 2. Check if YOUTUBE_COOKIES env var is defined
    cookies_content = os.environ.get("YOUTUBE_COOKIES", "").strip()
    if cookies_content:
        fd, temp_path = tempfile.mkstemp(suffix=".txt", prefix="cookies_")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(cookies_content)
        return temp_path, True

    return None, False


def _extract_video_id(url: str):
    """Pull the YouTube video ID from any YouTube URL format."""
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0].split("&")[0]
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    if "embed/" in url:
        return url.split("embed/")[-1].split("?")[0]
    if "shorts/" in url:
        return url.split("shorts/")[-1].split("?")[0]
    return None


def _find_downloaded_file(ydl, info, vid_id: str) -> Path:
    """Locate the actual downloaded file regardless of container."""
    expected = Path(ydl.prepare_filename(info))
    if expected.exists():
        return expected
    for ext in [".mp4", ".mkv", ".webm", ".avi", ".m4v"]:
        candidate = expected.with_suffix(ext)
        if candidate.exists():
            return candidate
    for f in DOWNLOAD_DIR.glob(f"{vid_id}.*"):
        if f.suffix in [".mp4", ".mkv", ".webm", ".avi", ".m4v"]:
            return f
    return expected


def _fetch_proxies(limit: int = 30) -> list:
    """Fetch proxies from multiple free sources, return up to `limit` entries."""
    sources = [
        f"https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&limit={limit}",
        f"https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        f"https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    ]
    proxies = []
    for src in sources:
        if len(proxies) >= limit:
            break
        try:
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as r:
                lines = r.read().decode().strip().splitlines()
                for line in lines:
                    p = line.strip()
                    if p and ":" in p and not p.startswith("#"):
                        proxies.append(p)
                    if len(proxies) >= limit:
                        break
        except Exception:
            continue
    return proxies[:limit]


def _ydl_download(watch_url: str, opts: dict) -> tuple:
    """Run yt-dlp with given opts, returns (path, title) or raises."""
    with yt_dlp.YoutubeDL(opts) as ydl:
        info   = ydl.extract_info(watch_url, download=True)
        vid_id = info["id"]
        title  = info.get("title", "video")
        path   = _find_downloaded_file(ydl, info, vid_id)
        return path, title


def download_video(url: str):
    """
    Aggressive 4-tier YouTube download strategy:
      Tier 1 — yt-dlp + browser impersonation (curl_cffi)
      Tier 2 — yt-dlp player clients (mweb/tv_embedded/ios/android)
      Tier 3 — yt-dlp + proxy rotation (30 proxies, 3 sources)
      Tier 4 — pytubefix (completely separate library, different HTTP stack)
    """
    video_id  = _extract_video_id(url)
    watch_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else url
    print(f"\nDownloading: {watch_url}")

    cookie_path, is_temp = get_cookiefile_path()
    if cookie_path:
        print(f"  Using cookies: {'from env' if is_temp else cookie_path}")

    base_opts = {
        "format":               "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl":              str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "merge_output_format":  "mp4",
        "quiet":                True,
        "no_warnings":          True,
        "socket_timeout":       20,
        "retries":              1,
        "fragment_retries":     1,
    }
    if cookie_path:
        base_opts["cookiefile"] = cookie_path

    try:
        # ════════════════════════════════════════════════════════
        # TIER 1 — yt-dlp + curl_cffi browser impersonation
        #   Spoofs real Chrome/Safari TLS fingerprint — strongest bypass
        # ════════════════════════════════════════════════════════
        impersonate_targets = ["chrome", "chrome110", "safari", "safari17_0", "edge99"]
        for browser in impersonate_targets:
            try:
                opts = {
                    **base_opts,
                    "impersonate": browser,
                    "extractor_args": {"youtube": {"player_client": ["mweb", "web"]}},
                }
                print(f"[T1] Impersonating {browser} ...")
                path, title = _ydl_download(watch_url, opts)
                print(f"✅ [T1] Downloaded '{title}'")
                return path, title
            except Exception as e:
                err = str(e)
                if "impersonate" in err.lower() or "curl" in err.lower() or "ModuleNotFoundError" in err:
                    print(f"[T1] curl_cffi not available, skipping impersonation tier")
                    break
                print(f"[T1] {browser} failed: {err[:100]}")

        # ════════════════════════════════════════════════════════
        # TIER 2 — yt-dlp player clients (no proxy)
        #   Different YouTube API paths — some bypass bot checks
        # ════════════════════════════════════════════════════════
        client_combos = [
            ["mweb"],
            ["tv_embedded"],
            ["ios"],
            ["android"],
            ["web_creator"],
            ["mweb", "ios"],
            ["tv_embedded", "android"],
        ]
        for clients in client_combos:
            label = "+".join(clients)
            try:
                opts = {
                    **base_opts,
                    "extractor_args": {"youtube": {"player_client": clients}},
                }
                print(f"[T2] Client: {label} ...")
                path, title = _ydl_download(watch_url, opts)
                print(f"✅ [T2] Downloaded '{title}'")
                return path, title
            except Exception as e:
                print(f"[T2] {label}: {str(e)[:90]}")

        # ════════════════════════════════════════════════════════
        # TIER 3 — yt-dlp + proxy rotation (30 proxies, 3 sources)
        #   Route through residential/datacenter proxy to get a clean IP
        # ════════════════════════════════════════════════════════
        print("[T3] Fetching proxy list (30 proxies from 3 sources)...")
        proxies = _fetch_proxies(limit=30)
        print(f"[T3] Got {len(proxies)} proxies. Trying each...")

        for j, proxy in enumerate(proxies, 1):
            proxy_url = f"http://{proxy}" if not proxy.startswith("http") else proxy
            for clients in [["mweb"], ["tv_embedded"], ["ios"]]:
                try:
                    opts = {
                        **base_opts,
                        "proxy":            proxy_url,
                        "socket_timeout":   12,
                        "extractor_args":   {"youtube": {"player_client": clients}},
                    }
                    path, title = _ydl_download(watch_url, opts)
                    print(f"✅ [T3] Proxy {j} ({proxy}) downloaded '{title}'")
                    return path, title
                except Exception as e:
                    err = str(e)
                    # Stop trying this proxy on connection errors, try next one
                    if any(x in err for x in ["refused", "timed out", "tunnel", "Tunnel"]):
                        break
                    # Bot error — try next client on same proxy
                    continue

            if j % 5 == 0:
                print(f"[T3] Tried {j}/{len(proxies)} proxies...")

        # ════════════════════════════════════════════════════════
        # TIER 4 — pytubefix
        #   Completely separate HTTP stack, different YouTube API
        # ════════════════════════════════════════════════════════
        print("[T4] Trying pytubefix (separate HTTP stack)...")
        try:
            from pytubefix import YouTube
            from pytubefix.cli import on_progress

            yt     = YouTube(watch_url, on_progress_callback=on_progress, use_oauth=False)
            title  = yt.title or "video"
            stream = (
                yt.streams.filter(progressive=True, file_extension="mp4")
                  .order_by("resolution").last()
                or yt.streams.get_highest_resolution()
            )
            if stream:
                out_path = stream.download(output_path=str(DOWNLOAD_DIR),
                                           filename=f"{video_id}.mp4")
                print(f"✅ [T4] pytubefix downloaded '{title}'")
                return Path(out_path), title
        except ImportError:
            print("[T4] pytubefix not installed")
        except Exception as e:
            print(f"[T4] pytubefix failed: {str(e)[:120]}")

    finally:
        if is_temp and cookie_path and os.path.exists(cookie_path):
            try:
                os.unlink(cookie_path)
            except Exception:
                pass

    raise RuntimeError(
        "All 4 download tiers failed. The server IP is heavily blocked by YouTube. "
        "Please set the YOUTUBE_COOKIES environment variable on Render with your "
        "exported YouTube cookies to bypass this restriction reliably."
    )



def get_ffmpeg():
    """Find ffmpeg — works with imageio-ffmpeg (no system install needed)."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"   # fall back to system ffmpeg if available


def transcribe_video(video_path: Path) -> dict:
    print("Extracting audio for Groq transcriptions API...")
    audio_path = video_path.with_suffix(".m4a")
    ffmpeg = get_ffmpeg()
    
    # Extract audio: mono, 32k bitrate, AAC
    cmd = [
        ffmpeg, "-y",
        "-i", str(video_path),
        "-vn",
        "-c:a", "aac",
        "-b:a", "32k",
        "-ac", "1",
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to extract audio with ffmpeg:\n{result.stderr}")
        
    print(f"Audio extracted to: {audio_path.name} ({audio_path.stat().st_size / 1024 / 1024:.2f} MB)")
    
    try:
        print("Sending audio to Groq Whisper API (whisper-large-v3)...")
        with open(audio_path, "rb") as file:
            transcription = groq_client.audio.transcriptions.create(
                file=(audio_path.name, file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        
        transcription_dict = transcription.model_dump() if hasattr(transcription, "model_dump") else dict(transcription)
        segments = transcription_dict.get("segments", [])
        print(f"Transcription done — {len(segments)} segments completed")
        return transcription_dict
        
    finally:
        if audio_path.exists():
            audio_path.unlink(missing_ok=True)


ANALYSIS_PROMPT = """
You are an expert educational content curator. Given a timestamped transcript of a
long educational YouTube video, identify the 5-6 MOST IMPORTANT segments that together
give a viewer the FULL understanding of the topic.

Focus on: core concepts, key formulas/algorithms, worked examples, summary points.

Return ONLY a valid JSON array (no markdown, no explanation):
[
  {
    "short_number": 1,
    "title": "Short descriptive title",
    "key_concept": "One-line summary of what this segment teaches",
    "important_terms": ["term1", "term2"],
    "start_time": 12.5,
    "end_time": 87.3,
    "reason": "Why this segment is crucial"
  }
]

Rules:
- Each segment MUST be 30-90 seconds long.
- Segments must NOT overlap.
- Cover different aspects — no repeating the same idea.
- start_time and end_time must be real values from the transcript.
- Return ONLY the JSON array. Nothing else.
"""

def analyze_transcript(transcript_result: dict, video_title: str) -> list:
    lines = [
        f"[{s['start']:.1f}s - {s['end']:.1f}s]: {s['text'].strip()}"
        for s in transcript_result["segments"]
    ]
    transcript_text = "\n".join(lines)
    if len(transcript_text) > 24000:
        transcript_text = transcript_text[:24000] + "\n...[truncated]"

    print("Analyzing with LLaMA-3 via Groq (free)...")
    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user",   "content": f"Video Title: {video_title}\n\nTranscript:\n{transcript_text}"},
        ],
        temperature=0.3,
        max_tokens=2048,
    )

    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$",          "", raw, flags=re.MULTILINE).strip()
    m   = re.search(r"\[.*\]", raw, re.DOTALL)
    if m:
        raw = m.group(0)

    segments = json.loads(raw)
    print(f"LLaMA-3 identified {len(segments)} key segments")
    return segments


def cut_clip_ffmpeg(source: Path, start: float, end: float, out: Path):
    """Cut a segment from source video using FFmpeg."""
    ffmpeg = get_ffmpeg()
    duration = end - start
    cmd = [
        ffmpeg, "-y",
        "-ss", str(start),
        "-i", str(source),
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-avoid_negative_ts", "make_zero",
        str(out)
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg cut failed:\n{result.stderr.decode()}")


def crop_to_vertical_ffmpeg(source: Path, out: Path):
    """Center-crop 16:9 video to 9:16 using FFmpeg."""
    ffmpeg = get_ffmpeg()
    
    probe_cmd = [
        ffmpeg, "-i", str(source),
        "-hide_banner"
    ]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True)
    
    match = re.search(r"(\d{3,4})x(\d{3,4})", probe.stderr)
    if not match:
        return source  # can't parse, skip crop
    
    w, h = int(match.group(1)), int(match.group(2))
    if w <= h:
        return source  # already portrait

    target_w = int(h * 9 / 16)
    x_offset = (w - target_w) // 2

    cmd = [
        ffmpeg, "-y",
        "-i", str(source),
        "-vf", f"crop={target_w}:{h}:{x_offset}:0",
        "-c:v", "libx264",
        "-c:a", "aac",
        str(out)
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return source  # crop failed, use original
    return out


def draw_text_with_background(frame, text, position, font_scale, color,
                              bg_color=(0, 0, 0), thickness=2, padding=8):
    """Draw text with a dark background box on a frame."""
    font      = cv2.FONT_HERSHEY_DUPLEX
    lines     = text.split("\n")
    x, y      = position
    line_h    = int(30 * font_scale)

    for i, line in enumerate(lines):
        ly = y + i * line_h
        (tw, th), _ = cv2.getTextSize(line, font, font_scale, thickness)
        cv2.rectangle(frame,
                      (x - padding, ly - th - padding),
                      (x + tw + padding, ly + padding),
                      bg_color, -1)
      
        cv2.putText(frame, line, (x, ly), font, font_scale, color, thickness, cv2.LINE_AA)


def add_text_overlay_opencv(video_path: Path, out_path: Path,
                             title: str, concept: str):
    """
    Add title (top) and concept caption (bottom) overlays
    using OpenCV — with pre-computed text layouts to make it 5x faster.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps   = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    tmp_video = out_path.parent / f"_tmp_novid_{out_path.name}"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(tmp_video), fourcc, fps, (w, h))

    font_scale_title   = max(0.5, w / 1000)
    font_scale_caption = max(0.45, w / 1100)
    font = cv2.FONT_HERSHEY_DUPLEX

    max_chars = max(20, int(w / (14 * font_scale_caption)))
    wrapped_concept = "\n".join(textwrap.wrap(concept, max_chars))

    title_frames = int(fps * 3)

    # 1. Precomputations: Title layout
    title_lines = title[:60].split("\n")
    title_line_h = int(30 * font_scale_title)
    title_y = int(h * 0.06)
    title_padding = 10
    title_draw_commands = []
    for i, line in enumerate(title_lines):
        ly = title_y + i * title_line_h
        (tw, th), _ = cv2.getTextSize(line, font, font_scale_title, 2)
        rect_start = (20 - title_padding, ly - th - title_padding)
        rect_end = (20 + tw + title_padding, ly + title_padding)
        title_draw_commands.append((line, rect_start, rect_end, (20, ly)))

    # 2. Precomputations: Caption layout
    caption_lines = wrapped_concept.split("\n")
    caption_line_h = int(32 * font_scale_caption)
    caption_y = h - (len(caption_lines) * caption_line_h) - 30
    caption_padding = 8
    caption_draw_commands = []
    for i, line in enumerate(caption_lines):
        ly = caption_y + i * caption_line_h
        (tw, th), _ = cv2.getTextSize(line, font, font_scale_caption, 2)
        rect_start = (20 - caption_padding, ly - th - caption_padding)
        rect_end = (20 + tw + caption_padding, ly + caption_padding)
        caption_draw_commands.append((line, rect_start, rect_end, (20, ly)))

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw title overlays (for first 3 seconds only)
        if frame_idx < title_frames:
            for line, rect_start, rect_end, text_pos in title_draw_commands:
                cv2.rectangle(frame, rect_start, rect_end, (0, 0, 0), -1)
                cv2.putText(frame, line, text_pos, font, font_scale_title, (0, 230, 255), 2, cv2.LINE_AA)

        # Draw caption concept overlays (always)
        for line, rect_start, rect_end, text_pos in caption_draw_commands:
            cv2.rectangle(frame, rect_start, rect_end, (20, 20, 20), -1)
            cv2.putText(frame, line, text_pos, font, font_scale_caption, (255, 255, 255), 2, cv2.LINE_AA)

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()

    ffmpeg = get_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", str(tmp_video),      
        "-i", str(video_path),     
        "-c:v", "libx264",
        "-c:a", "aac",
        "-map", "0:v",
        "-map", "1:a?",
        "-shortest",
        str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    tmp_video.unlink(missing_ok=True)

    if result.returncode != 0:
        # Fallback to copy format using direct H264 re-encoding (guarantees browser readability)
        cmd_fallback = [
            ffmpeg, "-y",
            "-i", str(tmp_video),
            "-c:v", "libx264",
            str(out_path)
        ]
        subprocess.run(cmd_fallback, capture_output=True)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


def export_short(source_video: Path, segment: dict, idx: int, crop: bool = True) -> Path:
    try:
        start = float(segment.get("start_time", 0.0))
        end   = float(segment.get("end_time", 30.0))
    except (ValueError, TypeError, KeyError):
        start = 0.0
        end   = 30.0

    # Ensure timestamps do not overshoot video duration
    cap = cv2.VideoCapture(str(source_video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / fps if total_frames and fps else 300.0
    cap.release()

    if start < 0: start = 0.0
    if end > duration: end = duration
    if end - start < 5.0: end = min(duration, start + 30.0)

    title    = segment.get("title", f"Short {idx}")
    concept  = segment.get("key_concept", "")

    print(f"  Short {idx}: '{title}' [{start:.1f}s -> {end:.1f}s]")

    slug     = slugify(title)
    tmp_cut  = OUTPUT_DIR / f"_tmp_cut_{idx}_{slug}.mp4"
    tmp_crop = OUTPUT_DIR / f"_tmp_crop_{idx}_{slug}.mp4"
    out_path = OUTPUT_DIR / f"short_{idx:02d}_{slug}.mp4"

    try:
        # 1. Cut segment
        cut_clip_ffmpeg(source_video, start, end, tmp_cut)

        # 2. Crop to vertical
        if crop:
            cropped = crop_to_vertical_ffmpeg(tmp_cut, tmp_crop)
        else:
            cropped = tmp_cut

        # 3. Add text overlays with OpenCV
        add_text_overlay_opencv(cropped, out_path,
                                title=f"#{idx} {title}",
                                concept=concept)

        print(f"     Saved -> {out_path.name}")
        return out_path

    finally:
        for f in [tmp_cut, tmp_crop]:
            if f.exists():
                f.unlink(missing_ok=True)


def convert(youtube_url: str, crop_to_vert: bool = True, on_short_ready=None) -> list:
    print("\nYouTube Long -> Shorts Converter  [100% FREE]")
    print("=" * 52)

    video_path, title = download_video(youtube_url)
    transcript        = transcribe_video(video_path)
    segments          = analyze_transcript(transcript, title)

    print(f"\nGenerating {len(segments)} shorts...")
    paths = []
    for i, seg in enumerate(segments, 1):
        out = export_short(video_path, seg, i, crop=crop_to_vert)
        paths.append(out)
        # ── Notify caller immediately so frontend can stream the card ──
        if on_short_ready:
            try:
                on_short_ready(Path(out).name, i, len(segments))
            except Exception:
                pass

    print("\n" + "=" * 52)
    print("All shorts generated!\n")
    for i, (seg, p) in enumerate(zip(segments, paths), 1):
        print(f"  Short {i}: {seg['title']}")
        print(f"           Concept: {seg['key_concept']}")
        print(f"           File   : {p}\n")
    return paths



if __name__ == "__main__":
    import sys

    if not os.environ.get("GROQ_API_KEY"):
        print("\nERROR: GROQ_API_KEY not found!")
        print("Make sure .env contains: GROQ_API_KEY=gsk_...")
        print("Get a FREE key at: https://console.groq.com\n")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python processor.py <youtube_url> [--landscape]")
        sys.exit(1)

    convert(sys.argv[1], crop_to_vert="--landscape" not in sys.argv)
