import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, Zap, Shield, Globe, Code, Rocket } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <Database className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-gray-900">NovaStack</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/auth/login">
                <Button variant="ghost">Login</Button>
              </Link>
              <Link href="/auth/register">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            The European
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {" "}Database-as-a-Service{" "}
            </span>
            Platform
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Auto-generate REST & GraphQL APIs from your databases. 
            Built for European developers with GDPR compliance, multi-database support, and complete control.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/register">
              <Button size="lg" className="text-lg px-8 py-3">
                <Rocket className="mr-2 h-5 w-5" />
                Start Building
              </Button>
            </Link>
            <Link href="/docs">
              <Button variant="outline" size="lg" className="text-lg px-8 py-3">
                <Code className="mr-2 h-5 w-5" />
                View Documentation
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Choose NovaStack?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Built by Europeans, for Europeans. Get the power of Supabase with the control and compliance you need.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card>
              <CardHeader>
                <Zap className="h-12 w-12 text-blue-600 mb-4" />
                <CardTitle>Auto-Generated APIs</CardTitle>
                <CardDescription>
                  Instant REST & GraphQL APIs from your database schemas. No manual coding required.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Database className="h-12 w-12 text-green-600 mb-4" />
                <CardTitle>Multi-Database Support</CardTitle>
                <CardDescription>
                  PostgreSQL and MySQL support. Unlike Supabase, choose the database that fits your needs.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Shield className="h-12 w-12 text-purple-600 mb-4" />
                <CardTitle>GDPR Compliant</CardTitle>
                <CardDescription>
                  Built with European data protection in mind. Your data stays in Europe, under European law.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Globe className="h-12 w-12 text-orange-600 mb-4" />
                <CardTitle>Self-Hosted</CardTitle>
                <CardDescription>
                  Complete control over your infrastructure. Deploy anywhere, own your data completely.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Code className="h-12 w-12 text-red-600 mb-4" />
                <CardTitle>Open Source</CardTitle>
                <CardDescription>
                  Transparent, customizable, and community-driven. No vendor lock-in, ever.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Rocket className="h-12 w-12 text-indigo-600 mb-4" />
                <CardTitle>Developer First</CardTitle>
                <CardDescription>
                  Built by developers, for developers. Modern tooling, great DX, comprehensive docs.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to Build Something Amazing?
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Join the European developers who chose freedom, control, and compliance.
          </p>
          <Link href="/auth/register">
            <Button size="lg" variant="secondary" className="text-lg px-8 py-3">
              Get Started Free
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white border-t py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Database className="h-6 w-6 text-blue-600" />
              <span className="text-lg font-semibold text-gray-900">NovaStack</span>
            </div>
            <p className="text-gray-600">
              © 2025 NovaStack. Built with ❤️ in Europe.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
