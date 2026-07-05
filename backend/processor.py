

import os
import json
import re
import textwrap
import subprocess
import tempfile
from pathlib import Path


from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


import yt_dlp
import whisper
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
    print("2. Create a .env file in backend/ folder with:")
    print("   GROQ_API_KEY=gsk_your_key_here")
    print("3. Or set it in terminal:")
    print("   export GROQ_API_KEY='gsk_your_key_here'  (Mac/Linux)")
    print("   set GROQ_API_KEY=gsk_your_key_here       (Windows CMD)")
    print("="*60 + "\n")
    raise ValueError("GROQ_API_KEY environment variable is not set")

groq_client   = Groq(api_key=GROQ_API_KEY)
WHISPER_MODEL = "base"   # tiny | base | small | medium



def download_video(url: str):
    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]",
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info     = ydl.extract_info(url, download=True)
        video_id = info["id"]
        title    = info.get("title", "video")
        print(f"Downloaded: '{title}'")
    return DOWNLOAD_DIR / f"{video_id}.mp4", title



def transcribe_video(video_path: Path) -> dict:
    print(f"Loading Whisper '{WHISPER_MODEL}' model (local, no API cost)...")
    model  = whisper.load_model(WHISPER_MODEL)
    print("Transcribing... (may take a few minutes for long videos)")
    result = model.transcribe(str(video_path), verbose=False, fp16=False)
    print(f"Transcription done — {len(result['segments'])} segments found")
    return result



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



def get_ffmpeg():
    """Find ffmpeg — works with imageio-ffmpeg (no system install needed)."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"   # fall back to system ffmpeg if available


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
        # Draw background rectangle
        cv2.rectangle(frame,
                      (x - padding, ly - th - padding),
                      (x + tw + padding, ly + padding),
                      bg_color, -1)
      
        cv2.putText(frame, line, (x, ly), font, font_scale, color, thickness, cv2.LINE_AA)


def add_text_overlay_opencv(video_path: Path, out_path: Path,
                             title: str, concept: str):
    """
    Add title (top) and concept caption (bottom) overlays
    using OpenCV — no ImageMagick required.
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

   
    max_chars = max(20, int(w / (14 * font_scale_caption)))
    wrapped_concept = "\n".join(textwrap.wrap(concept, max_chars))

    
    title_frames = int(fps * 3)
    frame_idx    = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        
        if frame_idx < title_frames:
            draw_text_with_background(
                frame,
                text      = title[:60],
                position  = (20, int(h * 0.06)),
                font_scale= font_scale_title,
                color     = (0, 230, 255),   # yellow
                bg_color  = (0, 0, 0),
                thickness = 2,
                padding   = 10,
            )

        
        lines      = wrapped_concept.split("\n")
        line_h     = int(32 * font_scale_caption)
        caption_y  = h - (len(lines) * line_h) - 30

        draw_text_with_background(
            frame,
            text      = wrapped_concept,
            position  = (20, caption_y),
            font_scale= font_scale_caption,
            color     = (255, 255, 255),   # white
            bg_color  = (20, 20, 20),
            thickness = 2,
            padding   = 8,
        )

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
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    tmp_video.unlink(missing_ok=True)

    if result.returncode != 0:
       
        import shutil
        shutil.copy(str(tmp_video), str(out_path))



def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


def export_short(source_video: Path, segment: dict, idx: int, crop: bool = True) -> Path:
    start    = float(segment["start_time"])
    end      = float(segment["end_time"])
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



def convert(youtube_url: str, crop_to_vert: bool = True) -> list:
    print("\nYouTube Long -> Shorts Converter  [100% FREE]")
    print("=" * 52)

    video_path, title = download_video(youtube_url)
    transcript        = transcribe_video(video_path)
    segments          = analyze_transcript(transcript, title)

    print(f"\nGenerating {len(segments)} shorts...")
    paths = []
    for i, seg in enumerate(segments, 1):
        paths.append(export_short(video_path, seg, i, crop=crop_to_vert))

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
        print("Make sure backend/.env contains: GROQ_API_KEY=gsk_...")
        print("Get a FREE key at: https://console.groq.com\n")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python processor.py <youtube_url> [--landscape]")
        sys.exit(1)

    convert(sys.argv[1], crop_to_vert="--landscape" not in sys.argv)