#!/bin/bash

echo "========================================"
echo "  Avito Tasker - Bot Startup"
echo "========================================"
echo ""

# Check if backend directory exists
if [ ! -d "backend" ]; then
  echo "❌ Error: backend directory not found"
  exit 1
fi

cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
  echo "❌ Error: backend/.env not found"
  echo "Please create backend/.env with TELEGRAM_BOT_TOKEN and MINI_APP_URL"
  exit 1
fi

# Load .env
source .env

# Check required variables
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
  echo "❌ Error: TELEGRAM_BOT_TOKEN not set in .env"
  exit 1
fi

if [ -z "$MINI_APP_URL" ]; then
  echo "❌ Error: MINI_APP_URL not set in .env"
  exit 1
fi

echo "✅ Environment configured:"
echo "   Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
echo "   Mini App URL: $MINI_APP_URL"
echo ""

# Start bot
echo "🤖 Starting Telegram Bot..."
echo "Press Ctrl+C to stop"
echo ""

python3 bot.py
