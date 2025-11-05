'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { 
  Database, 
  Plus, 
  Search,
  Calendar,
  Activity,
  Settings,
  Trash2,
  Eye,
  Filter
} from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description: string;
  database_type: 'postgresql' | 'mysql';
  status: 'active' | 'inactive';
  created_at: string;
  updated_at: string;
  api_calls_today: number;
  total_api_calls: number;
  endpoints_count: number;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [filteredProjects, setFilteredProjects] = useState<Project[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // TODO: Replace with actual API call
    setTimeout(() => {
      const mockProjects: Project[] = [
        {
          id: '1',
          name: 'E-commerce API',
          description: 'Product catalog and order management system',
          database_type: 'postgresql',
          status: 'active',
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-20T14:30:00Z',
          api_calls_today: 127,
          total_api_calls: 5432,
          endpoints_count: 8
        },
        {
          id: '2',
          name: 'User Management',
          description: 'Authentication and user profiles',
          database_type: 'mysql',
          status: 'active',
          created_at: '2024-01-10T09:15:00Z',
          updated_at: '2024-01-19T16:45:00Z',
          api_calls_today: 89,
          total_api_calls: 3210,
          endpoints_count: 5
        },
        {
          id: '3',
          name: 'Analytics Dashboard',
          description: 'Business metrics and reporting',
          database_type: 'postgresql',
          status: 'inactive',
          created_at: '2024-01-08T11:30:00Z',
          updated_at: '2024-01-15T12:00:00Z',
          api_calls_today: 0,
          total_api_calls: 1567,
          endpoints_count: 12
        },
        {
          id: '4',
          name: 'Content Management',
          description: 'Blog posts and media management',
          database_type: 'mysql',
          status: 'active',
          created_at: '2024-01-05T08:45:00Z',
          updated_at: '2024-01-18T10:20:00Z',
          api_calls_today: 45,
          total_api_calls: 2890,
          endpoints_count: 6
        },
        {
          id: '5',
          name: 'Inventory System',
          description: 'Stock management and tracking',
          database_type: 'postgresql',
          status: 'active',
          created_at: '2024-01-03T14:20:00Z',
          updated_at: '2024-01-17T09:30:00Z',
          api_calls_today: 73,
          total_api_calls: 4123,
          endpoints_count: 10
        }
      ];
      
      setProjects(mockProjects);
      setFilteredProjects(mockProjects);
      setIsLoading(false);
    }, 1000);
  }, []);

  useEffect(() => {
    let filtered = projects;

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(project => 
        project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(project => project.status === statusFilter);
    }

    setFilteredProjects(filtered);
  }, [projects, searchQuery, statusFilter]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getDatabaseIcon = (type: 'postgresql' | 'mysql') => {
    return <Database className={`h-4 w-4 ${type === 'postgresql' ? 'text-blue-600' : 'text-orange-600'}`} />;
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
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Projects</h2>
            <p className="text-gray-600">Manage your database projects and APIs</p>
          </div>
          <Link href="/dashboard/projects/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Project
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as 'all' | 'active' | 'inactive')}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>

        {/* Projects Grid */}
        {filteredProjects.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredProjects.map((project) => (
              <Card key={project.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg flex items-center space-x-2">
                        {getDatabaseIcon(project.database_type)}
                        <span>{project.name}</span>
                      </CardTitle>
                      <CardDescription className="line-clamp-2">
                        {project.description}
                      </CardDescription>
                    </div>
                    <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                      {project.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Endpoints:</span>
                        <p className="font-medium">{project.endpoints_count}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Calls Today:</span>
                        <p className="font-medium">{project.api_calls_today.toLocaleString()}</p>
                      </div>
                    </div>

                    <div className="text-sm">
                      <span className="text-gray-500">Total API Calls:</span>
                      <p className="font-medium">{project.total_api_calls.toLocaleString()}</p>
                    </div>

                    {/* Dates */}
                    <div className="text-xs text-gray-500 space-y-1">
                      <div className="flex items-center justify-between">
                        <span>Created:</span>
                        <span>{formatDate(project.created_at)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Updated:</span>
                        <span>{formatDate(project.updated_at)}</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-2 pt-2">
                      <Link href={`/dashboard/projects/${project.id}`} className="flex-1">
                        <Button variant="outline" size="sm" className="w-full">
                          <Eye className="mr-1 h-3 w-3" />
                          View
                        </Button>
                      </Link>
                      <Link href={`/dashboard/projects/${project.id}/settings`}>
                        <Button variant="outline" size="sm">
                          <Settings className="h-3 w-3" />
                        </Button>
                      </Link>
                      <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700">
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <Database className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchQuery || statusFilter !== 'all' ? 'No projects found' : 'No projects yet'}
              </h3>
              <p className="text-gray-600 mb-6">
                {searchQuery || statusFilter !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Get started by creating your first database project'
                }
              </p>
              {!searchQuery && statusFilter === 'all' && (
                <Link href="/dashboard/projects/new">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Project
                  </Button>
                </Link>
              )}
            </CardContent>
          </Card>
        )}

        {/* Summary Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Database className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-sm text-gray-500">Total Projects</p>
                  <p className="text-lg font-semibold">{projects.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm text-gray-500">Active Projects</p>
                  <p className="text-lg font-semibold">
                    {projects.filter(p => p.status === 'active').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Calendar className="h-5 w-5 text-purple-600" />
                <div>
                  <p className="text-sm text-gray-500">Total API Calls</p>
                  <p className="text-lg font-semibold">
                    {projects.reduce((sum, p) => sum + p.total_api_calls, 0).toLocaleString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}