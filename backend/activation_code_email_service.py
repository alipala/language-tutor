"""
Activation Code Email Service
Sends invitation emails to institutions with activation codes
"""

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


def create_activation_code_email_html(
    institution_name: str,
    activation_code: str,
    trial_duration_days: Optional[int],
    max_tutors: int,
    max_learners: int,
    target_plan: str
) -> str:
    """Create HTML email template for activation code invitation"""
    
    # Build signup URL with pre-filled code
    signup_url = f"{FRONTEND_URL}/institution/signup?code={activation_code}"
    
    # Determine plan display name
    plan_display = {
        "starter": "Starter",
        "professional": "Professional", 
        "enterprise": "Enterprise"
    }.get(target_plan, target_plan.title())
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Language Tutor Activation Code</title>
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
                font-size: 32px;
                font-weight: bold;
                color: #4ECFBF;
                margin-bottom: 10px;
            }}
            .title {{
                font-size: 26px;
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 20px;
            }}
            .content {{
                font-size: 16px;
                line-height: 1.8;
                color: #4a5568;
                margin-bottom: 30px;
            }}
            .code-box {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                margin: 30px 0;
                box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
            }}
            .code {{
                color: white;
                font-size: 36px;
                font-weight: bold;
                letter-spacing: 3px;
                margin: 0;
                font-family: 'Courier New', monospace;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            }}
            .code-label {{
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .plan-details {{
                background-color: #f7fafc;
                padding: 25px;
                border-radius: 10px;
                margin: 25px 0;
                border-left: 4px solid #4ECFBF;
            }}
            .plan-details h3 {{
                color: #2d3748;
                margin-top: 0;
                margin-bottom: 15px;
                font-size: 18px;
            }}
            .plan-details ul {{
                margin: 0;
                padding-left: 20px;
            }}
            .plan-details li {{
                margin: 10px 0;
                color: #4a5568;
            }}
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, #4ECFBF 0%, #44b3a3 100%);
                color: white;
                padding: 16px 40px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 18px;
                text-align: center;
                margin: 25px 0;
                box-shadow: 0 4px 12px rgba(78, 207, 191, 0.3);
                transition: transform 0.2s ease;
            }}
            .cta-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 16px rgba(78, 207, 191, 0.4);
            }}
            .alternative-link {{
                font-size: 13px;
                color: #718096;
                margin-top: 20px;
                padding: 15px;
                background-color: #f7fafc;
                border-radius: 6px;
                word-break: break-all;
                border: 1px dashed #cbd5e0;
            }}
            .expiry-notice {{
                background-color: #fff5f5;
                border-left: 4px solid #fc8181;
                padding: 15px;
                margin: 25px 0;
                border-radius: 4px;
                font-size: 14px;
            }}
            .features {{
                margin: 25px 0;
            }}
            .feature-item {{
                display: flex;
                align-items: start;
                margin: 15px 0;
            }}
            .feature-icon {{
                font-size: 24px;
                margin-right: 12px;
                flex-shrink: 0;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 25px;
                border-top: 1px solid #e2e8f0;
                font-size: 14px;
                color: #718096;
                text-align: center;
            }}
            .footer a {{
                color: #4ECFBF;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎓 Language Tutor</div>
                <h1 class="title">Welcome to Language Tutor!</h1>
            </div>
            
            <div class="content">
                <p>Hello <strong>{institution_name}</strong>,</p>
                
                <p>We're excited to welcome you to Language Tutor! Your institutional activation code has been generated and is ready to use.</p>
                
                <div class="code-box">
                    <div class="code-label">Your Activation Code</div>
                    <h1 class="code">{activation_code}</h1>
                </div>
                
                <div class="plan-details">
                    <h3>📋 Your Plan Details</h3>
                    <ul>
                        <li><strong>Plan:</strong> {plan_display}</li>
                        {"<li><strong>Trial Period:</strong> " + str(trial_duration_days) + " days</li>" if trial_duration_days else ""}
                        <li><strong>Maximum Tutors:</strong> {max_tutors}</li>
                        <li><strong>Maximum Learners:</strong> {max_learners}</li>
                    </ul>
                </div>
                
                <div class="features">
                    <h3>✨ What You'll Get:</h3>
                    <div class="feature-item">
                        <span class="feature-icon">🗣️</span>
                        <div>
                            <strong>AI-Powered Conversations</strong><br>
                            <span style="color: #718096; font-size: 14px;">Practice speaking with advanced AI tutors</span>
                        </div>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📊</span>
                        <div>
                            <strong>Progress Tracking</strong><br>
                            <span style="color: #718096; font-size: 14px;">Monitor learner progress and achievements</span>
                        </div>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🎯</span>
                        <div>
                            <strong>Personalized Learning Plans</strong><br>
                            <span style="color: #718096; font-size: 14px;">Customized paths for each learner</span>
                        </div>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">👥</span>
                        <div>
                            <strong>Multi-User Management</strong><br>
                            <span style="color: #718096; font-size: 14px;">Manage tutors and learners from one dashboard</span>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <a href="{signup_url}" class="cta-button">Complete Your Signup →</a>
                </div>
                
                <p style="text-align: center; color: #718096; font-size: 14px; margin-top: 15px;">
                    Or copy and paste this link into your browser:
                </p>
                <div class="alternative-link">
                    {signup_url}
                </div>
                
                <div class="expiry-notice">
                    <strong>⏰ Important:</strong> This activation code expires in 30 days. Please complete your signup before the expiration date to ensure uninterrupted access.
                </div>
                
                <p>Once you complete the signup process, you'll be able to:</p>
                <ul style="color: #4a5568;">
                    <li>Add tutors and learners to your institution</li>
                    <li>Access the admin dashboard</li>
                    <li>Configure institution settings</li>
                    <li>Start using Language Tutor immediately</li>
                </ul>
            </div>
            
            <div class="footer">
                <p><strong>Need help getting started?</strong></p>
                <p>Our support team is here to assist you at <a href="mailto:hello@mytacoai.com">hello@mytacoai.com</a></p>
                <p style="margin-top: 20px;">&copy; 2025 Language Tutor. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """


def create_activation_code_email_text(
    institution_name: str,
    activation_code: str,
    trial_duration_days: Optional[int],
    max_tutors: int,
    max_learners: int,
    target_plan: str
) -> str:
    """Create plain text version of activation code email"""
    
    signup_url = f"{FRONTEND_URL}/institution/signup?code={activation_code}"
    
    plan_display = {
        "starter": "Starter",
        "professional": "Professional",
        "enterprise": "Enterprise"
    }.get(target_plan, target_plan.title())
    
    trial_text = f"\n- Trial Period: {trial_duration_days} days" if trial_duration_days else ""
    
    return f"""
Welcome to Language Tutor!

Hello {institution_name},

We're excited to welcome you to Language Tutor! Your institutional activation code has been generated and is ready to use.

YOUR ACTIVATION CODE
====================
{activation_code}
====================

YOUR PLAN DETAILS
-----------------
- Plan: {plan_display}{trial_text}
- Maximum Tutors: {max_tutors}
- Maximum Learners: {max_learners}

WHAT YOU'LL GET
---------------
🗣️ AI-Powered Conversations - Practice speaking with advanced AI tutors
📊 Progress Tracking - Monitor learner progress and achievements
🎯 Personalized Learning Plans - Customized paths for each learner
👥 Multi-User Management - Manage tutors and learners from one dashboard

COMPLETE YOUR SIGNUP
--------------------
Click here to get started: {signup_url}

⏰ IMPORTANT: This activation code expires in 30 days. Please complete your signup before the expiration date.

Once you complete the signup process, you'll be able to:
- Add tutors and learners to your institution
- Access the admin dashboard
- Configure institution settings
- Start using Language Tutor immediately

NEED HELP?
----------
Our support team is here to assist you at hello@mytacoai.com

Best regards,
The Language Tutor Team

© 2025 Language Tutor. All rights reserved.
    """


async def send_activation_code_email(
    institution_email: str,
    activation_code: str,
    institution_name: str,
    trial_duration_days: Optional[int],
    max_tutors: int,
    max_learners: int,
    target_plan: str
) -> bool:
    """
    Send activation code email to institution
    
    Args:
        institution_email: Email address of the institution contact
        activation_code: Generated activation code
        institution_name: Name of the institution
        trial_duration_days: Trial duration in days (None if not trial)
        max_tutors: Maximum number of tutors allowed
        max_learners: Maximum number of learners allowed
        target_plan: Target subscription plan (starter/professional/enterprise)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        print(f"[ACTIVATION EMAIL] Sending to {institution_email} for {institution_name}")
        print(f"[ACTIVATION EMAIL] Code: {activation_code}")
        print(f"[ACTIVATION EMAIL] SMTP Config - Server: {SMTP_SERVER}, Port: {SMTP_PORT}")
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Your Language Tutor Activation Code - {institution_name}"
        msg['From'] = f"Language Tutor <{FROM_EMAIL}>"
        msg['To'] = institution_email
        
        # Create both plain text and HTML versions
        text_content = create_activation_code_email_text(
            institution_name=institution_name,
            activation_code=activation_code,
            trial_duration_days=trial_duration_days,
            max_tutors=max_tutors,
            max_learners=max_learners,
            target_plan=target_plan
        )
        
        html_content = create_activation_code_email_html(
            institution_name=institution_name,
            activation_code=activation_code,
            trial_duration_days=trial_duration_days,
            max_tutors=max_tutors,
            max_learners=max_learners,
            target_plan=target_plan
        )
        
        # Attach both versions
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        print(f"[ACTIVATION EMAIL] Connecting to SMTP server...")
        
        if SMTP_PORT == 465:
            # Use SSL connection
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                print(f"[ACTIVATION EMAIL] Using SSL connection on port {SMTP_PORT}")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                print(f"[ACTIVATION EMAIL] Sending message...")
                server.send_message(msg)
        else:
            # Use STARTTLS connection
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                print(f"[ACTIVATION EMAIL] Starting TLS on port {SMTP_PORT}...")
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                print(f"[ACTIVATION EMAIL] Sending message...")
                server.send_message(msg)
        
        print(f"✅ Activation code email sent successfully to {institution_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error for {institution_email}: {str(e)}")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error sending activation email to {institution_email}: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ General error sending activation email to {institution_email}: {str(e)}")
        return False
