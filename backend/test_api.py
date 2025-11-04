"""
Quick test script for NovaStack API

This script tests our API endpoints without needing a browser.
"""

import asyncio
import json
import sys
sys.path.append('.')

from app.main import app
from fastapi.testclient import TestClient

def test_novastack_api():
    """Test NovaStack API endpoints"""
    
    print("🧪 Testing NovaStack API...")
    
    # Create test client
    client = TestClient(app)
    
    # Test root endpoint
    print("\n📍 Testing root endpoint (/)...")
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test health endpoint
    print("\n🏥 Testing health endpoint (/health)...")
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test config endpoint
    print("\n⚙️ Testing config endpoint (/config)...")
    response = client.get("/config")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test API v1 endpoint
    print("\n🔌 Testing API v1 endpoint (/api/v1/)...")
    response = client.get("/api/v1/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_novastack_api()