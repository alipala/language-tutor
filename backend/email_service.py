import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "hello@mytacoai.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "hello@mytacoai.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.mytacoai.com")

def create_verification_email_template(name: str, verification_link: str) -> str:
    """Create a professional HTML email template for email verification"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email - Language Tutor</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 12px;
                padding: 40px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 28px;
                font-weight: bold;
                color: #4ECFBF;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 24px;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 20px;
            }}
            .content {{
                font-size: 16px;
                line-height: 1.6;
                color: #4a5568;
                margin-bottom: 30px;
            }}
            .verify-button {{
                display: inline-block;
                background-color: #4ECFBF;
                color: white;
                padding: 14px 28px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                text-align: center;
                margin: 20px 0;
                transition: background-color 0.3s ease;
            }}
            .verify-button:hover {{
                background-color: #3bb3a3;
            }}
            .alternative-link {{
                font-size: 14px;
                color: #718096;
                margin-top: 20px;
                padding: 15px;
                background-color: #f7fafc;
                border-radius: 6px;
                word-break: break-all;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                font-size: 14px;
                color: #718096;
                text-align: center;
            }}
            .security-note {{
                background-color: #fef5e7;
                border-left: 4px solid #f6ad55;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🌟 Language Tutor</div>
                <h1 class="title">Verify Your Email Address</h1>
            </div>
            
            <div class="content">
                <p>Hi {name},</p>
                
                <p>Welcome to Language Tutor! We're excited to help you on your language learning journey.</p>
                
                <p>To get started and access all features, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center;">
                    <a href="{verification_link}" class="verify-button">Verify Email Address</a>
                </div>
                
                <div class="security-note">
                    <strong>🔒 Security Note:</strong> This verification link will expire in 24 hours for your security.
                </div>
                
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <div class="alternative-link">
                    {verification_link}
                </div>
                
                <p>Once verified, you'll be able to:</p>
                <ul>
                    <li>✨ Access unlimited conversation practice</li>
                    <li>📊 Track your learning progress</li>
                    <li>🎯 Create personalized learning plans</li>
                    <li>🏆 Earn achievements and maintain streaks</li>
                </ul>
            </div>
            
            <div class="footer">
                <p>If you didn't create an account with Language Tutor, you can safely ignore this email.</p>
                <p>Need help? Contact us at <a href="mailto:hello@mytacoai.com" style="color: #4ECFBF;">hello@mytacoai.com</a></p>
                <p>&copy; 2025 Language Tutor. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

def create_verification_email_text(name: str, verification_link: str) -> str:
    """Create a plain text version of the verification email"""
    return f"""
Hi {name},

Welcome to Language Tutor! We're excited to help you on your language learning journey.

To get started and access all features, please verify your email address by visiting this link:

{verification_link}

This verification link will expire in 24 hours for your security.

Once verified, you'll be able to:
- Access unlimited conversation practice
- Track your learning progress  
- Create personalized learning plans
- Earn achievements and maintain streaks

If you didn't create an account with Language Tutor, you can safely ignore this email.

Need help? Contact us at hello@mytacoai.com

Best regards,
The Language Tutor Team
"""

async def send_verification_email(email: str, name: str, verification_token: str) -> bool:
    """Send email verification email to user"""
    try:
        print(f"[EMAIL] Attempting to send verification email to {email}")
        print(f"[EMAIL] SMTP Config - Server: {SMTP_SERVER}, Port: {SMTP_PORT}, Username: {SMTP_USERNAME}")
        print(f"[EMAIL] Frontend URL: {FRONTEND_URL}")
        
        # Create verification link
        verification_link = f"{FRONTEND_URL}/auth/verify-email?token={verification_token}"
        print(f"[EMAIL] Verification link: {verification_link}")
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Verify Your Email - Language Tutor"
        msg['From'] = f"Language Tutor <{FROM_EMAIL}>"
        msg['To'] = email
        
        # Create both plain text and HTML versions
        text_content = create_verification_email_text(name, verification_link)
        html_content = create_verification_email_template(name, verification_link)
        
        # Attach both versions
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email with detailed error handling
        print(f"[EMAIL] Connecting to SMTP server...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print(f"[EMAIL] Starting TLS...")
            server.starttls()
            print(f"[EMAIL] Logging in with username: {SMTP_USERNAME}")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print(f"[EMAIL] Sending message...")
            server.send_message(msg)
        
        print(f"✅ Verification email sent successfully to {email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error for {email}: {str(e)}")
        print(f"[EMAIL] Check SMTP credentials - Username: {SMTP_USERNAME}, Server: {SMTP_SERVER}")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error sending verification email to {email}: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ General error sending verification email to {email}: {str(e)}")
        return False

async def send_welcome_email(email: str, name: str) -> bool:
    """Send welcome email after successful verification"""
    try:
        # Create welcome email content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Language Tutor!</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 12px;
                    padding: 40px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #4ECFBF;
                    margin-bottom: 10px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: 600;
                    color: #2d3748;
                    margin-bottom: 20px;
                }}
                .content {{
                    font-size: 16px;
                    line-height: 1.6;
                    color: #4a5568;
                    margin-bottom: 30px;
                }}
                .cta-button {{
                    display: inline-block;
                    background-color: #4ECFBF;
                    color: white;
                    padding: 14px 28px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    text-align: center;
                    margin: 20px 0;
                }}
                .feature-list {{
                    background-color: #f7fafc;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e2e8f0;
                    font-size: 14px;
                    color: #718096;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🎉 Language Tutor</div>
                    <h1 class="title">Welcome to Your Language Learning Journey!</h1>
                </div>
                
                <div class="content">
                    <p>Hi {name},</p>
                    
                    <p>Congratulations! Your email has been verified and your Language Tutor account is now active.</p>
                    
                    <div class="feature-list">
                        <h3>🚀 What's Next?</h3>
                        <ul>
                            <li><strong>Take a Speaking Assessment</strong> - Discover your current language level</li>
                            <li><strong>Start Conversations</strong> - Practice with our AI language tutor</li>
                            <li><strong>Create Learning Plans</strong> - Set goals and track your progress</li>
                            <li><strong>Build Streaks</strong> - Maintain daily practice for maximum improvement</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{FRONTEND_URL}/assessment/speaking" class="cta-button">Start Your First Assessment</a>
                    </div>
                    
                    <p>We're here to support you every step of the way. Happy learning!</p>
                </div>
                
                <div class="footer">
                    <p>Questions? We're here to help at <a href="mailto:hello@mytacoai.com" style="color: #4ECFBF;">hello@mytacoai.com</a></p>
                    <p>&copy; 2025 Language Tutor. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Hi {name},

Congratulations! Your email has been verified and your Language Tutor account is now active.

What's Next?
- Take a Speaking Assessment - Discover your current language level
- Start Conversations - Practice with our AI language tutor  
- Create Learning Plans - Set goals and track your progress
- Build Streaks - Maintain daily practice for maximum improvement

Get started: {FRONTEND_URL}/assessment/speaking

We're here to support you every step of the way. Happy learning!

Questions? We're here to help at hello@mytacoai.com

Best regards,
The Language Tutor Team
        """
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "🎉 Welcome to Language Tutor - Let's Start Learning!"
        msg['From'] = f"Language Tutor <{FROM_EMAIL}>"
        msg['To'] = email
        
        # Attach both versions
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Welcome email sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending welcome email to {email}: {str(e)}")
        return False
