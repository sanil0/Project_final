#!/bin/bash
# Quick deployment script for DDoS Protection Proxy
# Usage: ./deploy.sh [start|stop|restart|status|logs|build]

set -e

COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
show_banner() {
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║    DDoS Protection Proxy - Deployment Tool            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}❌ $ENV_FILE not found${NC}"
        echo -e "${YELLOW}Creating from .env.production template...${NC}"
        cp .env.production "$ENV_FILE"
        echo -e "${YELLOW}Please edit $ENV_FILE with your settings${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites met${NC}"
    echo ""
}

create_directories() {
    echo -e "${YELLOW}Creating required directories...${NC}"
    mkdir -p logs certs models grafana-dashboards
    chmod 755 logs
    echo -e "${GREEN}✅ Directories created${NC}"
    echo ""
}

build_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t ddos-protection:latest .
    echo -e "${GREEN}✅ Image built successfully${NC}"
    echo ""
}

start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    echo -e "${GREEN}✅ Services started${NC}"
    echo -e "${YELLOW}Waiting for services to be ready (30 seconds)...${NC}"
    sleep 30
    
    show_access_info
}

stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    docker-compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✅ Services stopped${NC}"
    echo ""
}

restart_services() {
    stop_services
    start_services
}

show_status() {
    echo -e "${YELLOW}Service Status:${NC}"
    echo ""
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    
    echo -e "${YELLOW}Health Checks:${NC}"
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Proxy is healthy${NC}"
    else
        echo -e "${RED}❌ Proxy health check failed${NC}"
    fi
    
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Prometheus is healthy${NC}"
    else
        echo -e "${RED}❌ Prometheus health check failed${NC}"
    fi
    
    echo ""
}

show_logs() {
    echo -e "${YELLOW}Showing logs (Ctrl+C to exit)...${NC}"
    docker-compose -f "$COMPOSE_FILE" logs -f
}

show_access_info() {
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║             Services are Ready to Use!                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Access Points:${NC}"
    echo -e "  ${GREEN}Dashboard:${NC}     http://localhost:8000/dashboard/login"
    echo -e "  ${GREEN}Prometheus:${NC}    http://localhost:9090"
    echo -e "  ${GREEN}Grafana:${NC}       http://localhost:3000"
    echo -e "  ${GREEN}Proxy API:${NC}     http://localhost:8080"
    echo ""
    
    echo -e "${YELLOW}Credentials:${NC}"
    DASHBOARD_USER=$(grep "^DASHBOARD_USER=" "$ENV_FILE" | cut -d'=' -f2)
    echo -e "  ${GREEN}Dashboard User:${NC}  $DASHBOARD_USER"
    echo -e "  ${GREEN}Grafana User:${NC}    admin / admin123"
    echo ""
    
    echo -e "${YELLOW}Quick Test:${NC}"
    echo -e "  Test proxy: ${GREEN}curl http://localhost:8080/${NC}"
    echo -e "  View logs:  ${GREEN}./deploy.sh logs${NC}"
    echo ""
}

# Main
show_banner

case "${1:-start}" in
    start)
        check_prerequisites
        create_directories
        build_image
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    build)
        build_image
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|build}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services (default)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status and health"
        echo "  logs     - Show live logs (Ctrl+C to exit)"
        echo "  build    - Build Docker image"
        exit 1
        ;;
esac
