# NovaStack Branch Structure

This document outlines the Git branching strategy for the NovaStack project.

## Branch Overview

### 🌟 Main Branches

- **`main`** - Production-ready code, stable releases only
- **`development`** - Integration branch for features, pre-production testing

### 🚀 Feature Branches

- **`feature/frontend-backend-integration`** ✅ **COMPLETED**
  - Complete full-stack application with authentication
  - Next.js 14 frontend with Tailwind CSS
  - FastAPI backend with mock authentication
  - JWT token management and API integration
  - **Status**: Ready for production merge

- **`feature/file-storage-system`** 🔄 **UPCOMING**
  - MinIO-based file storage implementation
  - Upload/download capabilities
  - Integration with API endpoints
  - File management UI components

- **`feature/realtime-features`** 🔄 **UPCOMING**
  - WebSocket-based realtime subscriptions
  - Live database change notifications
  - Real-time dashboard updates
  - Socket.IO integration

### 🔧 Support Branches

- **`hotfix/production-fixes`** 🛠️ **MAINTENANCE**
  - Critical bug fixes for production
  - Security patches
  - Performance optimizations

## Branching Workflow

### Development Process:
1. Create feature branch from `development`
2. Implement feature with tests
3. Create pull request to `development`
4. Code review and testing
5. Merge to `development`
6. Deploy to staging for integration testing
7. Merge `development` to `main` for production

### Branch Naming Convention:
- `feature/descriptive-feature-name`
- `hotfix/critical-issue-description`
- `bugfix/issue-description`
- `chore/maintenance-task`

## Current Status

### ✅ Completed Features (Phase 6):
- **Frontend Dashboard**: Complete React/Next.js application
- **Authentication System**: JWT-based auth with mock backend
- **API Integration**: REST and GraphQL endpoint generation
- **Project Management**: Full CRUD operations
- **Database Integration**: Schema introspection and API generation

### 🔄 In Progress:
- **Current Branch**: `feature/frontend-backend-integration` 
- **Next**: File Storage System (MinIO integration)
- **Future**: Realtime Features (WebSocket subscriptions)

### 🌍 Remote Repositories:
All branches are pushed to GitHub: `https://github.com/simeonsotirov/novastack`

## Pull Request Links:
- [Frontend-Backend Integration](https://github.com/simeonsotirov/novastack/pull/new/feature/frontend-backend-integration)
- [File Storage System](https://github.com/simeonsotirov/novastack/pull/new/feature/file-storage-system)
- [Realtime Features](https://github.com/simeonsotirov/novastack/pull/new/feature/realtime-features)

## Development Environment:
- **Frontend**: http://localhost:3000 (Next.js)
- **Backend**: http://127.0.0.1:8000 (FastAPI)
- **Auth**: Mock system (no database required)
- **Status**: ✅ Both servers running, authentication working

---
*Last updated: November 5, 2025*