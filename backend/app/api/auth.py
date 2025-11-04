"""
Authentication API routes for NovaStack

This module contains all the authentication endpoints:
- POST /register - Create new user account
- POST /login - Authenticate and get token
- GET /me - Get current user profile
- PUT /me - Update user profile
- POST /change-password - Change password
- POST /logout - Logout (token invalidation)

These are the endpoints that the frontend will call for user management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.auth import (
    UserRegister, 
    UserLogin, 
    UserResponse, 
    TokenResponse, 
    PasswordChange,
    MessageResponse
)
from app.services.user_service import UserService

# Create router for authentication endpoints
router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    Creates a new user account and returns an access token so they're
    automatically logged in after registration.
    
    Args:
        user_data: User registration information
        db: Database session
        
    Returns:
        Access token and user information
    """
    user_service = UserService(db)
    
    # Create the user
    new_user = await user_service.create_user(user_data)
    
    # Log them in immediately after registration
    login_data = UserLogin(email=user_data.email, password=user_data.password)
    token_data = await user_service.login_user(login_data)
    
    return TokenResponse(**token_data)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access token
    
    Args:
        login_data: Email and password
        db: Database session
        
    Returns:
        Access token and user information
    """
    user_service = UserService(db)
    token_data = await user_service.login_user(login_data)
    return TokenResponse(**token_data)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile information
    
    This endpoint requires authentication - user must provide valid JWT token.
    
    Args:
        current_user_id: Extracted from JWT token
        db: Database session
        
    Returns:
        Current user's profile information
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile information
    
    Args:
        full_name: New full name (optional)
        current_user_id: Extracted from JWT token
        db: Database session
        
    Returns:
        Updated user profile
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user_profile(current_user_id, full_name)
    return UserResponse.model_validate(updated_user)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password
    
    Args:
        password_data: Current and new password
        current_user_id: Extracted from JWT token
        db: Database session
        
    Returns:
        Success message
    """
    user_service = UserService(db)
    await user_service.change_password(current_user_id, password_data)
    
    return MessageResponse(
        message="Password changed successfully",
        success=True
    )


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Logout user (invalidate token)
    
    For JWT tokens, logout is usually handled client-side by deleting the token.
    In production, you might want to maintain a token blacklist.
    
    Args:
        current_user_id: Extracted from JWT token
        
    Returns:
        Success message
    """
    # In a production system, you might add the token to a blacklist here
    # For now, we just return a success message
    return MessageResponse(
        message="Logged out successfully",
        success=True
    )


@router.delete("/me", response_model=MessageResponse)
async def deactivate_account(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate current user's account
    
    This is a "soft delete" - the account is marked as inactive but data is preserved.
    
    Args:
        current_user_id: Extracted from JWT token
        db: Database session
        
    Returns:
        Success message
    """
    user_service = UserService(db)
    await user_service.deactivate_user(current_user_id)
    
    return MessageResponse(
        message="Account deactivated successfully",
        success=True
    )