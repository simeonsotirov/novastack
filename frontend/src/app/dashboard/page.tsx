'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { 
  Database, 
  Plus, 
  Activity, 
  Users, 
  Zap,
  ArrowUpRight,
  Calendar,
  Clock
} from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description: string;
  database_type: 'postgresql' | 'mysql';
  status: 'active' | 'inactive';
  created_at: string;
  api_calls_today: number;
}

interface DashboardStats {
  total_projects: number;
  active_apis: number;
  total_api_calls: number;
  api_calls_today: number;
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    total_projects: 0,
    active_apis: 0,
    total_api_calls: 0,
    api_calls_today: 0
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const { apiClient } = await import('@/lib/api');
        
        // Fetch projects
        const projectsResponse = await apiClient.getProjects();
        if (projectsResponse.status === 200 && projectsResponse.data) {
          setProjects(projectsResponse.data);
          
          // Calculate stats from projects
          setStats({
            total_projects: projectsResponse.data.length,
            active_apis: projectsResponse.data.length * 2, // REST + GraphQL per project
            total_api_calls: 45678, // Mock for now
            api_calls_today: 234 // Mock for now
          });
        } else {
          // Use mock data if API fails
          setStats({
            total_projects: 5,
            active_apis: 12,
            total_api_calls: 45678,
            api_calls_today: 234
          });

          setProjects([
            {
              id: '1',
              name: 'E-commerce API',
              description: 'Product catalog and order management',
              database_type: 'postgresql',
              status: 'active',
              created_at: '2024-01-15',
              api_calls_today: 127
            },
            {
              id: '2',
              name: 'User Management',
              description: 'Authentication and user profiles',
              database_type: 'mysql',
              status: 'active',
              created_at: '2024-01-10',
              api_calls_today: 89
            },
            {
              id: '3',
              name: 'Analytics Dashboard',
              description: 'Business metrics and reporting',
              database_type: 'postgresql',
              status: 'inactive',
              created_at: '2024-01-08',
              api_calls_today: 0
            }
          ]);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        // Use mock data as fallback
        setStats({
          total_projects: 5,
          active_apis: 12,
          total_api_calls: 45678,
          api_calls_today: 234
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Welcome Section */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Welcome back!</h2>
          <p className="text-gray-600">Here's what's happening with your APIs today.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Projects</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_projects}</div>
              <p className="text-xs text-muted-foreground">
                +2 from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active APIs</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_apis}</div>
              <p className="text-xs text-muted-foreground">
                +4 from last week
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">API Calls Today</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.api_calls_today.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                +12% from yesterday
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total API Calls</CardTitle>
              <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_api_calls.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                +20% from last month
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Projects */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Recent Projects</h3>
            <Link href="/dashboard/projects">
              <Button variant="outline" size="sm">
                View All
                <ArrowUpRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Card key={project.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{project.name}</CardTitle>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      project.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {project.status}
                    </div>
                  </div>
                  <CardDescription>{project.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">Database:</span>
                      <span className="font-medium capitalize">
                        {project.database_type}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500">API Calls Today:</span>
                      <span className="font-medium">
                        {project.api_calls_today.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-500 flex items-center">
                        <Calendar className="mr-1 h-3 w-3" />
                        Created:
                      </span>
                      <span className="font-medium">
                        {formatDate(project.created_at)}
                      </span>
                    </div>
                  </div>
                  <div className="mt-4 flex space-x-2">
                    <Link href={`/dashboard/projects/${project.id}`}>
                      <Button variant="outline" size="sm" className="flex-1">
                        View Details
                      </Button>
                    </Link>
                    <Link href={`/dashboard/projects/${project.id}/apis`}>
                      <Button size="sm" className="flex-1">
                        Manage APIs
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {projects.length === 0 && (
            <Card>
              <CardContent className="text-center py-12">
                <Database className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
                <p className="text-gray-600 mb-6">
                  Get started by creating your first database project
                </p>
                <Link href="/dashboard/projects/new">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Project
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <Plus className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-lg">Create New Project</CardTitle>
                </div>
                <CardDescription>
                  Start a new database project and generate APIs
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-green-600" />
                  <CardTitle className="text-lg">View Analytics</CardTitle>
                </div>
                <CardDescription>
                  Monitor your API performance and usage
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-purple-600" />
                  <CardTitle className="text-lg">Manage Team</CardTitle>
                </div>
                <CardDescription>
                  Invite team members and manage permissions
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}