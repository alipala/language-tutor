#!/usr/bin/env python3
"""
Deployment verification script to test Railway deployment configuration locally.
This script verifies that all dependencies can be installed and the application can start.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(cmd, cwd=None, timeout=300):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False, result.stderr
        return True, result.stdout
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {cmd}")
        return False, "Command timed out"
    except Exception as e:
        print(f"Exception running command: {cmd} - {e}")
        return False, str(e)

def check_python_version():
    """Check if Python 3.11 is available."""
    print("Checking Python version...")
    success, output = run_command("python3 --version")
    if success:
        print(f"Python version: {output.strip()}")
        return True
    return False

def check_node_version():
    """Check if Node.js is available."""
    print("Checking Node.js version...")
    success, output = run_command("node --version")
    if success:
        print(f"Node.js version: {output.strip()}")
        return True
    return False

def test_pip_upgrade():
    """Test pip upgrade process."""
    print("Testing pip upgrade...")
    success, output = run_command("python3 -m pip install --no-cache-dir --upgrade pip==24.0")
    if success:
        print("Pip upgrade successful")
        return True
    print(f"Pip upgrade failed: {output}")
    return False

def test_python_dependencies():
    """Test Python dependencies installation."""
    print("Testing Python dependencies installation...")
    
    # First install setuptools and wheel
    success, output = run_command("python3 -m pip install --no-cache-dir setuptools==69.5.1 wheel==0.43.0")
    if not success:
        print(f"Failed to install setuptools/wheel: {output}")
        return False
    
    # Then install requirements
    success, output = run_command("python3 -m pip install --no-cache-dir -r backend/requirements.txt")
    if success:
        print("Python dependencies installed successfully")
        return True
    print(f"Python dependencies installation failed: {output}")
    return False

def test_frontend_dependencies():
    """Test frontend dependencies installation."""
    print("Testing frontend dependencies installation...")
    success, output = run_command("npm install", cwd="frontend")
    if success:
        print("Frontend dependencies installed successfully")
        return True
    print(f"Frontend dependencies installation failed: {output}")
    return False

def test_frontend_build():
    """Test frontend build process."""
    print("Testing frontend build...")
    success, output = run_command("npm run build", cwd="frontend")
    if success:
        print("Frontend build successful")
        return True
    print(f"Frontend build failed: {output}")
    return False

def test_backend_import():
    """Test if backend can be imported."""
    print("Testing backend import...")
    success, output = run_command("python3 -c 'import sys; sys.path.append(\"backend\"); import main; print(\"Backend import successful\")'")
    if success:
        print("Backend import successful")
        return True
    print(f"Backend import failed: {output}")
    return False

def main():
    """Main verification function."""
    print("=== Railway Deployment Configuration Verification ===")
    print()
    
    # Check if we're in the right directory
    if not Path("backend/requirements.txt").exists():
        print("Error: backend/requirements.txt not found. Please run this script from the project root.")
        sys.exit(1)
    
    if not Path("frontend/package.json").exists():
        print("Error: frontend/package.json not found. Please run this script from the project root.")
        sys.exit(1)
    
    tests = [
        ("Python Version Check", check_python_version),
        ("Node.js Version Check", check_node_version),
        ("Pip Upgrade Test", test_pip_upgrade),
        ("Python Dependencies Test", test_python_dependencies),
        ("Frontend Dependencies Test", test_frontend_dependencies),
        ("Frontend Build Test", test_frontend_build),
        ("Backend Import Test", test_backend_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))
    
    print("\n=== SUMMARY ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The deployment configuration should work on Railway.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
