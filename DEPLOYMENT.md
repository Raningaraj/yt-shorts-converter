# Deployment Guide

## Best free option
This project is best deployed with a Docker container on Fly.io using the free tier.

## What was added
- `Dockerfile` for a Python/Flask container with `ffmpeg` and required libraries
- `.dockerignore` to keep build context small
- `fly.toml` for Fly.io deployment configuration

## Next setup steps
1. Install Docker and Fly CLI.
2. Run in the project root:
   ```bash
   fly auth login
   fly apps create
   fly deploy
   ```
3. Add your Groq API key in `backend/.env`:
   ```bash
   cp backend/.env.example backend/.env
   # then edit backend/.env and set GROQ_API_KEY
   ```

## Important notes
- The app listens on port `8080` in Docker and Fly.
- `backend/app.py` will serve the frontend from `backend/frontend`.
- Keep in mind that Whisper transcription and video processing are CPU-heavy; performance may be slow on free tier VMs.

## Optional alternatives
- If Fly.io is not a good fit, the same `Dockerfile` can also be used on Render, Railway, or another Docker-friendly host.
