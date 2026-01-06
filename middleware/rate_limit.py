"""
Rate limiting middleware to prevent brute force attacks
"""
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
from models import User
from config import config


async def check_rate_limit(email: str, db: Session) -> User:
    """
    Check if user has exceeded login rate limit
    Returns user if allowed, raises HTTPException if rate limited
    """
    statement = select(User).where(User.email == email)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        # User doesn't exist, but don't reveal that for security
        return None
    
    now = datetime.utcnow()
    
    # Check if account is locked
    if user.account_locked_until and user.account_locked_until > now:
        remaining_minutes = int((user.account_locked_until - now).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to too many failed login attempts. Try again in {remaining_minutes} minutes."
        )
    
    # Reset lock if time has passed
    if user.account_locked_until and user.account_locked_until <= now:
        user.account_locked_until = None
        user.failed_login_attempts = 0
        db.commit()
    
    # Check rate limiting window
    if user.last_failed_login:
        time_since_last_attempt = now - user.last_failed_login
        window = timedelta(minutes=config.LOGIN_RATE_LIMIT_WINDOW_MINUTES)
        
        # If last attempt was outside the window, reset counter
        if time_since_last_attempt > window:
            user.failed_login_attempts = 0
            db.commit()
    
    return user


def record_failed_login(user: User, db: Session):
    """Record a failed login attempt and lock account if threshold exceeded"""
    if not user:
        return
    
    user.failed_login_attempts += 1
    user.last_failed_login = datetime.utcnow()
    
    # Lock account if threshold exceeded
    if user.failed_login_attempts >= config.LOGIN_RATE_LIMIT_ATTEMPTS:
        user.account_locked_until = datetime.utcnow() + timedelta(
            minutes=config.ACCOUNT_LOCKOUT_MINUTES
        )
    
    db.commit()


def reset_failed_login_attempts(user: User, db: Session):
    """Reset failed login attempts after successful login"""
    if not user:
        return
    
    user.failed_login_attempts = 0
    user.last_failed_login = None
    user.account_locked_until = None
    db.commit()


# Simple in-memory rate limiter for endpoints (can be replaced with Redis for production)
class InMemoryRateLimiter:
    """Simple in-memory rate limiter for various endpoints"""
    
    def __init__(self):
        self.requests = {}  # {ip: [(timestamp, endpoint), ...]}
    
    def is_rate_limited(
        self,
        identifier: str,
        max_requests: int = 10,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if identifier has exceeded rate limit
        identifier: Usually IP address or user ID
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                (ts, endpoint) for ts, endpoint in self.requests[identifier]
                if ts > cutoff
            ]
        else:
            self.requests[identifier] = []
        
        # Check if rate limited
        if len(self.requests[identifier]) >= max_requests:
            return True
        
        # Add current request
        self.requests[identifier].append((now, ""))
        return False
    
    def cleanup(self):
        """Periodically cleanup old entries"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=10)
        
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                (ts, endpoint) for ts, endpoint in self.requests[identifier]
                if ts > cutoff
            ]
            if not self.requests[identifier]:
                del self.requests[identifier]


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for forwarded header first (for reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct connection
    return request.client.host if request.client else "unknown"
