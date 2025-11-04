"""
Project model for NovaStack

This model represents database projects created by users.
Each project contains an isolated database (PostgreSQL or MySQL).
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Project(Base):
    """
    Project model - represents a user's database project
    
    Each project gets its own isolated database container with:
    - Unique database name
    - Connection string
    - Container management
    - API endpoints
    """
    __tablename__ = "projects"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Project details
    name = Column(String(255), nullable=False)  # User-friendly project name
    description = Column(Text, nullable=True)   # Optional project description
    
    # Database configuration
    database_type = Column(String(50), nullable=False)  # 'postgresql' or 'mysql'
    database_name = Column(String(255), nullable=False)  # Actual DB name in container
    container_id = Column(String(255), nullable=True)    # Docker container ID
    connection_string = Column(Text, nullable=True)      # Full connection string
    
    # Ownership
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    api_keys = relationship("ApiKey", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project {self.name} ({self.database_type})>"
    
    @property
    def is_ready(self):
        """Check if project database is ready to use"""
        return self.container_id is not None and self.connection_string is not None
    
    @property
    def display_name(self):
        """Get display name for UI"""
        return f"{self.name} ({self.database_type.upper()})"