#!/bin/bash

echo "=========================================="
echo "  Avito Tasker - Production + Cloudflare"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Stop all old processes (full cleanup)
echo -e "${YELLOW}[1/4] Stopping all old processes...${NC}"
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "ngrok" 2>/dev/null || true
pkill -f "localtunnel" 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true
pkill -f "bot.py" 2>/dev/null || true
docker compose down 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓ All old processes stopped${NC}"
echo ""

# Step 2: Build and start Docker containers
echo -e "${YELLOW}[2/4] Building and starting Docker containers...${NC}"
echo "This may take a few minutes on first run..."
echo ""

docker compose up --build -d

if [ $? -ne 0 ]; then
  echo -e "${RED}❌ Failed to start Docker containers${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}✓ Docker containers started${NC}"
echo ""

# Step 3: Wait for services to be healthy
echo -e "${YELLOW}[3/4] Waiting for services to be healthy...${NC}"

# Wait for backend
for i in {1..30}; do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
    break
  fi
  if [ $i -eq 30 ]; then
    echo -e "${RED}❌ Backend health check timeout${NC}"
    docker compose logs backend
    exit 1
  fi
  sleep 1
done

# Wait for frontend
for i in {1..30}; do
  if curl -sf http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is healthy${NC}"
    break
  fi
  if [ $i -eq 30 ]; then
    echo -e "${RED}❌ Frontend health check timeout${NC}"
    docker compose logs frontend
    exit 1
  fi
  sleep 1
done

echo ""

# Step 4: Get Cloudflare Tunnel URL
echo -e "${YELLOW}[4/4] Getting public tunnel URL...${NC}"
echo "Waiting for Cloudflare Tunnel to start (may take 10-15 seconds)..."
echo ""

# Wait for tunnel to initialize and get URL from logs
TUNNEL_URL=""
for i in {1..20}; do
  # Try to get URL from docker logs
  TUNNEL_URL=$(docker compose logs tunnel 2>/dev/null | grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' | head -1)

  if [ ! -z "$TUNNEL_URL" ]; then
    echo -e "${GREEN}✓ Tunnel is ready!${NC}"
    break
  fi

  if [ $i -eq 20 ]; then
    echo -e "${YELLOW}⚠ Could not get tunnel URL from logs${NC}"
    echo "Check logs manually with: docker compose logs tunnel"
    break
  fi

  sleep 1
done

echo ""
echo "=========================================="
echo "  ✅ Production Started Successfully!"
echo "=========================================="
echo ""
echo "Services:"
echo "  Backend API:  http://localhost:8000"
echo "  Frontend:     http://localhost:80"

if [ ! -z "$TUNNEL_URL" ]; then
  echo "  Public URL:   $TUNNEL_URL"
  echo ""
  echo "🌐 Your Mini App is now accessible at:"
  echo "   $TUNNEL_URL"
  echo ""
  echo "📝 Update bot configuration:"
  echo "   1. Edit backend/.env"
  echo "   2. Set MINI_APP_URL=$TUNNEL_URL"
  echo "   3. Restart bot: pkill -f bot.py && ./start-bot.sh"
else
  echo ""
  echo "To get tunnel URL, run:"
  echo "  docker compose logs tunnel | grep trycloudflare"
fi

echo ""
echo "Commands:"
echo "  View logs:    docker compose logs -f"
echo "  Stop:         ./stop-production.sh"
echo "  Restart:      ./start-with-cloudflare.sh"
echo ""
echo "🔥 Press Ctrl+C to view live logs (containers will keep running)"
echo ""

# Follow logs
docker compose logs -f
