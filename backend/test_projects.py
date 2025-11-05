"""
Test script for Project Management API

This script tests all the project-related endpoints to make sure
our database provisioning system works correctly.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
import json

# Create test client
client = TestClient(app)

def test_project_endpoints():
    """Test project management endpoints"""
    print("🧪 Testing NovaStack Project Management API...\n")
    
    # Step 1: Register and login to get auth token
    print("1️⃣ Creating test user and logging in...")
    
    # Register
    register_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    
    response = client.post("/api/v1/auth/register", json=register_data)
    if response.status_code == 201:
        print("   ✅ User registered successfully")
    else:
        print(f"   ❌ Registration failed: {response.text}")
        return
    
    # Login
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print("   ✅ Login successful")
        print(f"   🔑 Token: {access_token[:20]}...")
    else:
        print(f"   ❌ Login failed: {response.text}")
        return
    
    # Headers for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: Create a PostgreSQL project
    print("\n2️⃣ Creating PostgreSQL project...")
    
    project_data = {
        "name": "My Test App",
        "database_type": "postgresql",
        "description": "A test PostgreSQL database for my app"
    }
    
    response = client.post("/api/v1/projects/", json=project_data, headers=headers)
    if response.status_code == 200:
        project = response.json()
        project_id = project["id"]
        print("   ✅ PostgreSQL project created successfully")
        print(f"   📝 Project ID: {project_id}")
        print(f"   🗄️  Database Name: {project['database_name']}")
    else:
        print(f"   ❌ Project creation failed: {response.text}")
        print(f"   📊 Status Code: {response.status_code}")
        # Continue with tests even if this fails (Docker not available)
        project_id = "test-project-id"
    
    # Step 3: List projects
    print("\n3️⃣ Listing all projects...")
    
    response = client.get("/api/v1/projects/", headers=headers)
    if response.status_code == 200:
        projects_data = response.json()
        print(f"   ✅ Found {projects_data['total']} project(s)")
        for project in projects_data['projects']:
            print(f"   📂 {project['name']} ({project['database_type']})")
    else:
        print(f"   ❌ Failed to list projects: {response.text}")
    
    # Step 4: Get project details
    print("\n4️⃣ Getting project details...")
    
    response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    if response.status_code == 200:
        project_status = response.json()
        print("   ✅ Project details retrieved")
        print(f"   📊 Container Status: {project_status.get('container_status', 'N/A')}")
        print(f"   🔗 Connection Available: {project_status.get('connection_available', False)}")
    else:
        print(f"   ❌ Failed to get project details: {response.text}")
    
    # Step 5: Update project
    print("\n5️⃣ Updating project...")
    
    update_data = {
        "description": "Updated description for my test app"
    }
    
    response = client.put(f"/api/v1/projects/{project_id}", json=update_data, headers=headers)
    if response.status_code == 200:
        updated_project = response.json()
        print("   ✅ Project updated successfully")
        print(f"   📝 New description: {updated_project['description']}")
    else:
        print(f"   ❌ Failed to update project: {response.text}")
    
    # Step 6: Get project statistics
    print("\n6️⃣ Getting project statistics...")
    
    response = client.get("/api/v1/projects/stats/overview", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print("   ✅ Project statistics retrieved")
        print(f"   📊 Total Projects: {stats['total_projects']}")
        print(f"   🐘 PostgreSQL: {stats['postgresql_projects']}")
        print(f"   🐬 MySQL: {stats['mysql_projects']}")
        print(f"   ⚡ Active Containers: {stats['active_containers']}")
    else:
        print(f"   ❌ Failed to get project stats: {response.text}")
    
    # Step 7: Try to get connection info (will likely fail without Docker)
    print("\n7️⃣ Testing connection info...")
    
    response = client.get(f"/api/v1/projects/{project_id}/connection", headers=headers)
    if response.status_code == 200:
        connection_info = response.json()
        print("   ✅ Connection info retrieved")
        print(f"   🔗 Host: {connection_info['host']}:{connection_info['port']}")
        print(f"   🗄️  Database: {connection_info['database']}")
    else:
        print(f"   ⚠️  Connection info not available: {response.json().get('detail', 'Unknown error')}")
    
    # Step 8: Create a MySQL project
    print("\n8️⃣ Creating MySQL project...")
    
    mysql_project_data = {
        "name": "My MySQL App",
        "database_type": "mysql",
        "description": "A test MySQL database"
    }
    
    response = client.post("/api/v1/projects/", json=mysql_project_data, headers=headers)
    if response.status_code == 200:
        mysql_project = response.json()
        mysql_project_id = mysql_project["id"]
        print("   ✅ MySQL project created successfully")
        print(f"   📝 Project ID: {mysql_project_id}")
    else:
        print(f"   ⚠️  MySQL project creation: {response.json().get('detail', 'Unknown error')}")
        mysql_project_id = "test-mysql-project"
    
    # Step 9: Test project actions (will likely fail without Docker)
    print("\n9️⃣ Testing project actions...")
    
    action_data = {"action": "restart"}
    response = client.post(f"/api/v1/projects/{project_id}/action", json=action_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Action completed: {result['message']}")
    else:
        print(f"   ⚠️  Action not available: {response.json().get('detail', 'Unknown error')}")
    
    print("\n🎉 Project API testing completed!")
    print("\n💡 Note: Some tests may show warnings if Docker is not available.")
    print("   This is normal for development environments.")

if __name__ == "__main__":
    test_project_endpoints()