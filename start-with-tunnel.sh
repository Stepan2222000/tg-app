#!/bin/bash

# Avito Tasker - Production Startup with Local Tunnel
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

# Check if a tunnel command is available (localtunnel via global install or npx)
LT_COMMAND=()
if command -v localtunnel &> /dev/null; then
    LT_COMMAND=(localtunnel)
elif command -v npx &> /dev/null; then
    LT_COMMAND=(npx localtunnel)
fi

if [ ${#LT_COMMAND[@]} -eq 0 ]; then
    echo -e "${RED}Error: Localtunnel is not available${NC}"
    echo ""
    echo "Install it globally or ensure npx is available:"
    echo "  npm install -g localtunnel"
    exit 1
fi

echo -e "${BLUE}Using ${LT_COMMAND[*]} for tunnel${NC}"

# Step 1: Start production
echo -e "${YELLOW}[1/2] Starting production containers...${NC}"
./start-production.sh

echo ""
echo -e "${GREEN}✓ Production containers started${NC}"
echo ""

# Wait a bit for services to stabilize
sleep 3

# Step 2: Start tunnel
echo ""
echo -e "${YELLOW}[2/2] Starting tunnel on port 80...${NC}"
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
"${LT_COMMAND[@]}" --port 80
