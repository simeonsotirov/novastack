"""
API Router package for NovaStack

This file sets up the main API router and includes all sub-routers
for different features (auth, projects, etc.)
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Import sub-routers
from app.api.projects import router as projects_router
from app.api.api_generation import router as api_generation_router
from app.api.graphql import router as graphql_router
# from app.api.storage import router as storage_router

# Use mock authentication for development (no database required)
from app.api.auth_mock import router as auth_router

# Include sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(api_generation_router, prefix="/generate", tags=["api-generation"])
api_router.include_router(graphql_router, prefix="/graphql", tags=["graphql"])
# api_router.include_router(storage_router, prefix="/storage", tags=["storage"])

# Basic API status endpoint
@api_router.get("/")
async def api_status():
    """API status endpoint"""
    return {
        "message": "NovaStack API v1",
        "status": "active",
        "version": "0.1.0",
        "features": [
            "User Authentication & Authorization",
            "Database Project Management", 
            "Auto-Generated REST APIs",
            "Auto-Generated GraphQL APIs",
            "PostgreSQL & MySQL Support",
            "Docker Container Orchestration"
        ],
        "endpoints": {
            "auth": "/api/v1/auth",
            "projects": "/api/v1/projects",
            "api_generation": "/api/v1/generate",
            "graphql": "/api/v1/graphql",
            "storage": "/api/v1/storage",
            "docs": "/docs",
            "health": "/health"
        }
    }