"""
Email utility for sending verification, password reset, and notification emails
"""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
from typing import List
from config import config
import secrets


# Email configuration
email_conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=config.MAIL_STARTTLS,
    MAIL_SSL_TLS=config.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Create FastMail instance
fm = FastMail(email_conf)


def generate_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


async def send_verification_email(email: EmailStr, username: str, token: str):
    """Send email verification link"""
    verification_url = f"{config.FRONTEND_URL}/verify-email?token={token}"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Welcome to Bookly, {username}!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p>
                <a href="{verification_url}" 
                   style="background-color: #4CAF50; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Verify Email Address
                </a>
            </p>
            <p>Or copy this link to your browser:</p>
            <p style="color: #666; font-size: 14px;">{verification_url}</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">
                This link will expire in {config.VERIFICATION_TOKEN_EXPIRE_HOURS} hours.<br>
                If you didn't create this account, please ignore this email.
            </p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Verify Your Email - Bookly",
        recipients=[email],
        body=html_body,
        subtype="html"
    )
    
    await fm.send_message(message)


async def send_password_reset_email(email: EmailStr, username: str, token: str):
    """Send password reset link"""
    reset_url = f"{config.FRONTEND_URL}/reset-password?token={token}"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Password Reset Request</h2>
            <p>Hello {username},</p>
            <p>We received a request to reset your password. Click the link below to set a new password:</p>
            <p>
                <a href="{reset_url}" 
                   style="background-color: #2196F3; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p>Or copy this link to your browser:</p>
            <p style="color: #666; font-size: 14px;">{reset_url}</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">
                This link will expire in {config.RESET_TOKEN_EXPIRE_HOURS} hour(s).<br>
                If you didn't request this reset, please ignore this email and your password will remain unchanged.
            </p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Password Reset - Bookly",
        recipients=[email],
        body=html_body,
        subtype="html"
    )
    
    await fm.send_message(message)


async def send_2fa_enabled_notification(email: EmailStr, username: str):
    """Notify user that 2FA has been enabled"""
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Two-Factor Authentication Enabled</h2>
            <p>Hello {username},</p>
            <p>Two-factor authentication has been successfully enabled on your account.</p>
            <p>From now on, you'll need to enter a verification code from your authenticator app when logging in.</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">
                If you didn't enable 2FA, please contact support immediately.
            </p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="2FA Enabled - Bookly",
        recipients=[email],
        body=html_body,
        subtype="html"
    )
    
    await fm.send_message(message)


async def send_login_alert(email: EmailStr, username: str, device_info: str):
    """Send alert for new login"""
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>New Login Detected</h2>
            <p>Hello {username},</p>
            <p>A new login to your account was detected:</p>
            <p><strong>Device:</strong> {device_info}</p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">
                If this wasn't you, please reset your password immediately.
            </p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="New Login Alert - Bookly",
        recipients=[email],
        body=html_body,
        subtype="html"
    )
    
    await fm.send_message(message)
