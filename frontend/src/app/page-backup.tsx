export default function Home() {
  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #dbeafe 0%, #f3e8ff 100%)' }}>
      {/* Navigation */}
      <nav style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: 'rgba(255, 255, 255, 0.8)', backdropFilter: 'blur(4px)' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '4rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '2rem', height: '2rem', backgroundColor: '#2563eb', borderRadius: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '1.25rem' }}>
                🗄️
              </div>
              <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1f2937' }}>NovaStack</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <a href="/auth/login" style={{ color: '#6b7280', textDecoration: 'none', padding: '0.5rem 1rem', borderRadius: '0.375rem', transition: 'background-color 0.2s' }}>
                Login
              </a>
              <a href="/auth/register" style={{ backgroundColor: '#2563eb', color: 'white', textDecoration: 'none', padding: '0.5rem 1rem', borderRadius: '0.375rem', fontWeight: '500', transition: 'background-color 0.2s' }}>
                Get Started
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={{ padding: '5rem 1rem', textAlign: 'center' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          <h1 style={{ fontSize: 'clamp(2.5rem, 5vw, 3.75rem)', fontWeight: 'bold', color: '#1f2937', marginBottom: '1.5rem', lineHeight: '1.1' }}>
            The European
            <span style={{ background: 'linear-gradient(45deg, #2563eb, #7c3aed)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', display: 'inline-block', margin: '0 0.5rem' }}>
              Database-as-a-Service
            </span>
            Platform
          </h1>
          <p style={{ fontSize: '1.25rem', color: '#6b7280', marginBottom: '2rem', maxWidth: '48rem', margin: '0 auto 2rem auto' }}>
            Auto-generate REST & GraphQL APIs from your databases. 
            Built for European developers with GDPR compliance, multi-database support, and complete control.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="/auth/register" style={{ backgroundColor: '#2563eb', color: 'white', textDecoration: 'none', padding: '0.75rem 2rem', borderRadius: '0.375rem', fontWeight: '500', fontSize: '1.125rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', transition: 'background-color 0.2s' }}>
              🚀 Start Building
            </a>
            <a href="/docs" style={{ border: '1px solid #d1d5db', color: '#374151', textDecoration: 'none', padding: '0.75rem 2rem', borderRadius: '0.375rem', fontWeight: '500', fontSize: '1.125rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'white', transition: 'border-color 0.2s' }}>
              💻 View Documentation
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section style={{ padding: '5rem 1rem', backgroundColor: 'white' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
            <h2 style={{ fontSize: 'clamp(1.875rem, 4vw, 2.25rem)', fontWeight: 'bold', color: '#1f2937', marginBottom: '1rem' }}>
              Why Choose NovaStack?
            </h2>
            <p style={{ fontSize: '1.25rem', color: '#6b7280', maxWidth: '32rem', margin: '0 auto' }}>
              Built by Europeans, for Europeans. Get the power of Supabase with the control and compliance you need.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
            {[
              { icon: '⚡', title: 'Auto-Generated APIs', desc: 'Instant REST & GraphQL APIs from your database schemas. No manual coding required.' },
              { icon: '🗄️', title: 'Multi-Database Support', desc: 'PostgreSQL and MySQL support. Unlike Supabase, choose the database that fits your needs.' },
              { icon: '🛡️', title: 'GDPR Compliant', desc: 'Built with European data protection in mind. Your data stays in Europe, under European law.' },
              { icon: '🌍', title: 'Self-Hosted', desc: 'Complete control over your infrastructure. Deploy anywhere, own your data completely.' },
              { icon: '💻', title: 'Open Source', desc: 'Transparent, customizable, and community-driven. No vendor lock-in, ever.' },
              { icon: '🚀', title: 'Developer First', desc: 'Built by developers, for developers. Modern tooling, great DX, comprehensive docs.' }
            ].map((feature, index) => (
              <div key={index} style={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '0.5rem', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)', transition: 'box-shadow 0.2s' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>{feature.icon}</div>
                <h3 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937', marginBottom: '0.5rem' }}>{feature.title}</h3>
                <p style={{ color: '#6b7280', lineHeight: '1.6' }}>{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{ padding: '5rem 1rem', backgroundColor: '#1f2937', color: 'white' }}>
        <div style={{ maxWidth: '64rem', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: 'clamp(1.875rem, 4vw, 2.25rem)', fontWeight: 'bold', marginBottom: '1.5rem' }}>
            Ready to Build Something Amazing?
          </h2>
          <p style={{ fontSize: '1.25rem', color: '#d1d5db', marginBottom: '2rem' }}>
            Join the European developers who chose freedom, control, and compliance.
          </p>
          <a href="/auth/register" style={{ backgroundColor: '#f3f4f6', color: '#1f2937', textDecoration: 'none', padding: '0.75rem 2rem', borderRadius: '0.375rem', fontWeight: '500', fontSize: '1.125rem', display: 'inline-block', transition: 'background-color 0.2s' }}>
            Get Started Free
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ backgroundColor: 'white', borderTop: '1px solid #e5e7eb', padding: '3rem 1rem' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '1.5rem', height: '1.5rem', backgroundColor: '#2563eb', borderRadius: '0.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '1rem' }}>
                🗄️
              </div>
              <span style={{ fontSize: '1.125rem', fontWeight: '600', color: '#1f2937' }}>NovaStack</span>
            </div>
            <p style={{ color: '#6b7280' }}>
              © 2025 NovaStack. Built with ❤️ in Europe.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}