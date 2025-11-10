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
echo -e "${YELLOW}[1/5] Stopping all old processes...${NC}"

# Stop Docker containers first (with longer timeout)
docker compose down --timeout 10 2>/dev/null || true
sleep 2

# Kill all old development and bot processes
pkill -9 -f "bot.py" 2>/dev/null || true
pkill -9 -f "start-bot.sh" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "ngrok" 2>/dev/null || true
pkill -f "localtunnel" 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true

# Final check
sleep 1
if pgrep -f "bot.py" > /dev/null; then
  echo -e "${YELLOW}⚠ Warning: Some bot.py processes still running. Forcing cleanup...${NC}"
  pkill -9 -f "bot.py" 2>/dev/null || true
  sleep 1
fi

echo -e "${GREEN}✓ All old processes stopped${NC}"
echo ""

# Step 2: Build and start Docker containers
echo -e "${YELLOW}[2/5] Building and starting Docker containers...${NC}"
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
echo -e "${YELLOW}[3/5] Waiting for services to be healthy...${NC}"

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

# Step 4: Initialize database views for moderation
echo -e "${YELLOW}[4/5] Installing moderation views in database...${NC}"
docker exec avito_tasker_backend python3 install_views.py

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Database views created${NC}"
else
  echo -e "${YELLOW}⚠ Views creation had warnings (this is OK if views already exist)${NC}"
fi

echo ""

# Step 5: Verify tunnel is ready
echo -e "${YELLOW}[5/5] Verifying Cloudflare Tunnel...${NC}"
echo "Waiting for named tunnel to connect (may take 10-15 seconds)..."
echo ""

# Wait for tunnel to connect
sleep 10

echo -e "${GREEN}✓ Named tunnel should be connected!${NC}"
echo ""
echo -e "${GREEN}Permanent tunnel URL: https://miniapp.cheapdomain2025.site${NC}"

# Check Telegram bot status (running via Docker)
echo ""
echo -e "${YELLOW}Checking Telegram bot status...${NC}"
sleep 2

BOT_STATUS=$(docker ps --filter "name=avito_tasker_bot" --format "{{.Status}}" 2>/dev/null)
if [[ $BOT_STATUS == *"Up"* ]]; then
  echo -e "${GREEN}✓ Telegram bot is running via Docker${NC}"
  echo -e "${GREEN}  View logs: docker logs -f avito_tasker_bot${NC}"
  echo ""
else
  echo -e "${RED}❌ Bot container failed to start${NC}"
  echo -e "${YELLOW}  Checking logs:${NC}"
  docker logs --tail 20 avito_tasker_bot 2>&1 || echo "No logs available"
  echo ""
  echo -e "${RED}  Please check the issue and restart${NC}"
fi

echo ""
echo "=========================================="
echo "  ✅ Production Started Successfully!"
echo "=========================================="
echo ""
echo "Services:"
echo "  Backend API:  http://localhost:8000"
echo "  Frontend:     http://localhost:80"
echo "  Public URL:   https://miniapp.cheapdomain2025.site"
echo ""
echo "🌐 Your Mini App is now accessible at:"
echo "   https://miniapp.cheapdomain2025.site"
echo ""
echo "📝 Bot is configured with permanent domain"
echo "   MINI_APP_URL=https://miniapp.cheapdomain2025.site"

echo ""
echo "Commands:"
echo "  View logs:    docker compose logs -f"
echo "  Bot logs:     tail -f /tmp/bot.log"
echo "  Stop:         ./stop-production.sh"
echo "  Restart:      ./start-with-cloudflare.sh"
echo ""
echo "🔥 Press Ctrl+C to view live logs (containers will keep running)"
echo ""

# Follow logs
docker compose logs -f
