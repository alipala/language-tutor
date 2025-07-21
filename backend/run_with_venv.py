#!/usr/bin/env python3
"""
Run script that ensures the virtual environment is used correctly
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Get the backend directory
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    venv_python = project_root / "venv" / "bin" / "python"
    
    # Check if virtual environment exists
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run: python -m venv venv")
        sys.exit(1)
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Run uvicorn with the virtual environment Python
    cmd = [
        str(venv_python), 
        "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ]
    
    print("🚀 Starting server with virtual environment...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
