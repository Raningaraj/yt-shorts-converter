#!/usr/bin/env python3


import os
import sys
import subprocess
from pathlib import Path


def main():
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    
    print("\n" + "="*60)
    print("  YT Shorts Converter - Setup for Mac/Linux")
    print("="*60 + "\n")
    
    
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        sys.exit(1)
    
    print("✓ Python version OK:", sys.version.split()[0])
    
    
    print("\n[1/4] Creating virtual environment...")
    if venv_path.exists():
        print("✓ Virtual environment already exists")
    else:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("✓ Virtual environment created")
    
    
    python_exe = venv_path / "bin" / "python"
    
    
    print("\n[2/4] Upgrading pip...")
    subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    
    print("\n[3/4] Installing dependencies...")
    requirements = project_root / "requirements.txt"
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(requirements)], check=True)
    
   
    print("\n[4/4] Checking environment configuration...")
    env_file = project_root / "backend" / ".env"
    env_example = project_root / "backend" / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("⚠️  No .env file found!")
        print("✓ Copy template: cp backend/.env.example backend/.env")
        print("✓ Then edit and add your Groq API key")
    elif env_file.exists():
        print("✓ .env file found")
    
    print("\n" + "="*60)
    print("  ✅ Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Add your Groq API key to backend/.env")
    print("   Get free key from: https://console.groq.com")
    print("\n2. Run the app:")
    print("   python run.py")
    print("\n3. Open browser to:")
    print("   http://localhost:5000")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
