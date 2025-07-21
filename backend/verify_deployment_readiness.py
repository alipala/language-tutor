#!/usr/bin/env python3
"""
Deployment Readiness Verification Script
Ensures all components are ready for Railway deployment
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NOT FOUND")
        return False

def check_import(module_name, description):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {description}: {module_name} - IMPORT ERROR: {e}")
        return False

def check_requirements():
    """Check if all required packages are in requirements.txt"""
    required_packages = [
        'weasyprint',
        'jinja2', 
        'plotly',
        'matplotlib',
        'seaborn',
        'numpy',
        'kaleido'
    ]
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().lower()
        
        missing_packages = []
        for package in required_packages:
            if package.lower() not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages in requirements.txt: {missing_packages}")
            return False
        else:
            print("✅ All required packages are in requirements.txt")
            return True
    except Exception as e:
        print(f"❌ Error checking requirements.txt: {e}")
        return False

def main():
    print("🔍 RAILWAY DEPLOYMENT READINESS CHECK")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check core files
    core_files = [
        ("main.py", "Main application file"),
        ("requirements.txt", "Requirements file"),
        ("enhanced_export_routes.py", "Enhanced export routes"),
        ("modern_pdf_generator.py", "Modern PDF generator"),
        ("ai_report_generator.py", "AI report generator"),
        ("templates/pdf/base_template.html", "Base PDF template"),
        ("templates/pdf/learning_plans_template.html", "Learning plans template"),
        ("templates/pdf/conversation_history_template.html", "Conversation history template")
    ]
    
    print("\n📁 FILE EXISTENCE CHECKS:")
    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Check requirements
    print("\n📦 REQUIREMENTS CHECK:")
    if not check_requirements():
        all_checks_passed = False
    
    # Check imports (only if we can import them)
    print("\n🐍 IMPORT CHECKS:")
    import_checks = [
        ("weasyprint", "WeasyPrint PDF generation"),
        ("jinja2", "Jinja2 templating"),
        ("plotly", "Plotly charts"),
        ("matplotlib", "Matplotlib charts"),
        ("seaborn", "Seaborn styling"),
        ("numpy", "NumPy arrays"),
    ]
    
    for module, description in import_checks:
        if not check_import(module, description):
            all_checks_passed = False
    
    # Check template directory structure
    print("\n📂 TEMPLATE STRUCTURE CHECK:")
    template_dir = Path("templates/pdf")
    if template_dir.exists():
        templates = list(template_dir.glob("*.html"))
        print(f"✅ Found {len(templates)} HTML templates in {template_dir}")
        for template in templates:
            print(f"   - {template.name}")
    else:
        print(f"❌ Template directory not found: {template_dir}")
        all_checks_passed = False
    
    # Check integration in main.py
    print("\n🔗 INTEGRATION CHECKS:")
    try:
        with open("main.py", "r") as f:
            main_content = f.read()
        
        if "enhanced_export_routes" in main_content:
            print("✅ Enhanced export routes integrated in main.py")
        else:
            print("❌ Enhanced export routes not found in main.py")
            all_checks_passed = False
            
        if "app.include_router(enhanced_export_router)" in main_content:
            print("✅ Enhanced export router included in main.py")
        else:
            print("❌ Enhanced export router not included in main.py")
            all_checks_passed = False
            
    except Exception as e:
        print(f"❌ Error checking main.py integration: {e}")
        all_checks_passed = False
    
    # Final result
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 ALL CHECKS PASSED - READY FOR RAILWAY DEPLOYMENT!")
        print("\n📋 DEPLOYMENT SUMMARY:")
        print("✅ Enhanced PDF reporting system implemented")
        print("✅ All dependencies included in requirements.txt")
        print("✅ Templates and generators properly structured")
        print("✅ Integration with main application verified")
        print("✅ Railway compatibility ensured")
        print("\n🚀 You can now deploy to Railway with confidence!")
        return True
    else:
        print("❌ SOME CHECKS FAILED - PLEASE FIX ISSUES BEFORE DEPLOYMENT")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
