'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { 
  Database, 
  ArrowLeft, 
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import Link from 'next/link';

interface DatabaseConnection {
  host: string;
  port: string;
  database: string;
  username: string;
  password: string;
}

export default function NewProjectPage() {
  const [step, setStep] = useState(1);
  const [projectData, setProjectData] = useState({
    name: '',
    description: '',
    database_type: 'postgresql' as 'postgresql' | 'mysql'
  });
  const [connectionData, setConnectionData] = useState<DatabaseConnection>({
    host: '',
    port: '',
    database: '',
    username: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [error, setError] = useState('');

  const router = useRouter();

  const handleProjectSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectData.name.trim()) {
      setError('Project name is required');
      return;
    }
    setError('');
    setStep(2);
  };

  const testConnection = async () => {
    setConnectionStatus('testing');
    setError('');

    try {
      // TODO: Replace with actual API call
      const response = await fetch('http://localhost:8000/api/database/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          database_type: projectData.database_type,
          ...connectionData
        })
      });

      if (response.ok) {
        setConnectionStatus('success');
        toast.success('Connection successful!');
      } else {
        const errorData = await response.json();
        setConnectionStatus('error');
        setError(errorData.message || 'Connection failed');
      }
    } catch (err) {
      setConnectionStatus('error');
      setError('Network error. Please try again.');
      console.error('Connection test error:', err);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // TODO: Replace with actual API call
      const response = await fetch('http://localhost:8000/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...projectData,
          connection: connectionData
        })
      });

      if (response.ok) {
        const newProject = await response.json();
        toast.success('Project created successfully!');
        router.push(`/dashboard/projects/${newProject.id}`);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Failed to create project');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Project creation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getDefaultPort = (dbType: 'postgresql' | 'mysql') => {
    return dbType === 'postgresql' ? '5432' : '3306';
  };

  const handleDatabaseTypeChange = (type: 'postgresql' | 'mysql') => {
    setProjectData(prev => ({ ...prev, database_type: type }));
    setConnectionData(prev => ({ ...prev, port: getDefaultPort(type) }));
  };

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <Link href="/dashboard/projects">
            <Button variant="outline" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          </Link>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Create New Project</h2>
            <p className="text-gray-600">Set up a new database project and generate APIs</p>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}>
              1
            </div>
            <span className="font-medium">Project Details</span>
          </div>
          <div className="flex-1 h-px bg-gray-300" />
          <div className={`flex items-center space-x-2 ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}>
              2
            </div>
            <span className="font-medium">Database Connection</span>
          </div>
        </div>

        {/* Step 1: Project Details */}
        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle>Project Information</CardTitle>
              <CardDescription>
                Provide basic information about your project
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProjectSubmit} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="name">Project Name *</Label>
                  <Input
                    id="name"
                    placeholder="e.g., E-commerce API"
                    value={projectData.name}
                    onChange={(e) => setProjectData(prev => ({
                      ...prev,
                      name: e.target.value
                    }))}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe what this project does..."
                    value={projectData.description}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setProjectData(prev => ({
                      ...prev,
                      description: e.target.value
                    }))}
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Database Type *</Label>
                  <div className="grid grid-cols-2 gap-4">
                    <button
                      type="button"
                      onClick={() => handleDatabaseTypeChange('postgresql')}
                      className={`p-4 border rounded-lg text-left transition-colors ${
                        projectData.database_type === 'postgresql'
                          ? 'border-blue-500 bg-blue-50 text-blue-900'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <Database className="h-6 w-6 text-blue-600" />
                        <div>
                          <h3 className="font-medium">PostgreSQL</h3>
                          <p className="text-sm text-gray-500">Advanced features, JSONB support</p>
                        </div>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDatabaseTypeChange('mysql')}
                      className={`p-4 border rounded-lg text-left transition-colors ${
                        projectData.database_type === 'mysql'
                          ? 'border-orange-500 bg-orange-50 text-orange-900'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <Database className="h-6 w-6 text-orange-600" />
                        <div>
                          <h3 className="font-medium">MySQL</h3>
                          <p className="text-sm text-gray-500">Fast, reliable, widely used</p>
                        </div>
                      </div>
                    </button>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button type="submit">
                    Continue
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Database Connection */}
        {step === 2 && (
          <Card>
            <CardHeader>
              <CardTitle>Database Connection</CardTitle>
              <CardDescription>
                Configure your {projectData.database_type} database connection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateProject} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="host">Host *</Label>
                    <Input
                      id="host"
                      placeholder="localhost"
                      value={connectionData.host}
                      onChange={(e) => setConnectionData(prev => ({
                        ...prev,
                        host: e.target.value
                      }))}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="port">Port *</Label>
                    <Input
                      id="port"
                      placeholder={getDefaultPort(projectData.database_type)}
                      value={connectionData.port}
                      onChange={(e) => setConnectionData(prev => ({
                        ...prev,
                        port: e.target.value
                      }))}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="database">Database Name *</Label>
                  <Input
                    id="database"
                    placeholder="my_database"
                    value={connectionData.database}
                    onChange={(e) => setConnectionData(prev => ({
                      ...prev,
                      database: e.target.value
                    }))}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username *</Label>
                    <Input
                      id="username"
                      placeholder="username"
                      value={connectionData.username}
                      onChange={(e) => setConnectionData(prev => ({
                        ...prev,
                        username: e.target.value
                      }))}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password">Password *</Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="password"
                      value={connectionData.password}
                      onChange={(e) => setConnectionData(prev => ({
                        ...prev,
                        password: e.target.value
                      }))}
                      required
                    />
                  </div>
                </div>

                {/* Test Connection */}
                <div className="space-y-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={testConnection}
                    disabled={connectionStatus === 'testing'}
                    className="w-full"
                  >
                    {connectionStatus === 'testing' ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Testing Connection...
                      </>
                    ) : (
                      <>
                        <Database className="mr-2 h-4 w-4" />
                        Test Connection
                      </>
                    )}
                  </Button>

                  {connectionStatus === 'success' && (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription className="text-green-800">
                        Connection successful! You can now create the project.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>

                <div className="flex justify-between">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setStep(1)}
                  >
                    Back
                  </Button>
                  <Button
                    type="submit"
                    disabled={isLoading || connectionStatus !== 'success'}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Creating Project...
                      </>
                    ) : (
                      'Create Project'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}