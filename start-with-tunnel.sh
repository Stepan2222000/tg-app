#!/bin/bash

# Avito Tasker - Production Startup with Ngrok Tunnel
# This script starts production and creates a public URL for Telegram

set -e  # Exit on error

echo "========================================"
echo "  Avito Tasker - Production + Tunnel"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if ngrok is installed
NGROK_INSTALLED=false
if command -v ngrok &> /dev/null; then
    NGROK_INSTALLED=true
fi

# Check if localtunnel is available
LT_INSTALLED=false
if command -v npx &> /dev/null; then
    LT_INSTALLED=true
fi

if [ "$NGROK_INSTALLED" = false ] && [ "$LT_INSTALLED" = false ]; then
    echo -e "${RED}Error: Neither ngrok nor localtunnel is available${NC}"
    echo ""
    echo "Install one of them:"
    echo "  Ngrok:        brew install ngrok  (or download from ngrok.com)"
    echo "  Localtunnel:  npm install -g localtunnel"
    exit 1
fi

# Step 1: Start production
echo -e "${YELLOW}[1/3] Starting production containers...${NC}"
./start-production.sh

echo ""
echo -e "${GREEN}✓ Production containers started${NC}"
echo ""

# Wait a bit for services to stabilize
sleep 3

# Step 2: Choose tunnel service
TUNNEL_CMD=""
if [ "$NGROK_INSTALLED" = true ]; then
    TUNNEL_CMD="ngrok"
    echo -e "${BLUE}Using ngrok for tunnel${NC}"
elif [ "$LT_INSTALLED" = true ]; then
    TUNNEL_CMD="localtunnel"
    echo -e "${BLUE}Using localtunnel for tunnel${NC}"
fi

# Step 3: Start tunnel
echo ""
echo -e "${YELLOW}[2/3] Starting tunnel on port 80...${NC}"
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}                    TUNNEL STARTING${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo -e "Copy the public URL and update it in ${GREEN}@BotFather${NC}:"
echo "  1. Open @BotFather in Telegram"
echo "  2. Send: /setmenubutton"
echo "  3. Select your bot"
echo "  4. Paste the URL you see below"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop everything${NC}"
echo ""
echo -e "${BLUE}================================================================${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping tunnel and containers...${NC}"
    ./stop-production.sh
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start the tunnel
if [ "$TUNNEL_CMD" = "ngrok" ]; then
    ngrok http 80
elif [ "$TUNNEL_CMD" = "localtunnel" ]; then
    npx localtunnel --port 80
fi
