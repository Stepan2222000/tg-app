#!/bin/bash

# Avito Tasker - Production Startup Script
# This script stops dev processes and starts production Docker containers

set -e  # Exit on error

echo "========================================"
echo "  Avito Tasker - Production Startup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Run this script from the project root directory"
    exit 1
fi

# Stop development processes
echo -e "${YELLOW}[1/5] Stopping development processes...${NC}"
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ Dev processes stopped${NC}"
echo ""

# Stop old Docker containers
echo -e "${YELLOW}[2/5] Stopping old Docker containers...${NC}"
docker compose down 2>/dev/null || true
echo -e "${GREEN}✓ Old containers stopped${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Using default values from docker-compose.yml"
    echo ""
fi

# Build and start containers
echo -e "${YELLOW}[3/5] Building and starting Docker containers...${NC}"
echo "This may take a few minutes on first run..."
echo ""
docker compose up --build -d

echo ""
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Wait for services to be ready
echo -e "${YELLOW}[4/5] Waiting for services to start...${NC}"
sleep 5

# Check container status
echo -e "${YELLOW}[5/5] Checking container status...${NC}"
docker compose ps
echo ""

# Test backend health
echo -e "${YELLOW}Testing backend health...${NC}"
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}⚠ Backend health check failed${NC}"
    echo "Check logs with: docker compose logs backend"
fi
echo ""

# Test frontend
echo -e "${YELLOW}Testing frontend...${NC}"
if curl -f -s http://localhost/ > /dev/null; then
    echo -e "${GREEN}✓ Frontend is serving${NC}"
else
    echo -e "${RED}⚠ Frontend not responding${NC}"
    echo "Check logs with: docker compose logs frontend"
fi
echo ""

# Success message
echo "========================================"
echo -e "${GREEN}  Production Started Successfully!${NC}"
echo "========================================"
echo ""
echo "📱 Application: http://localhost"
echo "🔧 Backend API: http://localhost/api/"
echo "📊 Backend direct: http://localhost:8000"
echo ""
echo "📝 View logs:        docker compose logs -f"
echo "🛑 Stop containers:  ./stop-production.sh"
echo "   or:               docker compose down"
echo ""
echo -e "${YELLOW}⚠ NOTE: To use with Telegram, you need a public URL${NC}"
echo "   Run: ./start-with-tunnel.sh (includes ngrok)"
echo ""
