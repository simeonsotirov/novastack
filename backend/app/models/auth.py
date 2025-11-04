"""
Authentication data models for NovaStack

These Pydantic models define the structure of data for authentication:
- What users send when registering/logging in
- What we send back in responses
- Input validation and serialization

Think of these as "forms" that define exactly what data is required
and how it should be formatted.
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """
    Data model for user registration
    
    This defines what data users must provide when creating an account.
    """
    email: EmailStr  # EmailStr automatically validates email format
    password: str
    full_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        """
        Password validation rules
        
        Ensure passwords meet security requirements:
        - At least 8 characters long
        - Contains letters and numbers (you can add more rules later)
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not (has_letter and has_number):
            raise ValueError('Password must contain at least one letter and one number')
        
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name if provided"""
        if v and len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        return v.strip() if v else None


class UserLogin(BaseModel):
    """
    Data model for user login
    
    Simple model - just email and password required for login.
    """
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Data model for user information in responses
    
    This is what we send back when users ask for their profile info.
    Note: We NEVER include passwords in responses!
    """
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        # This allows Pydantic to work with SQLAlchemy models
        from_attributes = True


class TokenResponse(BaseModel):
    """
    Data model for authentication token response
    
    This is what we send back after successful login.
    """
    access_token: str
    token_type: str = "bearer"  # Standard OAuth2 token type
    expires_in: int  # Token expiration time in seconds
    user: UserResponse  # Include user info with token


class PasswordChange(BaseModel):
    """
    Data model for password change requests
    
    Users need to provide their current password and new password.
    """
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Apply same password validation as registration"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not (has_letter and has_number):
            raise ValueError('Password must contain at least one letter and one number')
        
        return v


class PasswordReset(BaseModel):
    """
    Data model for password reset requests
    
    For now, just email - in production you'd add token verification.
    """
    email: EmailStr


class MessageResponse(BaseModel):
    """
    Generic message response model
    
    For simple success/error messages.
    """
    message: str
    success: bool = True