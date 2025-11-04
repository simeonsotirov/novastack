# NovaStack FastAPI Application
"""
NovaStack - Open-source Database-as-a-Service platform

This is the main FastAPI application entry point.
It sets up the API routes, middleware, and database connections.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
import asyncio

# Import our application components
from app.core.config import settings
from app.core.database import init_db, close_db, test_connection
from app.api import api_router

# Set up structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    
    This function handles startup and shutdown events:
    - On startup: Initialize database, test connections
    - On shutdown: Close database connections gracefully
    """
    # Startup
    logger.info("🚀 Starting NovaStack API...")
    
    # Test database connection
    if await test_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed!")
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Initialize database tables
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise HTTPException(status_code=500, detail="Database initialization failed")
    
    logger.info("✅ NovaStack API started successfully!")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down NovaStack API...")
    await close_db()
    logger.info("✅ Shutdown complete")


# Create FastAPI application with lifespan management
app = FastAPI(
    title="NovaStack API",
    description="Open-source Database-as-a-Service platform built for European developers",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware - allows frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time header to all requests"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint - shows API status and configuration"""
    return {
        "message": "Welcome to NovaStack API! 🚀",
        "status": "running",
        "version": "0.1.0",
        "environment": "development" if settings.debug else "production",
        "docs": "/docs",
        "features": {
            "database_types": ["postgresql", "mysql"],
            "api_types": ["REST", "GraphQL"],
            "auth": "JWT",
            "storage": "MinIO (S3-compatible)",
            "realtime": "WebSocket"
        }
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint for monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "0.1.0",
        "uptime": time.time(),  # Will be improved later with actual uptime
        "services": {}
    }
    
    # Test database connection
    try:
        db_healthy = await test_connection()
        health_status["services"]["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Add other service checks here later (Redis, MinIO, etc.)
    
    return health_status

@app.get("/config")
async def get_config():
    """Get public configuration information (no secrets!)"""
    return {
        "api_version": "0.1.0",
        "debug_mode": settings.debug,
        "cors_origins": settings.cors_origins,
        "supported_databases": ["postgresql", "mysql"],
        "jwt_expire_minutes": settings.jwt_expire_minutes
    }

# Global exception handler
@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors gracefully"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )