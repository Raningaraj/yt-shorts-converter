#!/usr/bin/env python3


import os
import sys
import subprocess
import platform
from pathlib import Path


def main():
   
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    backend_path = project_root / "backend"
    
    print("\n" + "="*50)
    print("  YT Shorts Converter - Starting...")
    print("="*50 + "\n")
    
    
    if not venv_path.exists():
        print("❌ ERROR: Virtual environment not found!")
        print("\nSetup instructions:")
        print("  1. python -m venv venv")
        print("  2. venv\\Scripts\\pip install -r requirements.txt (Windows)")
        print("     OR")
        print("     source venv/bin/activate && pip install -r requirements.txt (Mac/Linux)")
        sys.exit(1)
    
  
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"
    
    if not python_exe.exists():
        print(f"❌ ERROR: Python executable not found at {python_exe}")
        sys.exit(1)
    
  
    os.chdir(backend_path)
    
    print(f"📁 Working directory: {backend_path}")
    print(f"🐍 Using Python: {python_exe}\n")
    print("="*50)
    print("  🚀 Starting Flask server...")
    print("  Open your browser to: http://localhost:5000")
    print("="*50 + "\n")
    
   
    try:
        subprocess.run([str(python_exe), "app.py"], check=False)
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
