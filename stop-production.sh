#!/bin/bash

# Avito Tasker - Production Stop Script
# This script stops all Docker containers

set -e  # Exit on error

echo "========================================"
echo "  Avito Tasker - Stopping Production"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Run this script from the project root directory"
    exit 1
fi

# Stop containers
echo -e "${YELLOW}Stopping Docker containers...${NC}"
docker compose down

echo ""
echo -e "${GREEN}✓ All containers stopped${NC}"
echo ""

# Optional: Remove volumes (commented out by default)
# Uncomment to also remove data volumes
# echo -e "${YELLOW}Removing volumes...${NC}"
# docker compose down -v
# echo -e "${GREEN}✓ Volumes removed${NC}"

# Optional: Clean up images (commented out by default)
# Uncomment to also remove Docker images
# echo -e "${YELLOW}Removing images...${NC}"
# docker compose down --rmi all
# echo -e "${GREEN}✓ Images removed${NC}"

echo "========================================"
echo -e "${GREEN}  Production Stopped${NC}"
echo "========================================"
echo ""
echo "To start again: ./start-production.sh"
echo ""
