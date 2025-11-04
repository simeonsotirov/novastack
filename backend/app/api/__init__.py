"""
API Router package for NovaStack

This file sets up the main API router and includes all sub-routers
for different features (auth, projects, etc.)
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Import sub-routers
from app.api.auth import router as auth_router
# from app.api.projects import router as projects_router
# from app.api.storage import router as storage_router

# Include sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
# api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
# api_router.include_router(storage_router, prefix="/storage", tags=["storage"])

# Basic API status endpoint
@api_router.get("/")
async def api_status():
    """API status endpoint"""
    return {
        "message": "NovaStack API v1",
        "status": "active",
        "endpoints": {
            "auth": "/api/v1/auth",
            "projects": "/api/v1/projects", 
            "storage": "/api/v1/storage",
            "docs": "/docs"
        }
    }