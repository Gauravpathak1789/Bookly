"""
Enhanced Authentication Router with:
- Email Verification
- Password Reset
- Refresh Tokens
- Two-Factor Authentication (2FA)
- Rate Limiting
- Role-Based Access Control
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional
import uuid
import json

from database import get_db
from models import User, RefreshToken, UserRole
from schemas import (
    UserCreate, UserRead, UserLogin, Token, TokenData, RefreshTokenRequest,
    EmailVerificationRequest, ResendVerificationEmail,
    PasswordResetRequest, PasswordResetConfirm, PasswordChange
)
from config import config
from passlib.context import CryptContext
from jose import JWTError, jwt

# Import utilities
from utils.email import (
    send_verification_email, send_password_reset_email,
    send_password_changed_notification,
    generate_token
)
from utils.rate_limit import check_rate_limit, record_failed_login, reset_failed_attempts
from utils.rbac import require_admin, require_moderator_or_admin

# Router setup
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# JWT settings
SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES


# ==================== Helper Functions ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: uuid.UUID, db: Session, device_info: str = None) -> str:
    """Create a refresh token and store in database"""
    token = generate_token(64)
    expires_at = datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
        device_info=device_info
    )
    
    db.add(refresh_token)
    db.commit()
    
    return token


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=uuid.UUID(user_id))
    except JWTError:
        raise credentials_exception
    
    statement = select(User).where(User.uid == token_data.user_id)
    user = db.execute(statement).scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get the current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first."
        )
    return current_user


# ==================== Registration & Login ====================

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and send verification email"""
    
    # Check if username exists
    statement = select(User).where(User.username == user.username)
    existing_user = db.execute(statement).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    statement = select(User).where(User.email == user.email)
    existing_email = db.execute(statement).scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user.password)
    verification_token = generate_token()
    token_expiry = datetime.utcnow() + timedelta(hours=config.VERIFICATION_TOKEN_EXPIRE_HOURS)
    
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        verification_token=verification_token,
        verification_token_expiry=token_expiry
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    try:
        await send_verification_email(user.email, user.username, verification_token)
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        # Continue anyway - user is registered
    
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None)
):
    """Login user and return access + refresh tokens"""
    
    # Check rate limit
    statement = select(User).where(User.email == form_data.username)
    user = db.execute(statement).scalar_one_or_none()
    
    if user:
        is_allowed, message = check_rate_limit(user)
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message
            )
    
    # Verify credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        if user:
            record_failed_login(user, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Reset failed attempts
    reset_failed_attempts(user, db)
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.uid)},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(user.uid, db, user_agent)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Get new access token using refresh token"""
    
    statement = select(RefreshToken).where(
        RefreshToken.token == refresh_request.refresh_token
    )
    refresh_token = db.execute(statement).scalar_one_or_none()
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    if refresh_token.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    if refresh_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Get user
    statement = select(User).where(User.uid == refresh_token.user_id)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.uid)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
    refresh_request: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout and revoke refresh token"""
    
    statement = select(RefreshToken).where(
        RefreshToken.token == refresh_request.refresh_token,
        RefreshToken.user_id == current_user.uid
    )
    refresh_token = db.execute(statement).scalar_one_or_none()
    
    if refresh_token:
        refresh_token.is_revoked = True
        db.commit()
    
    return {"message": "Successfully logged out"}


# ==================== Email Verification ====================

@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """Verify email using token from email"""
    
    statement = select(User).where(User.verification_token == request.token)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    if user.verification_token_expiry < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )
    
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expiry = None
    db.commit()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification_email(
    request: ResendVerificationEmail,
    db: Session = Depends(get_db)
):
    """Resend verification email"""
    
    statement = select(User).where(User.email == request.email)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification link has been sent"}
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Generate new token
    verification_token = generate_token()
    token_expiry = datetime.utcnow() + timedelta(hours=config.VERIFICATION_TOKEN_EXPIRE_HOURS)
    
    user.verification_token = verification_token
    user.verification_token_expiry = token_expiry
    db.commit()
    
    try:
        await send_verification_email(user.email, user.username, verification_token)
    except Exception as e:
        print(f"Failed to send verification email: {e}")
    
    return {"message": "If the email exists, a verification link has been sent"}


# ==================== Password Reset ====================

@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset email"""
    
    statement = select(User).where(User.email == request.email)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_token()
    token_expiry = datetime.utcnow() + timedelta(hours=config.RESET_TOKEN_EXPIRE_HOURS)
    
    user.reset_token = reset_token
    user.reset_token_expiry = token_expiry
    db.commit()
    
    try:
        await send_password_reset_email(user.email, user.username, reset_token)
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using token from email"""
    
    statement = select(User).where(User.reset_token == request.token)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    if user.reset_token_expiry < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    user.failed_login_attempts = 0  # Reset rate limit
    db.commit()
    
    try:
        await send_password_changed_notification(user.email, user.username)
    except Exception as e:
        print(f"Failed to send notification email: {e}")
    
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    request: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change password for logged-in user"""
    
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    try:
        await send_password_changed_notification(current_user.email, current_user.username)
    except Exception as e:
        print(f"Failed to send notification email: {e}")
    
    return {"message": "Password changed successfully"}


# ==================== User Management ====================

@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user


@router.get("/users/{user_id}", response_model=UserRead)
async def read_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Get user by ID (requires verification)"""
    
    statement = select(User).where(User.uid == user_id)
    user = db.execute(statement).scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# ==================== Admin Endpoints ====================

@router.get("/admin/users", response_model=list[UserRead])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users (admin only)"""
    
    statement = select(User).offset(skip).limit(limit)
    users = db.execute(statement).scalars().all()
    
    return users


@router.patch("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: uuid.UUID,
    role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user role (admin only)"""
    
    statement = select(User).where(User.uid == user_id)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = role
    db.commit()
    
    return {"message": f"User role updated to {role.value}"}


@router.patch("/admin/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator_or_admin)
):
    """Deactivate user account (moderator or admin)"""
    
    statement = select(User).where(User.uid == user_id)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.uid == current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}
