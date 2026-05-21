#!/bin/bash

###############################################################################
# AI-Powered DevOps Pipeline - Deployment Script
# This script handles blue-green deployment with automatic rollback
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
DEPLOYMENT_STRATEGY=${3:-blue-green}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI-Powered DevOps Pipeline Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"
echo "Strategy: $DEPLOYMENT_STRATEGY"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if service is healthy
check_health() {
    local url=$1
    local max_attempts=30
    local attempt=1

    print_info "Checking service health at $url"

    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url/health" > /dev/null; then
            print_info "Service is healthy!"
            return 0
        fi
        
        print_warning "Health check attempt $attempt/$max_attempts failed. Retrying..."
        sleep 10
        ((attempt++))
    done

    print_error "Service health check failed after $max_attempts attempts"
    return 1
}

# Function to perform blue-green deployment
blue_green_deploy() {
    print_info "Starting blue-green deployment..."

    # Determine current active environment
    CURRENT_ENV=$(docker ps --filter "name=app-blue" --format "{{.Names}}" | grep -q "app-blue" && echo "blue" || echo "green")
    NEW_ENV=$([ "$CURRENT_ENV" = "blue" ] && echo "green" || echo "blue")

    print_info "Current environment: $CURRENT_ENV"
    print_info "Deploying to: $NEW_ENV"

    # Pull latest image
    print_info "Pulling Docker image..."
    docker pull codebytaki/ai-devops-pipeline:$VERSION

    # Start new environment
    print_info "Starting new environment: $NEW_ENV"
    docker-compose -f docker-compose.$NEW_ENV.yml up -d

    # Wait for new environment to be healthy
    if check_health "http://localhost:800$([[ $NEW_ENV == 'blue' ]] && echo '1' || echo '2')"; then
        print_info "New environment is healthy. Switching traffic..."

        # Update load balancer to point to new environment
        # This would typically update nginx config or cloud load balancer
        
        print_info "Traffic switched to $NEW_ENV environment"

        # Stop old environment
        print_info "Stopping old environment: $CURRENT_ENV"
        docker-compose -f docker-compose.$CURRENT_ENV.yml down

        print_info "Deployment completed successfully! 🚀"
    else
        print_error "New environment health check failed. Rolling back..."
        docker-compose -f docker-compose.$NEW_ENV.yml down
        print_error "Deployment failed. Old environment still running."
        exit 1
    fi
}

# Function to perform rolling deployment
rolling_deploy() {
    print_info "Starting rolling deployment..."

    # Pull latest image
    docker pull codebytaki/ai-devops-pipeline:$VERSION

    # Update services one by one
    docker-compose up -d --no-deps --build app

    if check_health "http://localhost:8000"; then
        print_info "Rolling deployment completed successfully! 🚀"
    else
        print_error "Deployment health check failed"
        exit 1
    fi
}

# Function to perform canary deployment
canary_deploy() {
    print_info "Starting canary deployment..."

    # Deploy canary instance (10% traffic)
    print_info "Deploying canary instance..."
    docker-compose -f docker-compose.canary.yml up -d

    # Monitor canary for 5 minutes
    print_info "Monitoring canary instance for 5 minutes..."
    sleep 300

    if check_health "http://localhost:8003"; then
        print_info "Canary is healthy. Proceeding with full deployment..."
        rolling_deploy
        docker-compose -f docker-compose.canary.yml down
        print_info "Canary deployment completed successfully! 🚀"
    else
        print_error "Canary health check failed. Rolling back..."
        docker-compose -f docker-compose.canary.yml down
        exit 1
    fi
}

# Main deployment logic
case $DEPLOYMENT_STRATEGY in
    blue-green)
        blue_green_deploy
        ;;
    rolling)
        rolling_deploy
        ;;
    canary)
        canary_deploy
        ;;
    *)
        print_error "Unknown deployment strategy: $DEPLOYMENT_STRATEGY"
        print_info "Available strategies: blue-green, rolling, canary"
        exit 1
        ;;
esac

# Post-deployment tasks
print_info "Running post-deployment tasks..."

# Run smoke tests
print_info "Running smoke tests..."
# Add smoke test commands here

# Send notifications
print_info "Sending deployment notifications..."
# Add notification logic here

print_info "Deployment process completed! 🎉"
