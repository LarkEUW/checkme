#!/bin/bash

# CheckMe Production Deployment Script
# This script deploys CheckMe to a production environment

set -e

echo "🚀 CheckMe Production Deployment"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please don't run this script as root"
    exit 1
fi

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install Git first."
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Setup SSL certificates
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    mkdir -p ssl
    
    # Check if certificates exist
    if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
        print_warning "SSL certificates not found. Generating self-signed certificates..."
        
        # Generate self-signed certificate (for demo purposes)
        openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=cpgjw4w7owohq.ok.kimi.link"
        
        print_warning "Self-signed certificates generated. For production, use proper SSL certificates."
    else
        print_success "SSL certificates found"
    fi
    
    # Set proper permissions
    chmod 600 ssl/key.pem
    chmod 644 ssl/cert.pem
}

# Create production environment file
create_prod_env() {
    print_status "Creating production environment file..."
    
    if [ ! -f .env.prod ]; then
        cat > .env.prod << EOF
# Database Configuration
POSTGRES_DB=checkme_db
POSTGRES_USER=checkme
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Security (CHANGE THESE!)
SECRET_KEY=$(openssl rand -base64 32)

# API Configuration
VITE_API_URL=https://cpgjw4w7owohq.ok.kimi.link
CORS_ORIGINS=https://cpgjw4w7owohq.ok.kimi.link

# Optional API Keys (add your own)
# OPENAI_API_KEY=your-openai-api-key
# VIRUSTOTAL_API_KEY=your-virustotal-api-key
# ABUSEIPDB_API_KEY=your-abuseipdb-api-key

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=/app/uploads
EOF
        
        print_success "Production environment file created"
        print_warning "Please edit .env.prod with your actual API keys and configuration"
    else
        print_success "Production environment file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p uploads logs ssl
    
    # Set proper permissions
    chmod 755 uploads logs
    
    print_success "Directories created"
}

# Pull latest code
pull_latest_code() {
    print_status "Pulling latest code..."
    
    if [ -d .git ]; then
        git pull origin main
        print_success "Code updated"
    else
        print_warning "Not a git repository. Skipping code update."
    fi
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Load production environment
    if [ -f .env.prod ]; then
        export $(cat .env.prod | xargs)
    fi
    
    # Stop existing services
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
    
    # Pull latest images
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
    
    # Build and start services
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    
    print_success "Services started"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for database
    print_status "Waiting for database..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec postgres pg_isready -U ${POSTGRES_USER:-checkme} >/dev/null 2>&1; then
            print_success "Database is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for backend
    print_status "Waiting for backend..."
    for i in {1..30}; do
        if curl -f -k https://localhost:8000/health >/dev/null 2>&1; then
            print_success "Backend is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    echo ""
}

# Display service status
show_status() {
    print_status "Service Status:"
    echo "==============="
    
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
    
    echo ""
    print_success "CheckMe is now running in production!"
    echo ""
    echo "Access the application at:"
    echo "  https://cpgjw4w7owohq.ok.kimi.link"
    echo ""
    echo "API Documentation:"
    echo "  https://cpgjw4w7owohq.ok.kimi.link/docs"
    echo ""
    print_warning "Remember to:"
    echo "  1. Configure proper SSL certificates"
    echo "  2. Add your API keys to .env.prod"
    echo "  3. Set up monitoring and logging"
    echo "  4. Configure firewall rules"
    echo "  5. Set up automated backups"
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Create monitoring script
    cat > monitor.sh << 'EOF'
#!/bin/bash
# CheckMe Monitoring Script

# Check if services are running
if ! docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "ERROR: Some services are not running"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
    exit 1
fi

# Check disk space
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "WARNING: Disk usage is above 80%"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ "$MEMORY_USAGE" -gt 80 ]; then
    echo "WARNING: Memory usage is above 80%"
fi

# Check database connectivity
if ! docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec postgres pg_isready -U ${POSTGRES_USER:-checkme} >/dev/null 2>&1; then
    echo "ERROR: Database is not accessible"
    exit 1
fi

echo "All systems operational"
EOF
    
    chmod +x monitor.sh
    print_success "Monitoring script created"
}

# Setup log rotation
setup_log_rotation() {
    print_status "Setting up log rotation..."
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/checkme << EOF
${PWD}/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ${USER} ${USER}
}
EOF
    
    print_success "Log rotation configured"
}

# Main execution
main() {
    echo "Starting CheckMe production deployment..."
    
    # Run all setup steps
    check_prerequisites
    setup_ssl
    create_prod_env
    create_directories
    pull_latest_code
    start_services
    wait_for_services
    setup_monitoring
    setup_log_rotation
    
    # Display final status
    show_status
    
    print_success "Production deployment completed successfully!"
    
    # Show next steps
    echo ""
    echo "Next steps:"
    echo "1. Edit .env.prod with your API keys"
    echo "2. Configure proper SSL certificates"
    echo "3. Set up monitoring (./monitor.sh)"
    echo "4. Configure firewall rules"
    echo "5. Set up automated backups"
    echo ""
    echo "To stop the services: docker-compose -f docker-compose.yml -f docker-compose.prod.yml down"
    echo "To view logs: docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main

# Show completion time
echo ""
echo "Deployment completed at: $(date)"
exit 0