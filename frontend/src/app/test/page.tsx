export default function SimplePage() {
  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>NovaStack Frontend Test</h1>
      <p>This is a simple test page to verify the Next.js setup is working.</p>
      <div style={{ marginTop: '2rem' }}>
        <h2>Frontend Features:</h2>
        <ul>
          <li>✅ Landing Page</li>
          <li>✅ Authentication System</li>
          <li>✅ Dashboard Layout</li>
          <li>✅ Project Management</li>
          <li>✅ Responsive Design</li>
        </ul>
      </div>
      <div style={{ marginTop: '2rem' }}>
        <a href="/dashboard" style={{ color: 'blue', textDecoration: 'underline' }}>
          Go to Dashboard (may not work due to font issues)
        </a>
      </div>
    </div>
  );
}