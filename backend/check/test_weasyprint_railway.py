#!/usr/bin/env python3
"""
Test WeasyPrint functionality for Railway deployment
This script verifies that WeasyPrint can import and generate PDFs
"""

import sys
import os
from io import BytesIO

def test_weasyprint_import():
    """Test if WeasyPrint can be imported successfully"""
    try:
        import weasyprint
        print("✅ WeasyPrint imported successfully")
        return True
    except ImportError as e:
        print(f"❌ WeasyPrint import failed: {e}")
        return False

def test_weasyprint_basic_pdf():
    """Test basic PDF generation with WeasyPrint"""
    try:
        import weasyprint
        
        # Simple HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Railway Test</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: #4ECFBF; color: white; padding: 20px; border-radius: 10px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Railway WeasyPrint Test</h1>
                <p>This PDF was generated successfully on Railway!</p>
            </div>
            <p>WeasyPrint is working correctly with all system dependencies.</p>
        </body>
        </html>
        """
        
        # Generate PDF
        html_doc = weasyprint.HTML(string=html_content)
        pdf_buffer = BytesIO()
        html_doc.write_pdf(pdf_buffer)
        
        pdf_size = len(pdf_buffer.getvalue())
        print(f"✅ WeasyPrint PDF generation successful - {pdf_size} bytes")
        return True
        
    except Exception as e:
        print(f"❌ WeasyPrint PDF generation failed: {e}")
        return False

def test_system_dependencies():
    """Test if required system libraries are available"""
    try:
        import weasyprint
        from weasyprint.text.ffi import ffi, pango
        print("✅ Pango libraries loaded successfully")
        
        from weasyprint.css import get_all_computed_styles
        print("✅ CSS processing libraries loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ System dependencies test failed: {e}")
        return False

def test_jinja2_integration():
    """Test Jinja2 template rendering"""
    try:
        from jinja2 import Environment, BaseLoader
        
        template_content = """
        <html>
        <body>
            <h1>Hello {{ name }}!</h1>
            <p>Railway deployment test successful.</p>
        </body>
        </html>
        """
        
        env = Environment(loader=BaseLoader())
        template = env.from_string(template_content)
        rendered = template.render(name="Railway")
        
        print("✅ Jinja2 template rendering successful")
        return True
        
    except Exception as e:
        print(f"❌ Jinja2 integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 RAILWAY WEASYPRINT COMPATIBILITY TEST")
    print("=" * 50)
    
    tests = [
        ("WeasyPrint Import", test_weasyprint_import),
        ("System Dependencies", test_system_dependencies),
        ("Jinja2 Integration", test_jinja2_integration),
        ("PDF Generation", test_weasyprint_basic_pdf)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - WeasyPrint ready for Railway!")
        print("\n✅ DEPLOYMENT STATUS:")
        print("   - WeasyPrint imports successfully")
        print("   - System dependencies available")
        print("   - PDF generation working")
        print("   - Template rendering functional")
        print("\n🚀 Ready for Railway deployment!")
        return True
    else:
        print("❌ SOME TESTS FAILED - Check system dependencies")
        print("\n📋 TROUBLESHOOTING:")
        print("   - Ensure nixpacks.toml includes all WeasyPrint dependencies")
        print("   - Check that Railway build includes system libraries")
        print("   - Verify requirements.txt has weasyprint>=60.0")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
