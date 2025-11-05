"""
GraphQL API Endpoints for NovaStack

This module provides GraphQL endpoints that work alongside our REST API generation system.
It creates GraphQL schemas dynamically from database projects and serves them via FastAPI.
"""

from fastapi import APIRouter, HTTPException, Depends
from strawberry.fastapi import GraphQLRouter
import strawberry
from typing import Dict, Optional
import logging

from app.core.security import get_current_user_id
from app.models.user import User
from app.models.project import Project
from app.services.project import ProjectService
from app.services.schema_introspector import SchemaIntrospector
from app.services.graphql_generator import create_graphql_schema_for_project

logger = logging.getLogger(__name__)

# Store for generated GraphQL schemas (in production, use Redis/Database)
_graphql_schemas: Dict[str, strawberry.Schema] = {}
_graphql_routers: Dict[str, GraphQLRouter] = {}

router = APIRouter()


@router.post("/generate-graphql/{project_id}")
async def generate_graphql_schema(
    project_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Generate GraphQL schema for a project's database
    
    This endpoint:
    1. Gets the project's database configuration
    2. Introspects the database schema  
    3. Generates GraphQL types, queries, and mutations
    4. Returns the schema information
    """
    try:
        logger.info(f"🚀 Generating GraphQL schema for project {project_id}")
        
        # Get project information
        project_service = ProjectService()
        project = await project_service.get_project(project_id, current_user_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get database configuration
        db_config = {
            "host": project.database_host,
            "port": project.database_port,
            "database": project.database_name,
            "username": project.database_user,
            "password": project.database_password,
            "database_type": project.database_type
        }
        
        # Introspect database schema
        introspector = SchemaIntrospector()
        database_schema = await introspector.introspect_database(db_config)
        
        if not database_schema or not database_schema.tables:
            raise HTTPException(
                status_code=400, 
                detail="No tables found in database or database connection failed"
            )
        
        # Generate GraphQL schema
        graphql_schema = create_graphql_schema_for_project(database_schema, project_id)
        
        # Store the schema for serving
        _graphql_schemas[project_id] = graphql_schema
        
        # Create GraphQL router for this project
        graphql_router = GraphQLRouter(graphql_schema, path=f"/graphql/{project_id}")
        _graphql_routers[project_id] = graphql_router
        
        # Build response with schema information
        types_info = []
        for table in database_schema.tables:
            table_name = table.table_name.title()
            types_info.append({
                "name": table_name,
                "table": table.table_name,
                "fields": [
                    {
                        "name": col.column_name,
                        "type": col.data_type,
                        "nullable": col.is_nullable,
                        "primary_key": col.is_primary_key
                    }
                    for col in table.columns
                ],
                "queries": [
                    f"{table.table_name.lower()}s",  # List query
                    f"{table.table_name.lower()}"    # Single query
                ],
                "mutations": [
                    f"create{table_name}",
                    f"update{table_name}", 
                    f"delete{table_name}"
                ]
            })
        
        logger.info(f"✅ Generated GraphQL schema with {len(types_info)} types")
        
        return {
            "message": "GraphQL schema generated successfully",
            "project_id": project_id,
            "database_type": database_schema.database_type,
            "database_version": database_schema.version,
            "schema_info": {
                "types_count": len(types_info),
                "types": types_info
            },
            "endpoints": {
                "graphql": f"/api/v1/graphql/{project_id}",
                "graphql_playground": f"/api/v1/graphql/{project_id}",
                "schema_sdl": f"/api/v1/graphql/{project_id}/sdl"
            },
            "status": "ready"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to generate GraphQL schema for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate GraphQL schema: {str(e)}")


@router.get("/graphql-schemas")
async def list_graphql_schemas(current_user_id: str = Depends(get_current_user_id)):
    """List all generated GraphQL schemas for the current user"""
    
    # In a real implementation, we'd query the database for user's projects
    user_schemas = []
    
    for project_id, schema in _graphql_schemas.items():
        # Here we'd verify the user owns this project
        user_schemas.append({
            "project_id": project_id,
            "graphql_endpoint": f"/api/v1/graphql/{project_id}",
            "status": "active"
        })
    
    return {
        "schemas": user_schemas,
        "total_count": len(user_schemas)
    }


@router.get("/graphql/{project_id}/sdl")
async def get_graphql_schema_sdl(
    project_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get the Schema Definition Language (SDL) for a project's GraphQL schema"""
    
    if project_id not in _graphql_schemas:
        raise HTTPException(status_code=404, detail="GraphQL schema not found")
    
    schema = _graphql_schemas[project_id]
    
    # Get SDL representation
    try:
        sdl = str(schema)
        return {
            "project_id": project_id,
            "schema_sdl": sdl,
            "content_type": "application/graphql"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SDL: {str(e)}")


@router.delete("/graphql/{project_id}")
async def remove_graphql_schema(
    project_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Remove a project's GraphQL schema"""
    
    if project_id not in _graphql_schemas:
        raise HTTPException(status_code=404, detail="GraphQL schema not found")
    
    # Remove from memory
    del _graphql_schemas[project_id]
    if project_id in _graphql_routers:
        del _graphql_routers[project_id]
    
    logger.info(f"🗑️ Removed GraphQL schema for project {project_id}")
    
    return {
        "message": "GraphQL schema removed successfully",
        "project_id": project_id
    }


def get_graphql_router_for_project(project_id: str) -> Optional[GraphQLRouter]:
    """Get the GraphQL router for a specific project"""
    return _graphql_routers.get(project_id)


def get_all_graphql_routers() -> Dict[str, GraphQLRouter]:
    """Get all GraphQL routers (for mounting in main app)"""
    return _graphql_routers.copy()


# Health check for GraphQL system
@router.get("/graphql-status")
async def graphql_system_status():
    """Get the status of the GraphQL generation system"""
    return {
        "status": "active",
        "message": "GraphQL schema generation system is running",
        "active_schemas": len(_graphql_schemas),
        "features": [
            "Dynamic GraphQL schema generation",
            "Auto-generated queries and mutations", 
            "Type-safe GraphQL types from database schemas",
            "GraphQL Playground integration",
            "Schema Definition Language (SDL) export"
        ],
        "endpoints": {
            "generate": "/api/v1/graphql/generate-graphql/{project_id}",
            "list": "/api/v1/graphql/graphql-schemas",
            "schema_sdl": "/api/v1/graphql/{project_id}/sdl",
            "remove": "/api/v1/graphql/{project_id}",
            "status": "/api/v1/graphql/graphql-status"
        }
    }