"""
API Generation Management Endpoints

These endpoints allow users to generate, manage, and configure
auto-generated REST APIs for their database projects.

Key features:
- Generate API for any project
- Configure API settings
- View API documentation
- Manage API keys and access control
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.project_service import ProjectService
from app.services.api_generator import api_generator, APIConfig
from app.services.schema_introspector import DatabaseType
from app.models.project_models import MessageResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["api-generation"])


class APIGenerationRequest(BaseModel):
    """Request model for API generation"""
    project_id: str
    config: Optional[Dict[str, Any]] = None


class APIConfigModel(BaseModel):
    """Model for API configuration"""
    max_page_size: int = 1000
    default_page_size: int = 20
    enable_bulk_operations: bool = True
    enable_file_uploads: bool = True
    rate_limit_per_minute: int = 1000


class APIStatusResponse(BaseModel):
    """Response model for API status"""
    project_id: str
    api_generated: bool
    generated_at: Optional[datetime] = None
    endpoint_count: int = 0
    base_url: Optional[str] = None


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    """Get ProjectService instance"""
    return ProjectService(db)


@router.post("/generate", response_model=APIStatusResponse)
async def generate_api(
    request: APIGenerationRequest,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Generate REST API for a database project
    
    This endpoint analyzes the project's database schema and creates
    full CRUD endpoints for all tables. The generated API will be
    available at /api/data/{project_id}/
    """
    try:
        logger.info(f"Generating API for project {request.project_id}")
        
        # Verify project ownership
        project = await project_service.get_project(
            db=project_service.db,
            project_id=request.project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        if not project.is_ready:
            raise HTTPException(
                status_code=400,
                detail="Project database is not ready. Please wait for provisioning to complete."
            )
        
        # Get connection information
        connection_info = await project_service.get_connection_info(
            db=project_service.db,
            project_id=request.project_id,
            user_id=user_id
        )
        
        if not connection_info:
            raise HTTPException(
                status_code=400,
                detail="Unable to get database connection information"
            )
        
        # Determine database type
        db_type = DatabaseType(project.database_type)
        
        # Create API config
        config = APIConfig()
        if request.config:
            config = APIConfig(**request.config)
        
        # Generate the API
        try:
            router_instance = await api_generator.generate_api_for_project(
                project_id=request.project_id,
                connection_string=connection_info.connection_string,
                database_type=db_type
            )
            
            # Get API info from cache
            api_info = api_generator.generated_apis.get(request.project_id)
            
            endpoint_count = len(api_info['schema'].tables) * 5  # 5 endpoints per table
            
            logger.info(f"API generated successfully for project {request.project_id}")
            
            return APIStatusResponse(
                project_id=request.project_id,
                api_generated=True,
                generated_at=api_info['generated_at'],
                endpoint_count=endpoint_count,
                base_url=f"/api/data/{request.project_id}"
            )
            
        except Exception as e:
            logger.error(f"API generation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate API: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in API generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate API")


@router.get("/{project_id}/status", response_model=APIStatusResponse)
async def get_api_status(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Get the status of a project's generated API
    
    Returns information about whether the API has been generated,
    when it was created, and how many endpoints are available.
    """
    try:
        # Verify project ownership
        project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if API is generated
        api_info = api_generator.generated_apis.get(project_id)
        
        if api_info:
            endpoint_count = len(api_info['schema'].tables) * 5
            return APIStatusResponse(
                project_id=project_id,
                api_generated=True,
                generated_at=api_info['generated_at'],
                endpoint_count=endpoint_count,
                base_url=f"/api/data/{project_id}"
            )
        else:
            return APIStatusResponse(
                project_id=project_id,
                api_generated=False,
                generated_at=None,
                endpoint_count=0,
                base_url=None
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get API status")


@router.delete("/{project_id}", response_model=MessageResponse)
async def remove_api(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Remove generated API for a project
    
    This will stop serving the auto-generated endpoints for this project.
    The database and project itself remain unchanged.
    """
    try:
        # Verify project ownership
        project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Remove from cache
        if project_id in api_generator.generated_apis:
            del api_generator.generated_apis[project_id]
            logger.info(f"Removed API for project {project_id}")
            
            return MessageResponse(
                message=f"API for project '{project.name}' has been removed",
                success=True
            )
        else:
            return MessageResponse(
                message="No API was generated for this project",
                success=True
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing API: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove API")


@router.get("/{project_id}/schema")
async def get_api_schema(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Get the database schema for a project's API
    
    Returns detailed information about all tables, columns, and
    relationships in the database.
    """
    try:
        # Verify project ownership
        project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if API is generated
        api_info = api_generator.generated_apis.get(project_id)
        
        if not api_info:
            raise HTTPException(
                status_code=404,
                detail="API not generated for this project. Generate it first."
            )
        
        schema = api_info['schema']
        
        return {
            "database_name": schema.database_name,
            "database_type": schema.database_type.value,
            "version": schema.version,
            "table_count": len(schema.tables),
            "tables": [
                {
                    "name": table.name,
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.type,
                            "nullable": col.nullable,
                            "primary_key": col.primary_key,
                            "auto_increment": col.auto_increment,
                            "max_length": col.max_length
                        }
                        for col in table.columns
                    ],
                    "primary_key": table.primary_key,
                    "foreign_keys": [
                        {
                            "table": fk.table,
                            "column": fk.column,
                            "on_delete": fk.on_delete,
                            "on_update": fk.on_update
                        }
                        for fk in table.foreign_keys
                    ],
                    "comment": table.comment
                }
                for table in schema.tables
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API schema: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get API schema")


@router.get("/{project_id}/endpoints")
async def get_api_endpoints(
    project_id: str,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Get list of all generated API endpoints for a project
    
    Returns a comprehensive list of all available REST endpoints
    with their HTTP methods and descriptions.
    """
    try:
        # Verify project ownership
        project = await project_service.get_project(
            db=project_service.db,
            project_id=project_id,
            user_id=user_id
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if API is generated
        api_info = api_generator.generated_apis.get(project_id)
        
        if not api_info:
            raise HTTPException(
                status_code=404,
                detail="API not generated for this project. Generate it first."
            )
        
        schema = api_info['schema']
        base_url = f"/api/data/{project_id}"
        
        endpoints = []
        
        # Add metadata endpoints
        endpoints.extend([
            {
                "method": "GET",
                "path": f"{base_url}/meta/schema",
                "description": "Get complete database schema",
                "category": "metadata"
            },
            {
                "method": "GET", 
                "path": f"{base_url}/meta/tables",
                "description": "Get list of all tables",
                "category": "metadata"
            }
        ])
        
        # Add table endpoints
        for table in schema.tables:
            table_name = table.name
            
            endpoints.extend([
                {
                    "method": "GET",
                    "path": f"{base_url}/{table_name}",
                    "description": f"List all {table_name} records",
                    "category": "data",
                    "table": table_name
                },
                {
                    "method": "GET",
                    "path": f"{base_url}/{table_name}/{{id}}",
                    "description": f"Get single {table_name} record",
                    "category": "data",
                    "table": table_name
                },
                {
                    "method": "POST",
                    "path": f"{base_url}/{table_name}",
                    "description": f"Create new {table_name} record",
                    "category": "data",
                    "table": table_name
                },
                {
                    "method": "PUT",
                    "path": f"{base_url}/{table_name}/{{id}}",
                    "description": f"Update {table_name} record",
                    "category": "data",
                    "table": table_name
                },
                {
                    "method": "DELETE",
                    "path": f"{base_url}/{table_name}/{{id}}",
                    "description": f"Delete {table_name} record",
                    "category": "data",
                    "table": table_name
                }
            ])
        
        return {
            "project_id": project_id,
            "base_url": base_url,
            "endpoint_count": len(endpoints),
            "endpoints": endpoints
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API endpoints: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get API endpoints")


@router.post("/{project_id}/regenerate", response_model=APIStatusResponse)
async def regenerate_api(
    project_id: str,
    config: Optional[APIConfigModel] = None,
    user_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Regenerate API for a project
    
    This will re-analyze the database schema and recreate all endpoints.
    Useful when the database structure has changed.
    """
    try:
        # Remove existing API
        if project_id in api_generator.generated_apis:
            del api_generator.generated_apis[project_id]
        
        # Generate new API
        request = APIGenerationRequest(
            project_id=project_id,
            config=config.dict() if config else None
        )
        
        return await generate_api(request, user_id, project_service)
    
    except Exception as e:
        logger.error(f"Error regenerating API: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to regenerate API")