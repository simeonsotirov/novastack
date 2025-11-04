"""
Configuration management for NovaStack

This file handles all environment variables and application settings.
Simple configuration without heavy dependencies for now.
"""

import os
from typing import List


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # API Configuration
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.api_reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"
        self.debug: bool = os.getenv("DEBUG", "true").lower() == "true"
        
        # Database Configuration  
        self.database_url: str = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/novastack")
        
        # Redis Configuration
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # JWT Configuration
        self.jwt_secret: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production-must-be-very-long")
        self.jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours
        
        # MinIO/S3 Configuration
        self.minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Docker Configuration (for database provisioning)
        self.docker_host: str = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
        
        # CORS Configuration
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        self.cors_origins: List[str] = [url.strip() for url in cors_origins_str.split(',')]
        
        # Monitoring
        self.prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "9090"))
        self.grafana_port: int = int(os.getenv("GRAFANA_PORT", "3001"))
        
        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "info")
        
        # Validate JWT secret
        if len(self.jwt_secret) < 32:
            raise ValueError('JWT secret must be at least 32 characters long')


# Create global settings instance
settings = Settings()

# Database URL components for easier access
def get_database_components():
    """Extract database components from URL for connection management"""
    import urllib.parse
    
    parsed = urllib.parse.urlparse(settings.database_url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/') or 'novastack',
        'username': parsed.username or 'admin',
        'password': parsed.password or 'password'
    }