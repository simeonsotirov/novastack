"""
Docker Management Service for NovaStack

This service handles all Docker operations for database provisioning:
- Creating new database containers (PostgreSQL/MySQL)
- Managing container lifecycle (start, stop, remove)
- Network and port management
- Container health monitoring

Think of this as the "container orchestrator" - it's like having a robot that
can instantly create and manage database servers for our users.
"""

import docker
import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
import secrets
import string

from app.core.config import settings

logger = logging.getLogger(__name__)


class DockerManager:
    """
    Service for managing Docker containers for database provisioning
    
    This class handles all Docker operations needed to create isolated
    databases for user projects.
    """
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            # Connect to Docker daemon
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            logger.info("✅ Docker client connected successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Docker: {e}")
            self.client = None
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password for database
        
        Args:
            length: Length of password to generate
            
        Returns:
            Secure random password
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def _get_available_port(self, start_port: int = 5433) -> int:
        """
        Find an available port for the database container
        
        Args:
            start_port: Port to start searching from
            
        Returns:
            Available port number
        """
        import socket
        
        port = start_port
        while port < 65535:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                port += 1
        
        raise Exception("No available ports found")
    
    async def create_postgresql_container(
        self,
        project_id: str,
        database_name: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        Create a new PostgreSQL container for a project
        
        Args:
            project_id: Unique project identifier
            database_name: Name of the database to create
            user_id: ID of the user who owns this project
            
        Returns:
            Dictionary with container info (id, port, connection details)
        """
        if not self.client:
            raise Exception("Docker client not available")
        
        # Generate secure credentials
        db_password = self._generate_secure_password()
        db_user = f"user_{project_id[:8]}"
        
        # Find available port
        host_port = self._get_available_port()
        
        # Container configuration
        container_name = f"novastack_pg_{project_id[:12]}"
        
        environment = {
            'POSTGRES_DB': database_name,
            'POSTGRES_USER': db_user,
            'POSTGRES_PASSWORD': db_password,
            'POSTGRES_INITDB_ARGS': '--auth-host=scram-sha-256'
        }
        
        # Create and start container
        try:
            container = self.client.containers.run(
                image="postgres:15-alpine",
                name=container_name,
                environment=environment,
                ports={'5432/tcp': host_port},
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                labels={
                    'novastack.project_id': project_id,
                    'novastack.user_id': user_id,
                    'novastack.database_type': 'postgresql',
                    'novastack.created_at': datetime.utcnow().isoformat()
                },
                # Resource limits for safety
                mem_limit='512m',
                cpu_quota=50000  # 50% of one CPU
            )
            
            # Wait for container to be ready
            await self._wait_for_database_ready(container.id, 'postgresql', host_port)
            
            # Build connection string
            connection_string = f"postgresql://{db_user}:{db_password}@localhost:{host_port}/{database_name}"
            
            logger.info(f"✅ PostgreSQL container created: {container_name}")
            
            return {
                'container_id': container.id,
                'container_name': container_name,
                'host_port': str(host_port),
                'database_name': database_name,
                'username': db_user,
                'password': db_password,
                'connection_string': connection_string,
                'database_type': 'postgresql'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create PostgreSQL container: {e}")
            raise Exception(f"Failed to create PostgreSQL database: {str(e)}")
    
    async def create_mysql_container(
        self,
        project_id: str,
        database_name: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        Create a new MySQL container for a project
        
        Args:
            project_id: Unique project identifier
            database_name: Name of the database to create
            user_id: ID of the user who owns this project
            
        Returns:
            Dictionary with container info (id, port, connection details)
        """
        if not self.client:
            raise Exception("Docker client not available")
        
        # Generate secure credentials
        db_password = self._generate_secure_password()
        root_password = self._generate_secure_password()
        db_user = f"user_{project_id[:8]}"
        
        # Find available port
        host_port = self._get_available_port(start_port=3307)
        
        # Container configuration
        container_name = f"novastack_mysql_{project_id[:12]}"
        
        environment = {
            'MYSQL_ROOT_PASSWORD': root_password,
            'MYSQL_DATABASE': database_name,
            'MYSQL_USER': db_user,
            'MYSQL_PASSWORD': db_password,
            'MYSQL_CHARSET': 'utf8mb4',
            'MYSQL_COLLATION': 'utf8mb4_unicode_ci'
        }
        
        # Create and start container
        try:
            container = self.client.containers.run(
                image="mysql:8.0",
                name=container_name,
                environment=environment,
                ports={'3306/tcp': host_port},
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                labels={
                    'novastack.project_id': project_id,
                    'novastack.user_id': user_id,
                    'novastack.database_type': 'mysql',
                    'novastack.created_at': datetime.utcnow().isoformat()
                },
                # Resource limits for safety
                mem_limit='512m',
                cpu_quota=50000  # 50% of one CPU
            )
            
            # Wait for container to be ready
            await self._wait_for_database_ready(container.id, 'mysql', host_port)
            
            # Build connection string
            connection_string = f"mysql://{db_user}:{db_password}@localhost:{host_port}/{database_name}"
            
            logger.info(f"✅ MySQL container created: {container_name}")
            
            return {
                'container_id': container.id,
                'container_name': container_name,
                'host_port': str(host_port),
                'database_name': database_name,
                'username': db_user,
                'password': db_password,
                'connection_string': connection_string,
                'database_type': 'mysql'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create MySQL container: {e}")
            raise Exception(f"Failed to create MySQL database: {str(e)}")
    
    async def _wait_for_database_ready(
        self,
        container_id: str,
        db_type: str,
        port: int,
        timeout: int = 60
    ):
        """
        Wait for database container to be ready to accept connections
        
        Args:
            container_id: Container ID to check
            db_type: Database type ('postgresql' or 'mysql')
            port: Port to check
            timeout: Maximum time to wait in seconds
        """
        import time
        import socket
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if port is responding
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    if sock.connect_ex(('localhost', port)) == 0:
                        # Port is open, wait a bit more for DB to initialize
                        await asyncio.sleep(2)
                        logger.info(f"✅ Database container {container_id[:12]} is ready")
                        return
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        raise Exception(f"Database container {container_id[:12]} failed to start within {timeout} seconds")
    
    def stop_container(self, container_id: str) -> bool:
        """
        Stop a database container
        
        Args:
            container_id: Container ID to stop
            
        Returns:
            True if stopped successfully
        """
        if not self.client:
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            logger.info(f"✅ Container {container_id[:12]} stopped")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to stop container {container_id[:12]}: {e}")
            return False
    
    def remove_container(self, container_id: str) -> bool:
        """
        Remove a database container (deletes all data!)
        
        Args:
            container_id: Container ID to remove
            
        Returns:
            True if removed successfully
        """
        if not self.client:
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            logger.info(f"✅ Container {container_id[:12]} removed")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to remove container {container_id[:12]}: {e}")
            return False
    
    def get_container_status(self, container_id: str) -> Optional[Dict[str, str]]:
        """
        Get status information about a container
        
        Args:
            container_id: Container ID to check
            
        Returns:
            Dictionary with container status information
        """
        if not self.client:
            return None
        
        try:
            container = self.client.containers.get(container_id)
            return {
                'id': container.id,
                'name': container.name,
                'status': container.status,
                'created': container.attrs['Created'],
                'image': container.image.tags[0] if container.image.tags else 'unknown'
            }
        except Exception as e:
            logger.error(f"❌ Failed to get container status {container_id[:12]}: {e}")
            return None
    
    def get_container_status(self, container_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status information for a container by name
        
        Args:
            container_name: Name of the container
            
        Returns:
            Container status information or None if not found
        """
        if not self.client:
            return None
        
        try:
            container = self.client.containers.get(container_name)
            
            # Get detailed container information
            container.reload()
            
            # Parse creation time
            created_str = container.attrs.get('Created', '')
            created = None
            if created_str:
                try:
                    # Parse ISO format datetime string
                    # Format: "2023-12-01T10:30:45.123456789Z"
                    if created_str.endswith('Z'):
                        created_str = created_str[:-1]
                    if '.' in created_str:
                        created_str = created_str.split('.')[0]
                    created = datetime.fromisoformat(created_str)
                except:
                    created = datetime.utcnow()
            
            # Get port mappings
            ports = {}
            if container.attrs.get('NetworkSettings', {}).get('Ports'):
                for container_port, host_bindings in container.attrs['NetworkSettings']['Ports'].items():
                    if host_bindings:
                        ports[container_port] = host_bindings[0]['HostPort']
            
            return {
                'container_id': container.id,
                'name': container.name,
                'status': container.status,
                'created': created or datetime.utcnow(),
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'ports': ports,
                'resource_usage': {}  # Could be expanded with stats
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get container status for {container_name}: {e}")
            return None
    
    def restart_container(self, container_name: str) -> bool:
        """
        Restart a container by name
        
        Args:
            container_name: Name of the container to restart
            
        Returns:
            True if restarted successfully
        """
        if not self.client:
            return False
        
        try:
            container = self.client.containers.get(container_name)
            container.restart()
            logger.info(f"✅ Restarted container: {container_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to restart container {container_name}: {e}")
            return False
    
    def stop_container(self, container_name: str) -> bool:
        """
        Stop a container by name
        
        Args:
            container_name: Name of the container to stop
            
        Returns:
            True if stopped successfully
        """
        if not self.client:
            return False
        
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            logger.info(f"✅ Stopped container: {container_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to stop container {container_name}: {e}")
            return False
    
    def start_container(self, container_name: str) -> bool:
        """
        Start a stopped container by name
        
        Args:
            container_name: Name of the container to start
            
        Returns:
            True if started successfully
        """
        if not self.client:
            return False
        
        try:
            container = self.client.containers.get(container_name)
            container.start()
            logger.info(f"✅ Started container: {container_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start container {container_name}: {e}")
            return False

    def list_novastack_containers(self) -> List[Dict[str, str]]:
        """
        List all NovaStack database containers
        
        Returns:
            List of container information dictionaries
        """
        if not self.client:
            return []
        
        try:
            containers = self.client.containers.list(
                all=True,
                filters={'label': 'novastack.project_id'}
            )
            
            result = []
            for container in containers:
                labels = container.labels or {}
                result.append({
                    'id': container.id,
                    'name': container.name,
                    'status': container.status,
                    'project_id': labels.get('novastack.project_id', 'unknown'),
                    'user_id': labels.get('novastack.user_id', 'unknown'),
                    'database_type': labels.get('novastack.database_type', 'unknown'),
                    'created_at': labels.get('novastack.created_at', 'unknown')
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to list containers: {e}")
            return []


# Global Docker manager instance
docker_manager = DockerManager()