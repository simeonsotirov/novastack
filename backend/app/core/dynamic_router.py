"""
Dynamic Router Management

This module handles the registration and serving of dynamically generated APIs.
It allows NovaStack to serve auto-generated REST endpoints at runtime without
requiring server restarts.

Key features:
- Runtime router registration
- Automatic endpoint discovery
- Request routing to generated APIs
- Middleware integration
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.routing import APIRouter
from typing import Dict, Any, Optional
import logging

from app.services.api_generator import api_generator

logger = logging.getLogger(__name__)


class DynamicRouterManager:
    """
    Manages dynamically generated API routers
    
    This class handles:
    - Registering generated APIs with the main app
    - Routing requests to the correct generated endpoints
    - Managing API lifecycle (creation, updates, removal)
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.registered_projects = set()
        
        # Add catch-all route for generated APIs
        self._setup_dynamic_routing()
    
    def _setup_dynamic_routing(self):
        """Setup dynamic routing for generated APIs"""
        
        @self.app.api_route(
            "/api/data/{project_id}/{path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            include_in_schema=False
        )
        async def dynamic_api_handler(request: Request, project_id: str, path: str):
            """
            Handle requests to dynamically generated APIs
            
            This function:
            1. Checks if API exists for the project
            2. Routes the request to the appropriate generated endpoint
            3. Returns the response from the generated API
            """
            try:
                # Check if API is generated for this project
                api_info = api_generator.generated_apis.get(project_id)
                
                if not api_info:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No API generated for project {project_id}. Generate API first."
                    )
                
                # Get the generated router
                router = api_info['router']
                
                # Find matching route in the generated router
                method = request.method.lower()
                full_path = f"/api/data/{project_id}/{path}" if path else f"/api/data/{project_id}/"
                
                # Look for matching route
                for route in router.routes:
                    if hasattr(route, 'methods') and method.upper() in route.methods:
                        # Check if path matches (simplified matching)
                        route_path = str(route.path)
                        
                        # Handle exact matches and parameter matches
                        if self._path_matches(route_path, full_path):
                            # Execute the route handler
                            try:
                                # Get route handler
                                handler = route.endpoint
                                
                                # Prepare parameters
                                path_params = self._extract_path_params(route_path, full_path)
                                query_params = dict(request.query_params)
                                
                                # Handle request body for POST/PUT
                                body = None
                                if method in ['post', 'put', 'patch']:
                                    try:
                                        body = await request.json()
                                    except:
                                        body = {}
                                
                                # Call handler with appropriate parameters
                                if method == 'get':
                                    if path_params:
                                        # Single record endpoint
                                        record_id = path_params.get('record_id') or path_params.get('id')
                                        if record_id:
                                            result = await handler(record_id=record_id)
                                        else:
                                            result = await handler(request, **query_params)
                                    else:
                                        result = await handler(request, **query_params)
                                elif method in ['post']:
                                    result = await handler(body)
                                elif method in ['put', 'patch']:
                                    record_id = path_params.get('record_id') or path_params.get('id')
                                    result = await handler(record_id, body)
                                elif method == 'delete':
                                    record_id = path_params.get('record_id') or path_params.get('id')
                                    result = await handler(record_id)
                                else:
                                    result = await handler()
                                
                                return result
                                
                            except Exception as e:
                                logger.error(f"Error executing generated API endpoint: {str(e)}")
                                raise HTTPException(
                                    status_code=500,
                                    detail=f"Error executing API endpoint: {str(e)}"
                                )
                
                # No matching route found
                raise HTTPException(
                    status_code=404,
                    detail=f"Endpoint not found: {method.upper()} {full_path}"
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in dynamic API handler: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )
    
    def _path_matches(self, route_path: str, request_path: str) -> bool:
        """
        Check if a route path matches a request path
        
        Handles both exact matches and parameterized paths
        """
        # Remove query parameters from request path
        request_path = request_path.split('?')[0]
        
        # Simple exact match
        if route_path == request_path:
            return True
        
        # Handle parameterized paths
        route_parts = route_path.strip('/').split('/')
        request_parts = request_path.strip('/').split('/')
        
        if len(route_parts) != len(request_parts):
            return False
        
        for route_part, request_part in zip(route_parts, request_parts):
            if route_part.startswith('{') and route_part.endswith('}'):
                # This is a parameter, so it matches any value
                continue
            elif route_part != request_part:
                return False
        
        return True
    
    def _extract_path_params(self, route_path: str, request_path: str) -> Dict[str, str]:
        """Extract path parameters from the request path"""
        params = {}
        
        route_parts = route_path.strip('/').split('/')
        request_parts = request_path.strip('/').split('/')
        
        for route_part, request_part in zip(route_parts, request_parts):
            if route_part.startswith('{') and route_part.endswith('}'):
                param_name = route_part[1:-1]  # Remove { and }
                params[param_name] = request_part
        
        return params
    
    def register_project_api(self, project_id: str) -> bool:
        """
        Register a project's generated API with the main application
        
        This makes the generated endpoints available for requests.
        """
        try:
            if project_id not in api_generator.generated_apis:
                logger.warning(f"No generated API found for project {project_id}")
                return False
            
            # API is already accessible through dynamic routing
            self.registered_projects.add(project_id)
            
            logger.info(f"Registered API for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register API for project {project_id}: {str(e)}")
            return False
    
    def unregister_project_api(self, project_id: str) -> bool:
        """
        Unregister a project's generated API
        
        This stops serving the generated endpoints.
        """
        try:
            if project_id in self.registered_projects:
                self.registered_projects.remove(project_id)
            
            logger.info(f"Unregistered API for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister API for project {project_id}: {str(e)}")
            return False
    
    def is_project_registered(self, project_id: str) -> bool:
        """Check if a project's API is registered"""
        return project_id in self.registered_projects
    
    def get_registered_projects(self) -> list:
        """Get list of projects with registered APIs"""
        return list(self.registered_projects)


# Global instance (will be initialized in main.py)
dynamic_router_manager: Optional[DynamicRouterManager] = None


def init_dynamic_router_manager(app: FastAPI) -> DynamicRouterManager:
    """Initialize the dynamic router manager"""
    global dynamic_router_manager
    dynamic_router_manager = DynamicRouterManager(app)
    return dynamic_router_manager


def get_dynamic_router_manager() -> DynamicRouterManager:
    """Get the dynamic router manager instance"""
    if dynamic_router_manager is None:
        raise RuntimeError("Dynamic router manager not initialized")
    return dynamic_router_manager