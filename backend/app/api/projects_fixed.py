"""
Project Management API Routes (Fixed Version)

Clean implementation of project endpoints with proper dependency injection.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.project_models import (
    ProjectCreate, 
    ProjectUpdate, 
    ProjectResponse, 
    ProjectList, 
    ProjectStatus,
    DatabaseConnection,
    ProjectStats,
    ContainerStatus,
    ProjectAction,
    MessageResponse
)
from app.services.project_service import ProjectService
from app.services.docker_service import DockerManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Initialize Docker manager
docker_manager = DockerManager()

# Dependency to get project service
def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    """Get ProjectService instance"""
    return ProjectService(db)


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """Create a new database project"""
    try:
        logger.info(f"Creating project '{project_data.name}' for user {user_id}")
        
        project = await project_service.create_project(
            user_id=user_id,
            name=project_data.name,
            database_type=project_data.database_type.value,
            description=project_data.description
        )
        
        logger.info(f"Successfully created project {project.id}")
        return project
        
    except ValueError as e:
        logger.warning(f"Project creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create project")


@router.get("/", response_model=ProjectList)
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """List all projects for the current user"""
    try:
        projects = await project_service.get_user_projects(
            db=project_service.db,
            user_id=user_id,
            skip=(page - 1) * per_page,
            limit=per_page
        )
        
        total = await project_service.count_user_projects(
            db=project_service.db,
            user_id=user_id
        )
        
        return ProjectList(
            projects=projects,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing projects for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list projects")


@router.get("/{project_id}", response_model=ProjectStatus)
async def get_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """Get detailed information about a specific project"""
    try:
        project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get container status if project is ready
        container_status = None
        connection_available = False
        
        if project.is_ready:
            try:
                container_name = f"novastack-{project.database_type}-{project.id[:8]}"
                container_info = docker_manager.get_container_status(container_name)
                
                if container_info:
                    container_status = container_info.get('status')
                    connection_available = container_status == 'running'
                    
            except Exception as e:
                logger.warning(f"Could not get container status for project {project_id}: {str(e)}")
        
        return ProjectStatus(
            project=project,
            container_status=container_status,
            connection_available=connection_available
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get project")


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """Update project information"""
    try:
        # Check if project exists and belongs to user
        existing_project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update the project
        updated_project = await project_service.update_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id,
            updates=project_data.dict(exclude_unset=True)
        )
        
        logger.info(f"Updated project {project_id}")
        return updated_project
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Project update failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update project")


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """Delete a project and its associated database container"""
    try:
        # Check if project exists and belongs to user
        project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete the project
        await project_service.delete_project(
            project_id=project_id,
            user_id=user_id
        )
        
        logger.info(f"Deleted project {project_id}")
        return MessageResponse(
            message=f"Project '{project.name}' has been deleted successfully",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete project")


@router.get("/{project_id}/connection", response_model=DatabaseConnection)
async def get_connection_info(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """Get database connection information for a project"""
    try:
        project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.is_ready:
            raise HTTPException(
                status_code=400, 
                detail="Project is not ready yet. Please wait for the database to be provisioned."
            )
        
        # Get connection details
        connection_info = await project_service.get_connection_info(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        return connection_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection info for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get connection information")


@router.post("/{project_id}/action", response_model=MessageResponse)
async def project_action(
    project_id: str,
    action: ProjectAction,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """Perform actions on a project's database container"""
    try:
        project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.is_ready:
            raise HTTPException(
                status_code=400,
                detail="Cannot perform actions on a project that is not ready"
            )
        
        # Perform the action
        container_name = f"novastack-{project.database_type}-{project.id[:8]}"
        
        if action.action == "restart":
            result = docker_manager.restart_container(container_name)
            message = f"Project '{project.name}' database has been restarted"
            
        elif action.action == "stop":
            result = docker_manager.stop_container(container_name)
            message = f"Project '{project.name}' database has been stopped"
            
        elif action.action == "start":
            result = docker_manager.start_container(container_name)
            message = f"Project '{project.name}' database has been started"
            
        elif action.action == "backup":
            raise HTTPException(status_code=501, detail="Backup feature not yet implemented")
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")
        
        if not result:
            raise HTTPException(status_code=500, detail=f"Failed to {action.action} project database")
        
        logger.info(f"Performed action '{action.action}' on project {project_id}")
        return MessageResponse(message=message, success=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing action on project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to {action.action} project")


@router.get("/stats/overview", response_model=ProjectStats)
async def get_project_stats(
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """Get overview statistics for user's projects"""
    try:
        stats = await project_service.get_user_project_stats(
            db=project_service.db,
            user_id=user_id
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting project stats for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get project statistics")