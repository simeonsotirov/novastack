"""
Project data models for NovaStack

These Pydantic models define the structure of data for project operations:
- What users send when creating/updating projects
- What we send back in responses
- Input validation and serialization
"""

from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class ProjectCreate(BaseModel):
    """
    Data model for project creation requests
    
    This defines what data users must provide when creating a new project.
    """
    name: str
    database_type: DatabaseType
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        """
        Validate project name
        
        Project names should be:
        - Between 3 and 50 characters
        - Contain only letters, numbers, spaces, hyphens, underscores
        - Not be empty or just whitespace
        """
        if not v or not v.strip():
            raise ValueError('Project name cannot be empty')
        
        v = v.strip()
        
        if len(v) < 3:
            raise ValueError('Project name must be at least 3 characters long')
        
        if len(v) > 50:
            raise ValueError('Project name cannot be longer than 50 characters')
        
        # Check for valid characters
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Project name can only contain letters, numbers, spaces, hyphens, and underscores')
        
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate project description if provided"""
        if v and len(v) > 500:
            raise ValueError('Project description cannot be longer than 500 characters')
        return v.strip() if v else None


class ProjectUpdate(BaseModel):
    """
    Data model for project update requests
    
    Users can update project name and description.
    Database type cannot be changed after creation.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        """Apply same validation as ProjectCreate"""
        if v is None:
            return v
        
        if not v.strip():
            raise ValueError('Project name cannot be empty')
        
        v = v.strip()
        
        if len(v) < 3:
            raise ValueError('Project name must be at least 3 characters long')
        
        if len(v) > 50:
            raise ValueError('Project name cannot be longer than 50 characters')
        
        import re
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Project name can only contain letters, numbers, spaces, hyphens, and underscores')
        
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate description if provided"""
        if v is not None and len(v) > 500:
            raise ValueError('Project description cannot be longer than 500 characters')
        return v.strip() if v else None


class ProjectResponse(BaseModel):
    """
    Data model for project information in responses
    
    This is what we send back when users request project information.
    """
    id: str
    name: str
    description: Optional[str] = None
    database_type: str
    database_name: str
    created_at: datetime
    updated_at: datetime
    is_ready: bool
    
    # Connection info (only for project owner)
    connection_string: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProjectStatus(BaseModel):
    """
    Data model for detailed project status information
    
    Includes both project info and container status.
    """
    project: ProjectResponse
    container_status: Optional[str] = None  # running, stopped, etc.
    container_created: Optional[datetime] = None
    connection_available: bool = False
    database_size: Optional[str] = None  # For future implementation


class ProjectList(BaseModel):
    """
    Data model for listing multiple projects
    
    Used for paginated project listings.
    """
    projects: list[ProjectResponse]
    total: int
    page: int = 1
    per_page: int = 10


class DatabaseConnection(BaseModel):
    """
    Data model for database connection information
    
    Provides all the details needed to connect to a project's database.
    """
    host: str = "localhost"
    port: int
    database: str
    username: str
    password: str
    connection_string: str
    database_type: DatabaseType
    
    # Additional connection parameters
    ssl_mode: str = "prefer"  # For PostgreSQL
    charset: str = "utf8mb4"  # For MySQL


class ProjectStats(BaseModel):
    """
    Data model for project statistics
    
    For dashboard and monitoring purposes.
    """
    total_projects: int
    postgresql_projects: int
    mysql_projects: int
    active_containers: int
    total_storage_mb: float
    created_today: int
    
    
class ContainerStatus(BaseModel):
    """
    Data model for container status information
    """
    container_id: str
    name: str
    status: str  # running, stopped, created, etc.
    created: datetime
    image: str
    ports: Dict[str, Any] = {}
    resource_usage: Optional[Dict[str, Any]] = None


class ProjectAction(BaseModel):
    """
    Data model for project actions (restart, stop, etc.)
    """
    action: str
    
    @validator('action')
    def validate_action(cls, v):
        """Validate action type"""
        allowed_actions = ['restart', 'stop', 'start', 'backup']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class MessageResponse(BaseModel):
    """
    Generic success/error message response
    """
    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None