'use client';

import { useState, useEffect } from 'react';
import { useApi } from '@/lib/api';

export default function TestConnection() {
  const [backendStatus, setBackendStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const api = useApi();

  useEffect(() => {
    const testConnection = async () => {
      try {
        setLoading(true);
        const response = await api.healthCheck();
        
        if (response.status === 200) {
          setBackendStatus(response.data);
          setError(null);
        } else {
          setError(`Backend returned status ${response.status}: ${response.error}`);
        }
      } catch (err) {
        setError(`Connection failed: ${err}`);
      } finally {
        setLoading(false);
      }
    };

    testConnection();
  }, []);

  const testAuth = async () => {
    try {
      const response = await api.register('test@example.com', 'password123', 'password123');
      console.log('Auth test response:', response);
    } catch (err) {
      console.error('Auth test failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Testing backend connection...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">NovaStack Connection Test</h1>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Backend Health Status</h2>
          
          {error ? (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="text-red-400">❌</div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Connection Failed</h3>
                  <div className="mt-2 text-sm text-red-700">{error}</div>
                </div>
              </div>
            </div>
          ) : backendStatus ? (
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex">
                <div className="text-green-400">✅</div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">Backend Connected Successfully</h3>
                  <div className="mt-2 text-sm text-green-700">
                    <pre className="whitespace-pre-wrap font-mono text-xs">
                      {JSON.stringify(backendStatus, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">API Endpoints Test</h2>
          
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900">Frontend URL:</h3>
              <p className="text-blue-600">http://localhost:3000</p>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900">Backend URL:</h3>
              <p className="text-blue-600">http://127.0.0.1:8000</p>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900">Available Endpoints:</h3>
              <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                <li><code className="bg-gray-100 px-2 py-1 rounded">GET /health</code> - Health check</li>
                <li><code className="bg-gray-100 px-2 py-1 rounded">GET /</code> - API information</li>
                <li><code className="bg-gray-100 px-2 py-1 rounded">POST /api/v1/auth/login</code> - User login</li>
                <li><code className="bg-gray-100 px-2 py-1 rounded">POST /api/v1/auth/register</code> - User registration</li>
                <li><code className="bg-gray-100 px-2 py-1 rounded">GET /api/v1/projects</code> - List projects</li>
                <li><code className="bg-gray-100 px-2 py-1 rounded">GET /docs</code> - API documentation</li>
              </ul>
            </div>
            
            <div className="pt-4">
              <button 
                onClick={testAuth}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
              >
                Test Auth Endpoint
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 text-center">
          <a 
            href="/dashboard" 
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
          >
            Go to Dashboard
          </a>
          <a 
            href="http://127.0.0.1:8000/docs" 
            target="_blank" 
            rel="noopener noreferrer"
            className="ml-4 inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            View API Docs
          </a>
        </div>
      </div>
    </div>
  );
}