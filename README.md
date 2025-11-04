# NovaStack 🚀

**Open-source Database-as-a-Service platform built for European developers**

NovaStack provides instant PostgreSQL and MySQL databases with auto-generated APIs, real-time subscriptions, authentication, and file storage - all in one platform.

## ✨ Features

- 🗄️ **Multi-Database Support**: PostgreSQL & MySQL
- 🔌 **Auto-Generated APIs**: REST & GraphQL endpoints
- ⚡ **Real-time Subscriptions**: WebSocket-based live updates  
- 🔐 **Built-in Authentication**: JWT-based user management
- 📁 **File Storage**: S3-compatible object storage
- 🎯 **Developer Dashboard**: Web-based project management
- 🇪🇺 **EU-Hosted**: GDPR-compliant, European data centers
- 📖 **Open Source**: MIT licensed

## 🏗️ Architecture

```
NovaStack/
├── backend/          # FastAPI Python backend
├── frontend/         # Next.js dashboard
├── docker/          # Container configurations  
├── docs/            # Documentation
└── scripts/         # Utility scripts
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/novastack.git
cd novastack
```

2. **Start development environment**
```bash
docker-compose up -d
```

3. **Access the platform**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

## 📚 Documentation

- [Getting Started](./docs/getting-started.md)
- [API Reference](./docs/api-reference.md)
- [Deployment Guide](./docs/deployment.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./docs/contributing.md) for details.

## 📄 License

MIT License - see [LICENSE](./LICENSE) file for details.

## 🌟 Roadmap

- [x] Project setup and architecture
- [ ] FastAPI backend core
- [ ] Authentication system
- [ ] Database provisioning
- [ ] REST & GraphQL APIs
- [ ] Frontend dashboard
- [ ] File storage system
- [ ] Real-time features

---

Built with ❤️ for the developer community