
from sqlalchemy import TIMESTAMP, Column, Integer, String, Boolean, text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

import uuid
from datetime import datetime
from database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    # Role-Based Access Control
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Email Verification
    verification_token = Column(String, nullable=True, unique=True)
    verification_token_expiry = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Password Reset
    reset_token = Column(String, nullable=True, unique=True)
    reset_token_expiry = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Rate Limiting
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_failed_login = Column(TIMESTAMP(timezone=True), nullable=True)
    account_locked_until = Column(TIMESTAMP(timezone=True), nullable=True)
    
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.uid", ondelete="CASCADE"), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    device_info = Column(String, nullable=True)  # User agent, device name
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")


class Book(Base):
    __tablename__ = "books"
    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    author = Column(String, nullable=False)
    title = Column(String, nullable=False)
    publisher = Column(String, nullable=False)
    published_date = Column(String, nullable=False)
    page_count = Column(Integer, nullable=False)
    language = Column(String, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )