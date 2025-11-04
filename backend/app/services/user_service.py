"""
User service for NovaStack

This service handles all user-related business logic:
- User registration and validation
- User authentication and login
- User profile management
- Password changes

Think of this as the "business logic brain" - it knows the rules
about how users should be created, authenticated, etc.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import datetime, timezone

from app.models.user import User
from app.models.auth import UserRegister, UserLogin, PasswordChange
from app.core.security import PasswordManager, create_token_for_user
from app.core.config import settings


class UserService:
    """Service class for user operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize user service with database session
        
        Args:
            db: Database session for this service instance
        """
        self.db = db
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Find a user by their ID
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_user(self, user_data: UserRegister) -> User:
        """
        Create a new user account
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        hashed_password = PasswordManager.hash_password(user_data.password)
        
        # Create new user
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_superuser=False
        )
        
        # Add to database
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Find user by email
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        # Verify password
        if not PasswordManager.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def login_user(self, login_data: UserLogin) -> dict:
        """
        Log in a user and return access token
        
        Args:
            login_data: Login credentials
            
        Returns:
            Dictionary with token and user info
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Authenticate user
        user = await self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = create_token_for_user(str(user.id))
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_expire_minutes * 60,  # Convert to seconds
            "user": user
        }
    
    async def change_password(self, user_id: str, password_data: PasswordChange) -> bool:
        """
        Change a user's password
        
        Args:
            user_id: User's ID
            password_data: Current and new password
            
        Returns:
            True if password changed successfully
            
        Raises:
            HTTPException: If current password is wrong or user not found
        """
        # Get user
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not PasswordManager.verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = PasswordManager.hash_password(password_data.new_password)
        
        # Update password
        user.hashed_password = new_hashed_password
        user.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        return True
    
    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account (soft delete)
        
        Args:
            user_id: User's ID
            
        Returns:
            True if deactivated successfully
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        return True
    
    async def update_user_profile(self, user_id: str, full_name: Optional[str] = None) -> User:
        """
        Update user profile information
        
        Args:
            user_id: User's ID
            full_name: New full name (optional)
            
        Returns:
            Updated user object
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if full_name is not None:
            user.full_name = full_name
        
        user.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user


# Dependency to get user service
async def get_user_service(db: AsyncSession) -> UserService:
    """
    Dependency to get user service instance
    
    This can be used in FastAPI routes like:
    
    @app.post("/register")
    async def register(user_service: UserService = Depends(get_user_service)):
        # Use user_service here
    """
    return UserService(db)