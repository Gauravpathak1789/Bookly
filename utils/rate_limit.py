"""
Rate limiting utilities to prevent brute force attacks
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import User
from config import config
import uuid


def check_rate_limit(user: User) -> tuple[bool, str]:
    """
    Check if user is rate limited
    Returns (is_allowed, message)
    """
    now = datetime.utcnow()
    
    # Check if account is locked
    if user.account_locked_until and user.account_locked_until > now:
        minutes_left = int((user.account_locked_until - now).total_seconds() / 60)
        return False, f"Account locked. Try again in {minutes_left} minutes."
    
    # If lock expired, reset attempts
    if user.account_locked_until and user.account_locked_until <= now:
        user.account_locked_until = None
        user.failed_login_attempts = 0
        return True, ""
    
    # Check if within rate limit window
    if user.last_failed_login:
        time_since_last_attempt = (now - user.last_failed_login).total_seconds() / 60
        
        # Reset attempts if outside window
        if time_since_last_attempt > config.LOGIN_RATE_LIMIT_WINDOW_MINUTES:
            user.failed_login_attempts = 0
            return True, ""
    
    # Check attempt count
    if user.failed_login_attempts >= config.LOGIN_RATE_LIMIT_ATTEMPTS:
        # Lock account
        user.account_locked_until = now + timedelta(minutes=config.ACCOUNT_LOCKOUT_MINUTES)
        return False, f"Too many failed attempts. Account locked for {config.ACCOUNT_LOCKOUT_MINUTES} minutes."
    
    return True, ""


def record_failed_login(user: User, db: Session):
    """Record a failed login attempt"""
    user.failed_login_attempts += 1
    user.last_failed_login = datetime.utcnow()
    
    # Check if should lock account
    if user.failed_login_attempts >= config.LOGIN_RATE_LIMIT_ATTEMPTS:
        user.account_locked_until = datetime.utcnow() + timedelta(
            minutes=config.ACCOUNT_LOCKOUT_MINUTES
        )
    
    db.commit()


def reset_failed_attempts(user: User, db: Session):
    """Reset failed login attempts after successful login"""
    user.failed_login_attempts = 0
    user.last_failed_login = None
    user.account_locked_until = None
    db.commit()


async def check_rate_limit_by_email(email: str, db: Session) -> tuple[bool, str]:
    """
    Check rate limit for an email address
    Returns (is_allowed, message)
    """
    statement = select(User).where(User.email == email)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        return True, ""  # No user, no rate limit
    
    return check_rate_limit(user)
