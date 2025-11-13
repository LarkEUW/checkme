# CheckMe - Browser Extension Security Analyzer

A comprehensive security analysis platform for browser extensions, designed for SOC and cybersecurity analysts to audit Chrome, Edge, and Firefox extensions.

## 🎯 Purpose

CheckMe analyzes browser extensions through static analysis, threat intelligence, and AI reasoning to generate detailed security reports with trust scores (0-50 scale, where 0 = safe, 50 = critical).

## 🏗️ Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React + Vite
- **Database**: PostgreSQL
- **Containerization**: Docker + Docker Compose
- **Authentication**: JWT (2 roles: admin/user)
- **AI**: Optional (Gemini Flash 1.5 / OpenAI)
- **Threat Intelligence**: VirusTotal, NVD, PhishTank, AbuseIPDB

## 🚀 Quick Start

```bash
# Clone and start the platform
git clone <repository-url>
cd checkme-platform
docker-compose up -d

# Access the application
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

## 📊 Analysis Workflow

1. **Input**: Extension URL, .crx/.xpi file, or combined mode
2. **Extraction**: Parse manifest and metadata
3. **Analysis**: Run parallel security modules
4. **Scoring**: Compute weighted risk score (0-50)
5. **Report**: Generate detailed JSON + PDF report
6. **Decision**: Accept/Reject/Pending status

## 🔍 Security Modules

- **Metadata Analysis**: Store data, developer info, update frequency
- **Permission Analysis**: Risk assessment of requested permissions
- **Code Behavior**: Pattern matching for malicious behaviors
- **Network/Privacy**: Data flow analysis and GDPR compliance
- **Threat Intelligence**: VirusTotal, phishing databases
- **CVE Analysis**: Known vulnerabilities in dependencies
- **AI Analysis**: Contextual risk explanation (optional)

## 📈 Scoring Model

| Range | Status | Action |
|-------|--------|--------|
| 0-10 | Safe | Accept |
| 11-25 | Needs Review | Manual Review |
| 26-40 | High Risk | Restricted Use |
| 41-50 | Block/Malicious | Block |

## 🔐 Security Features

- JWT-based authentication with role-based access
- Input validation and sanitization
- Rate limiting and request throttling
- Secure file upload handling
- Encrypted data storage
- Audit logging

## 🛠️ Development

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Database Schema](docs/DATABASE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)

## 🤝 Contributing

Please read our contributing guidelines before submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.