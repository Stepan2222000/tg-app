#!/bin/bash

# Avito Tasker - Production Startup Script
# This script fully cleans up old processes and starts production with Cloudflare Tunnel

set -e  # Exit on error

echo "========================================"
echo "  Avito Tasker - Production Startup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

echo -e "${BLUE}Starting production with Cloudflare Tunnel...${NC}"
echo ""

# Execute start-with-cloudflare.sh which does full cleanup and startup
exec ./start-with-cloudflare.sh
