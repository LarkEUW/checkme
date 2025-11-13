#!/bin/bash

# CheckMe Deployment Script
# This script sets up and deploys the CheckMe security analysis platform

set -e

echo "🚀 CheckMe Security Analyzer Deployment"
echo "======================================"

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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check available memory
    MEMORY_GB=$(free -g | awk 'NR==2{printf "%.1f", $2}')
    if (( $(echo "$MEMORY_GB < 4" | bc -l) )); then
        print_warning "Less than 4GB RAM detected. The application may run slowly."
    else
        print_success "Memory requirement met (${MEMORY_GB}GB)"
    fi
    
    # Check disk space
    DISK_AVAIL=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$DISK_AVAIL" -lt 5 ]; then
        print_warning "Less than 5GB disk space available."
    else
        print_success "Disk space requirement met (${DISK_AVAIL}GB)"
    fi
}

# Setup environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    # Backend environment
    if [ ! -f backend/.env ]; then
        cp backend/.env.example backend/.env
        print_success "Created backend/.env file"
        print_warning "Please edit backend/.env with your configuration"
    else
        print_status "backend/.env already exists"
    fi
    
    # Frontend environment
    if [ ! -f frontend/.env ]; then
        cp frontend/.env.example frontend/.env
        print_success "Created frontend/.env file"
    else
        print_status "frontend/.env already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p backend/uploads
    mkdir -p logs
    
    print_success "Directories created"
}

# Set proper permissions
set_permissions() {
    print_status "Setting proper permissions..."
    
    # Make sure scripts are executable
    chmod +x deploy.sh
    chmod +x backend/*.sh 2>/dev/null || true
    
    # Set directory permissions
    chmod 755 backend/uploads
    chmod 755 logs
    
    print_success "Permissions set"
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Pull latest images
    docker-compose pull
    
    # Build and start services
    docker-compose up -d --build
    
    print_success "Services started"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for database
    print_status "Waiting for database..."
    for i in {1..30}; do
        if docker-compose exec postgres pg_isready -U checkme >/dev/null 2>&1; then
            print_success "Database is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for backend
    print_status "Waiting for backend..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
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
    
    docker-compose ps
    
    echo ""
    print_success "CheckMe is now running!"
    echo ""
    echo "Access the application at:"
    echo "  Frontend: http://localhost:3000"
    echo "  API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    echo "Default credentials:"
    echo "  Admin: admin@example.com / password"
    echo "  User: user@example.com / password"
    echo ""
    print_warning "Remember to change default passwords and secrets for production use!"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    docker-compose down
    print_success "Cleanup complete"
}

# Main execution
main() {
    echo "Starting CheckMe deployment..."
    
    # Check prerequisites
    check_docker
    check_requirements
    
    # Setup environment
    setup_environment
    create_directories
    set_permissions
    
    # Start services
    start_services
    wait_for_services
    
    # Show final status
    show_status
    
    print_success "Deployment completed successfully!"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main

# Remove trap and exit successfully
trap - EXIT
exit 0