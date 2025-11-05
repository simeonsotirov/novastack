"""
Mock Authentication API routes for NovaStack (Development Mode)

This module provides authentication endpoints that work without a database connection.
This is useful for frontend development when you don't have a database set up yet.

Note: This is for development only - never use this in production!
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

from app.core.security import JWTManager, PasswordManager

# Simple Pydantic models for mock auth
class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    confirm_password: str
    full_name: Optional[str] = None

class UserInfo(BaseModel):
    id: str
    email: str  
    full_name: str
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo

class MessageResponse(BaseModel):
    message: str
    success: bool

# Create router for authentication endpoints
router = APIRouter()

# Mock user storage (in-memory, resets when server restarts)
mock_users: Dict[str, Dict[str, Any]] = {
    "admin@novastack.dev": {
        "id": "user_admin",
        "email": "admin@novastack.dev",
        "full_name": "NovaStack Admin",
        "hashed_password": PasswordManager.hash_password("admin123"),
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
}


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    """
    Register a new user account (Mock Implementation)
    
    Creates a mock user account and returns an access token.
    """
    # Check if user already exists
    if user_data.email in mock_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password confirmation
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Create mock user
    user_id = f"user_{len(mock_users) + 1}"
    mock_users[user_data.email] = {
        "id": user_id,
        "email": user_data.email,
        "full_name": getattr(user_data, 'full_name', user_data.email.split('@')[0]),
        "hashed_password": PasswordManager.hash_password(user_data.password),
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    
    # Create access token
    access_token = JWTManager.create_access_token(data={"sub": user_id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 24 * 60,  # 30 days in minutes
        user={
            "id": user_id,
            "email": user_data.email,
            "full_name": mock_users[user_data.email]["full_name"],
            "is_active": True
        }
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """
    Authenticate user and return access token (Mock Implementation)
    """
    # Check if user exists
    if login_data.email not in mock_users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = mock_users[login_data.email]
    
    # Verify password
    if not PasswordManager.verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create access token
    access_token = JWTManager.create_access_token(data={"sub": user["id"]})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 24 * 60,  # 30 days in minutes
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "is_active": user["is_active"]
        }
    )


@router.get("/me")
async def get_current_user():
    """
    Get current user info (Mock Implementation)
    
    Note: This doesn't validate the token for simplicity in mock mode
    """
    return {
        "message": "Mock authentication active - database connection required for full auth",
        "available_endpoints": [
            "POST /api/v1/auth/register",
            "POST /api/v1/auth/login",
            "GET /api/v1/auth/me"
        ],
        "mock_users": [
            {
                "email": email,
                "id": user["id"],
                "full_name": user["full_name"],
                "created_at": user["created_at"]
            }
            for email, user in mock_users.items()
        ]
    }


@router.post("/logout", response_model=MessageResponse)
async def logout_user():
    """
    Logout user (Mock Implementation)
    """
    return MessageResponse(
        message="Logged out successfully (mock mode)",
        success=True
    )


@router.get("/status")
async def auth_status():
    """
    Get authentication system status
    """
    return {
        "status": "mock_mode",
        "message": "Running in mock authentication mode (no database required)",
        "total_mock_users": len(mock_users),
        "database_required": False,
        "production_ready": False,
        "default_admin": {
            "email": "admin@novastack.dev",
            "password": "admin123"
        }
    }