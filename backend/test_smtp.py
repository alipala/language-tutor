#!/usr/bin/env python3
"""
Simple SMTP test script to debug email authentication issues
"""
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "hello@mytacoai.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "hello@mytacoai.com")

def test_smtp_connection():
    """Test SMTP connection and authentication"""
    print("🔧 Testing SMTP Connection")
    print(f"Server: {SMTP_SERVER}")
    print(f"Port: {SMTP_PORT}")
    print(f"Username: {SMTP_USERNAME}")
    print(f"Password: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'NOT SET'}")
    print("-" * 50)
    
    try:
        print("1. Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        print("✅ Connected successfully")
        
        print("2. Starting TLS...")
        server.starttls()
        print("✅ TLS started successfully")
        
        print("3. Attempting login...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("✅ Login successful!")
        
        print("4. Testing email send...")
        msg = MIMEText("This is a test email from Language Tutor SMTP test.")
        msg['Subject'] = "SMTP Test - Language Tutor"
        msg['From'] = f"Language Tutor <{FROM_EMAIL}>"
        msg['To'] = "test@example.com"  # This won't actually send
        
        # Just test the message creation, don't actually send
        print("✅ Email message created successfully")
        
        server.quit()
        print("✅ SMTP test completed successfully!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {e}")
        print("Possible causes:")
        print("- Incorrect username or password")
        print("- Account requires app-specific password")
        print("- Two-factor authentication enabled")
        print("- Account locked or suspended")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ General Error: {e}")
        return False

def test_alternative_ports():
    """Test alternative SMTP ports"""
    ports = [587, 465, 25, 2525]
    
    for port in ports:
        print(f"\n🔧 Testing port {port}...")
        try:
            if port == 465:
                # SSL connection
                server = smtplib.SMTP_SSL(SMTP_SERVER, port)
                print(f"✅ SSL connection successful on port {port}")
            else:
                # Regular connection with STARTTLS
                server = smtplib.SMTP(SMTP_SERVER, port)
                server.starttls()
                print(f"✅ STARTTLS connection successful on port {port}")
            
            server.quit()
            
        except Exception as e:
            print(f"❌ Port {port} failed: {e}")

if __name__ == "__main__":
    print("🚀 Language Tutor SMTP Test")
    print("=" * 50)
    
    if not SMTP_PASSWORD:
        print("❌ SMTP_PASSWORD environment variable not set!")
        exit(1)
    
    # Test main configuration
    success = test_smtp_connection()
    
    if not success:
        print("\n🔧 Testing alternative configurations...")
        test_alternative_ports()
    
    print("\n" + "=" * 50)
    print("SMTP test completed.")
