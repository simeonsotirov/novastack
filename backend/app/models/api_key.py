"""
API Key model for NovaStack

This model represents API keys that provide access to project databases.
Each project can have multiple API keys with different permissions.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class ApiKey(Base):
    """
    API Key model - provides secure access to project databases
    
    API keys allow external applications to access project data through
    REST and GraphQL endpoints. Keys can have limited permissions and
    expiration dates for security.
    """
    __tablename__ = "api_keys"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # API key details
    key_name = Column(String(255), nullable=False)  # Human-readable name
    key_hash = Column(String(255), nullable=False, index=True)  # Hashed API key
    
    # Permissions and configuration
    permissions = Column(JSON, default={})  # JSON object with permissions
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Project association
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="api_keys")
    
    def __repr__(self):
        return f"<ApiKey {self.key_name} for {self.project.name}>"
    
    @property
    def is_expired(self):
        """Check if API key has expired"""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_active(self):
        """Check if API key is active and usable"""
        return not self.is_expired