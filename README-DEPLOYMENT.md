# CheckMe Deployment Guide

## 🚀 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning)
- At least 4GB RAM available

### 1. Clone and Setup
```bash
git clone <repository-url>
cd checkme-platform
```

### 2. Environment Configuration
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit the environment files with your configuration
# backend/.env - Database, API keys, security settings
# frontend/.env - API URL, feature flags
```

### 3. Start the Platform
```bash
# Start all services
docker-compose up -d

# Or start with build (first time or after changes)
docker-compose up -d --build
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Default Credentials

### Demo Accounts
- **Admin**: admin@example.com / password
- **User**: user@example.com / password

### Database
- **Database**: checkme_db
- **User**: checkme
- **Password**: checkme_password (change in production!)

## 🔧 Configuration

### Backend Configuration (backend/.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://checkme:checkme_password@postgres:5432/checkme_db

# Security (CHANGE THESE!)
SECRET_KEY=your-very-secure-secret-key-here

# Optional API Keys
OPENAI_API_KEY=your-openai-api-key
VIRUSTOTAL_API_KEY=your-virustotal-api-key
```

### Frontend Configuration (frontend/.env)
```env
# API URL
VITE_API_URL=http://localhost:8000

# Feature Flags
VITE_ENABLE_AI_ANALYSIS=true
```

## 🏗️ Development Setup

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

## 📊 Database Management

### Initial Setup
```bash
# The database tables are created automatically on first startup
# Manual migration (if needed):
docker-compose exec backend alembic upgrade head
```

### Backup Database
```bash
# Create backup
docker-compose exec postgres pg_dump -U checkme checkme_db > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U checkme checkme_db < backup.sql
```

## 🔒 Security Considerations

### Production Deployment
1. **Change all default passwords and secrets**
2. **Use HTTPS with proper SSL certificates**
3. **Configure firewall rules**
4. **Set up monitoring and logging**
5. **Regular security updates**

### Environment Security
```env
# Production environment variables
SECRET_KEY=use-a-secure-random-string
POSTGRES_PASSWORD=secure-database-password
CORS_ORIGINS=https://yourdomain.com
```

## 🚀 Production Deployment

### Using Docker Compose (Production)
```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Using Kubernetes
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/
```

### Using AWS ECS/Fargate
```bash
# Use AWS ECS CLI
ecs-cli compose --project-name checkme up
```

## 📈 Monitoring

### Health Checks
- Backend: `GET http://localhost:8000/health`
- Database: Automatic in Docker Compose

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

## 🔧 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change ports in docker-compose.yml
   ports:
     - "8001:8000"  # Backend
     - "3001:3000"  # Frontend
   ```

2. **Database connection failed**
   ```bash
   # Check database health
   docker-compose ps
   docker-compose logs postgres
   ```

3. **Frontend build fails**
   ```bash
   # Clear node_modules and reinstall
   cd frontend
   rm -rf node_modules
   npm install
   ```

4. **Permission errors**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

## 🔄 Updates

### Updating the Platform
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Update database if needed
docker-compose exec backend alembic upgrade head
```

## 🗂️ Directory Structure

```
checkme-platform/
├── backend/           # FastAPI backend
│   ├── models.py      # Database models
│   ├── analysis_engine.py  # Analysis logic
│   ├── main.py        # FastAPI app
│   └── requirements.txt
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Page components
│   │   └── services/     # API services
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 📞 Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Review environment configuration
3. Check system requirements
4. Consult troubleshooting section

## 🎯 Next Steps

1. **Configure SSL certificates** for production
2. **Set up monitoring** (Prometheus/Grafana)
3. **Configure backup strategy**
4. **Set up CI/CD pipeline**
5. **Configure rate limiting and DDoS protection**

---

**Note**: This is a development/demo deployment. For production use, implement additional security measures, monitoring, and scaling considerations.