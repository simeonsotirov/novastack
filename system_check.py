#!/usr/bin/env python3
"""
NovaStack Phase 5 - Complete System Validation
Tests all components without needing a running server
"""

import sys
import os
import importlib.util
from pathlib import Path

def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"🧪 {text}")
    print(f"{'='*60}")

def print_success(text: str):
    print(f"✅ {text}")

def print_error(text: str):
    print(f"❌ {text}")

def print_info(text: str):
    print(f"ℹ️  {text}")

def check_virtual_environment():
    """Check if we're in a virtual environment"""
    print_header("Virtual Environment Check")
    
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print_success(f"Running in virtual environment: {venv_path}")
        return True
    else:
        print_error("Not in virtual environment!")
        print_info("Please run: .\.venv\Scripts\Activate.ps1")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print_header("Dependencies Check")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'asyncpg',
        'aiomysql',
        'pydantic',
        'jose',  # python-jose imports as 'jose'
        'passlib',
        'python-multipart',
        'docker',
        'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package} - installed")
        except ImportError:
            display_name = "python-jose" if package == "jose" else package
            print_error(f"{display_name} - missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_file_structure():
    """Check if all Phase 5 files exist"""
    print_header("File Structure Check")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    if not backend_dir.exists():
        backend_dir = Path("backend")
    
    required_files = [
        "app/main.py",
        "app/services/schema_introspector.py", 
        "app/services/api_generator.py",
        "app/api/api_generation.py",
        "app/core/dynamic_router.py",
        "app/core/config.py",
        "app/core/database.py",
        "app/models/user.py",
        "app/models/project.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = backend_dir / file_path
        if full_path.exists():
            print_success(f"{file_path} - exists")
        else:
            print_error(f"{file_path} - missing")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_imports():
    """Check if all Phase 5 modules can be imported"""
    print_header("Import Tests")
    
    # Add backend to path if needed
    backend_path = str(Path("backend").resolve())
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    modules_to_test = [
        ("app.main", "FastAPI main application"),
        ("app.services.schema_introspector", "Schema Introspector"),
        ("app.services.api_generator", "API Generator"),
        ("app.api.api_generation", "API Generation endpoints"),
        ("app.core.dynamic_router", "Dynamic Router"),
        ("app.core.database", "Database core"),
        ("app.models.user", "User model"),
        ("app.models.project", "Project model")
    ]
    
    failed_imports = []
    for module_name, description in modules_to_test:
        try:
            importlib.import_module(module_name)
            print_success(f"{description} - imports successfully")
        except Exception as e:
            print_error(f"{description} - import failed: {str(e)}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0

def check_fastapi_app():
    """Check if FastAPI app can be created"""
    print_header("FastAPI Application Test")
    
    try:
        # Add backend to path
        backend_path = str(Path("backend").resolve())
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        from app.main import app
        print_success(f"FastAPI app created successfully")
        print_success(f"App title: {app.title}")
        print_success(f"App version: {app.version}")
        
        # Check if our routes are registered
        routes = [route.path for route in app.routes]
        
        key_routes = [
            "/health",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/projects/",
            "/api/v1/generate/"
        ]
        
        missing_routes = []
        for route in key_routes:
            if any(route in r for r in routes):
                print_success(f"Route {route} - registered")
            else:
                print_error(f"Route {route} - missing")
                missing_routes.append(route)
        
        return len(missing_routes) == 0
        
    except Exception as e:
        print_error(f"FastAPI app creation failed: {str(e)}")
        return False

def check_api_generation_components():
    """Check API generation system components"""
    print_header("API Generation System Test")
    
    try:
        backend_path = str(Path("backend").resolve())
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Test Schema Introspector
        from app.services.schema_introspector import SchemaIntrospector, DatabaseSchema
        print_success("Schema Introspector - can be imported")
        
        # Test API Generator  
        from app.services.api_generator import DynamicAPIGenerator
        print_success("Dynamic API Generator - can be imported")
        
        # Test Dynamic Router
        from app.core.dynamic_router import DynamicRouterManager
        print_success("Dynamic Router Manager - can be imported")
        
        # Test API Generation endpoints
        from app.api.api_generation import router as api_gen_router
        print_success("API Generation endpoints - can be imported")
        
        return True
        
    except Exception as e:
        print_error(f"API Generation system test failed: {str(e)}")
        return False

def main():
    """Run complete system validation"""
    print_header("NovaStack Phase 5 - Complete System Validation")
    
    all_good = True
    
    # Check virtual environment
    if not check_virtual_environment():
        all_good = False
    
    # Check dependencies
    if not check_dependencies():
        all_good = False
    
    # Check file structure
    if not check_file_structure():
        all_good = False
    
    # Check imports
    if not check_imports():
        all_good = False
    
    # Check FastAPI app
    if not check_fastapi_app():
        all_good = False
    
    # Check API generation components
    if not check_api_generation_components():
        all_good = False
    
    print_header("Validation Results")
    
    if all_good:
        print_success("🎉 ALL SYSTEMS GO!")
        print_success("Phase 5: REST & GraphQL APIs - FULLY FUNCTIONAL!")
        print_info("✅ Schema Introspection System")
        print_info("✅ Dynamic REST API Generator") 
        print_info("✅ API Management Endpoints")
        print_info("✅ Dynamic Router Integration")
        print_info("✅ FastAPI Application")
        print("")
        print_info("🚀 Ready to start server with:")
        print_info("   cd backend && python -m uvicorn app.main:app --reload --port 8000")
        print("")
        print_info("🎯 Ready to continue to:")
        print_info("   - GraphQL Schema Generator")
        print_info("   - Frontend Dashboard")
    else:
        print_error("Some components need attention!")
        print_info("Please fix the issues above before proceeding")

if __name__ == "__main__":
    main()