"""
Security utilities for NovaStack

This module handles:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- Security dependencies for protected routes

Think of this as the "security guard" of our application - it keeps passwords safe
and ensures only authenticated users can access protected features.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# Password hashing context using bcrypt
# bcrypt is industry-standard for password hashing - it's slow on purpose to prevent brute force attacks
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme for FastAPI
# This tells FastAPI to look for "Authorization: Bearer <token>" headers
security = HTTPBearer()


class PasswordManager:
    """
    Password management utilities
    
    This class handles all password-related operations:
    - Hashing passwords before storing in database (never store plain text!)
    - Verifying passwords during login
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password using bcrypt
        
        Args:
            password: Plain text password from user
            
        Returns:
            Hashed password safe to store in database
        """
        # Truncate password to 72 bytes max (bcrypt limitation)
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against its hash
        
        Args:
            plain_password: Password user entered
            hashed_password: Hash stored in database
            
        Returns:
            True if password is correct, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)


class JWTManager:
    """
    JWT token management utilities
    
    JWT (JSON Web Token) is like a secure "ID card" for users.
    Once they log in, they get a token that proves who they are
    without needing to send username/password with every request.
    """
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Data to encode in token (usually user ID)
            expires_delta: How long token should be valid
            
        Returns:
            JWT token string
        """
        # Copy data to avoid modifying original
        to_encode = data.copy()
        
        # Set expiration time
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
        
        # Add expiration to token data
        to_encode.update({"exp": expire})
        
        # Create and return JWT token
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token data
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode and verify token
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to get current authenticated user ID
    
    This function can be used as a dependency in any route that needs authentication.
    It automatically extracts the JWT token from the Authorization header,
    verifies it, and returns the user ID.
    
    Usage in routes:
        @app.get("/protected-route")
        async def protected_route(user_id: str = Depends(get_current_user_id)):
            # This route requires authentication
            return {"message": f"Hello user {user_id}!"}
    
    Args:
        credentials: Automatically extracted from Authorization header
        
    Returns:
        User ID from token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    token = credentials.credentials
    payload = JWTManager.verify_token(token)
    
    # Extract user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token - no user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def create_token_for_user(user_id: str) -> str:
    """
    Helper function to create a token for a user
    
    Args:
        user_id: User's unique identifier
        
    Returns:
        JWT access token
    """
    return JWTManager.create_access_token(data={"sub": user_id})