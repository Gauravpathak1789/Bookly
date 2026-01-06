"""
OAuth 2.0 Social Login Router
Supports GitHub authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
import httpx
import secrets
from datetime import datetime, timedelta

from database import get_db
from models import User
from schemas import Token
from config import config
from routers.auth import create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    prefix="/oauth",
    tags=["OAuth Social Login"]
)

# OAuth state storage (use Redis in production)
oauth_states = {}


# ============ GITHUB OAUTH ============

@router.get("/github/login")
async def github_login():
    """Initiate GitHub OAuth flow"""
    
    if not config.GITHUB_CLIENT_ID or not config.GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth not configured"
        )
    
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {"provider": "github", "timestamp": datetime.utcnow()}
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={config.GITHUB_CLIENT_ID}&"
        f"redirect_uri={config.GITHUB_REDIRECT_URI}&"
        f"scope=user:email&"
        f"state={state}"
    )
    
    return RedirectResponse(url=github_auth_url)


@router.get("/github/callback")
async def github_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback"""
    
    # Verify state
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    del oauth_states[state]
    
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": config.GITHUB_CLIENT_ID,
                "client_secret": config.GITHUB_CLIENT_SECRET,
                "redirect_uri": config.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        
        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user information"
            )
        
        user_data = user_response.json()
        
        # Get primary email
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        
        emails = email_response.json()
        primary_email = next((e["email"] for e in emails if e["primary"]), None)
        
        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No primary email found"
            )
    
    # Find or create user
    oauth_id = str(user_data.get("id"))
    
    statement = select(User).where(User.email == primary_email)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        # Create new user
        username = user_data.get("login", primary_email.split("@")[0])
        
        # Ensure username is unique
        statement = select(User).where(User.username == username)
        if db.execute(statement).scalar_one_or_none():
            username = username + "_" + secrets.token_hex(4)
        
        user = User(
            username=username,
            email=primary_email,
            first_name=user_data.get("name", "").split()[0] if user_data.get("name") else None,
            last_name=" ".join(user_data.get("name", "").split()[1:]) if user_data.get("name") and len(user_data.get("name", "").split()) > 1 else None,
            is_verified=True,  # Email verified by GitHub
            hashed_password=None  # No password for OAuth users
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_access_token = create_access_token(
        data={"sub": str(user.uid)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(user.uid, db, "OAuth GitHub")
    
    # Redirect to frontend with tokens
    redirect_url = f"{config.FRONTEND_URL}/auth/callback?access_token={jwt_access_token}&refresh_token={refresh_token}"
    return RedirectResponse(url=redirect_url)
