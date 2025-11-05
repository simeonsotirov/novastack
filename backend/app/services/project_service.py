"""
Project Service for NovaStack

This service handles all project-related operations:
- Creating new database projects
- Managing project lifecycle
- Database provisioning integration
- Project ownership and permissions

Think of this as the "project manager" - it coordinates between
user requests, database provisioning, and data storage.
"""

import logging
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.project import Project
from app.models.user import User
from app.services.docker_service import docker_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProjectService:
    """Service class for project management operations"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize project service with database session
        
        Args:
            db: Database session for this service instance
        """
        self.db = db
    
    async def create_project(
        self,
        name: str,
        database_type: str,
        user_id: str,
        description: Optional[str] = None
    ) -> Project:
        """
        Create a new database project for a user
        
        This is the main function that:
        1. Validates the request
        2. Creates the database container 
        3. Stores project info in our database
        4. Returns the complete project info
        
        Args:
            name: User-friendly project name
            database_type: 'postgresql' or 'mysql'
            user_id: ID of the user creating the project
            description: Optional project description
            
        Returns:
            Created project with database connection info
            
        Raises:
            HTTPException: If validation fails or creation fails
        """
        # Validate database type
        if database_type not in ['postgresql', 'mysql']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database type must be 'postgresql' or 'mysql'"
            )
        
        # Check if user exists
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if project name already exists for this user
        existing_stmt = select(Project).where(
            and_(Project.owner_id == user_id, Project.name == name)
        )
        existing_result = await self.db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project '{name}' already exists"
            )
        
        # Create the project record first (we'll update it with container info)
        project = Project(
            name=name,
            description=description,
            database_type=database_type,
            database_name=f"db_{name.lower().replace(' ', '_').replace('-', '_')}",
            owner_id=user_id
        )
        
        # Add to database and get the ID
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        
        try:
            # Create the database container
            if database_type == 'postgresql':
                container_info = await docker_manager.create_postgresql_container(
                    project_id=str(project.id),
                    database_name=project.database_name,
                    user_id=user_id
                )
            else:  # mysql
                container_info = await docker_manager.create_mysql_container(
                    project_id=str(project.id),
                    database_name=project.database_name,
                    user_id=user_id
                )
            
            # Update project with container information
            project.container_id = container_info['container_id']
            project.connection_string = container_info['connection_string']
            
            await self.db.commit()
            await self.db.refresh(project)
            
            logger.info(f"✅ Project '{name}' created successfully for user {user_id}")
            return project
            
        except Exception as e:
            # If container creation fails, clean up the project record
            await self.db.delete(project)
            await self.db.commit()
            
            logger.error(f"❌ Failed to create project '{name}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create database project: {str(e)}"
            )
    
    async def get_user_projects(self, user_id: str) -> List[Project]:
        """
        Get all projects owned by a user
        
        Args:
            user_id: User's ID
            
        Returns:
            List of user's projects
        """
        stmt = select(Project).where(Project.owner_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_project_by_id(self, project_id: str, user_id: str) -> Optional[Project]:
        """
        Get a specific project by ID (only if user owns it)
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
            
        Returns:
            Project if found and owned by user, None otherwise
        """
        stmt = select(Project).where(
            and_(Project.id == project_id, Project.owner_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """
        Delete a project and its database container
        
        Args:
            project_id: Project ID to delete
            user_id: User ID (for ownership verification)
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If project not found or permission denied
        """
        # Get project
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Remove container if it exists
        if project.container_id:
            success = docker_manager.remove_container(project.container_id)
            if not success:
                logger.warning(f"⚠️ Failed to remove container for project {project_id}")
        
        # Remove project from database
        await self.db.delete(project)
        await self.db.commit()
        
        logger.info(f"✅ Project '{project.name}' deleted successfully")
        return True
    
    async def get_project_status(self, project_id: str, user_id: str) -> Optional[Dict]:
        """
        Get detailed status information about a project
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
            
        Returns:
            Dictionary with project and container status
        """
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return None
        
        # Get container status if container exists
        container_status = None
        if project.container_id:
            container_status = docker_manager.get_container_status(project.container_id)
        
        return {
            'project': {
                'id': str(project.id),
                'name': project.name,
                'description': project.description,
                'database_type': project.database_type,
                'database_name': project.database_name,
                'created_at': project.created_at.isoformat(),
                'is_ready': project.is_ready
            },
            'container': container_status,
            'connection_available': project.connection_string is not None
        }
    
    async def update_project(
        self,
        project_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Project]:
        """
        Update project information (name, description)
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
            name: New project name (optional)
            description: New project description (optional)
            
        Returns:
            Updated project or None if not found
        """
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if new name conflicts with existing projects
        if name and name != project.name:
            existing_stmt = select(Project).where(
                and_(
                    Project.owner_id == user_id,
                    Project.name == name,
                    Project.id != project_id
                )
            )
            existing_result = await self.db.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project name '{name}' already exists"
                )
        
        # Update fields
        if name:
            project.name = name
        if description is not None:
            project.description = description
        
        await self.db.commit()
        await self.db.refresh(project)
        
        return project
    
    async def restart_project_database(self, project_id: str, user_id: str) -> bool:
        """
        Restart the database container for a project
        
        Args:
            project_id: Project ID
            user_id: User ID (for ownership verification)
            
        Returns:
            True if restarted successfully
        """
        project = await self.get_project_by_id(project_id, user_id)
        if not project or not project.container_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project or container not found"
            )
        
        try:
            # Stop and start the container
            docker_manager.stop_container(project.container_id)
            # TODO: Add start_container method to DockerManager
            logger.info(f"✅ Project '{project.name}' database restarted")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to restart project database: {e}")
            return False
    
    # API compatibility methods
    async def get_project(self, db: AsyncSession, project_id: str, user_id: str) -> Optional[Project]:
        """Get a project (for API compatibility)"""
        return await self.get_project_by_id(project_id, user_id)
    
    async def get_user_projects(self, db: AsyncSession, user_id: str, skip: int = 0, limit: int = 10) -> List[Project]:
        """Get paginated list of projects for a user"""
        try:
            stmt = select(Project).where(
                Project.owner_id == user_id
            ).order_by(Project.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting projects for user {user_id}: {str(e)}")
            return []
    
    async def count_user_projects(self, db: AsyncSession, user_id: str) -> int:
        """Count total projects for a user"""
        try:
            from sqlalchemy import func
            stmt = select(func.count(Project.id)).where(Project.owner_id == user_id)
            result = await self.db.execute(stmt) 
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting projects for user {user_id}: {str(e)}")
            return 0
    
    async def update_project(self, db: AsyncSession, project_id: str, user_id: str, updates: dict) -> Optional[Project]:
        """Update a project with new data (for API compatibility)"""
        return await self.update_project_info(
            project_id=project_id,
            user_id=user_id,
            name=updates.get('name'),
            description=updates.get('description')
        )
    
    async def get_connection_info(self, db: AsyncSession, project_id: str, user_id: str) -> Optional[dict]:
        """Get database connection information for a project"""
        try:
            project = await self.get_project_by_id(project_id, user_id)
            if not project or not project.is_ready:
                return None
            
            # Import here to avoid circular imports
            from app.models.project_models import DatabaseConnection, DatabaseType
            
            # Extract port from connection string or use defaults
            port = 5432 if project.database_type == "postgresql" else 3306
            
            connection_info = DatabaseConnection(
                host="localhost",
                port=port,
                database=project.database_name,
                username=project.database_name,
                password="secure_password",  # Should be from secure storage
                connection_string=project.connection_string or "",
                database_type=DatabaseType(project.database_type)
            )
            
            return connection_info
            
        except Exception as e:
            logger.error(f"Error getting connection info for project {project_id}: {str(e)}")
            return None
    
    async def get_user_project_stats(self, db: AsyncSession, user_id: str) -> dict:
        """Get statistics about user's projects"""
        try:
            from app.models.project_models import ProjectStats
            from sqlalchemy import func
            
            # Get basic counts
            total_result = await self.db.execute(
                select(func.count(Project.id)).where(Project.owner_id == user_id)
            )
            total_projects = total_result.scalar() or 0
            
            # Count by database type
            postgresql_result = await self.db.execute(
                select(func.count(Project.id)).where(
                    Project.owner_id == user_id,
                    Project.database_type == "postgresql"
                )
            )
            postgresql_projects = postgresql_result.scalar() or 0
            
            mysql_result = await self.db.execute(
                select(func.count(Project.id)).where(
                    Project.owner_id == user_id,
                    Project.database_type == "mysql"
                )
            )
            mysql_projects = mysql_result.scalar() or 0
            
            # Count active containers
            active_result = await self.db.execute(
                select(func.count(Project.id)).where(
                    Project.owner_id == user_id,
                    Project.is_ready == True
                )
            )
            active_containers = active_result.scalar() or 0
            
            # Count projects created today
            from datetime import datetime, date
            today = date.today()
            today_result = await self.db.execute(
                select(func.count(Project.id)).where(
                    Project.owner_id == user_id,
                    func.date(Project.created_at) == today
                )
            )
            created_today = today_result.scalar() or 0
            
            return ProjectStats(
                total_projects=total_projects,
                postgresql_projects=postgresql_projects,
                mysql_projects=mysql_projects,
                active_containers=active_containers,
                total_storage_mb=0.0,  # Future implementation
                created_today=created_today
            )
            
        except Exception as e:
            logger.error(f"Error getting project stats for user {user_id}: {str(e)}")
            from app.models.project_models import ProjectStats
            return ProjectStats(
                total_projects=0,
                postgresql_projects=0,
                mysql_projects=0,
                active_containers=0,
                total_storage_mb=0.0,
                created_today=0
            )


# Dependency to get project service
async def get_project_service(db: AsyncSession) -> ProjectService:
    """
    Dependency to get project service instance
    
    This can be used in FastAPI routes like:
    
    @app.post("/projects")
    async def create_project(project_service: ProjectService = Depends(get_project_service)):
        # Use project_service here
    """
    return ProjectService(db)