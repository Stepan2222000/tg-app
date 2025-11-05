# Avito Tasker - Telegram Mini App

Telegram Mini App for completing tasks on Avito (message sending platform). Users can take tasks, submit screenshots, earn money, and invite referrals for commission.

## Features

- Task Management (simple & phone tasks)
- Screenshot submission
- Balance tracking (main + referral)
- Withdrawal system
- Referral program (50% commission)
- Automatic task expiration and return
- Telegram authentication
- Admin moderation via SQL

## Tech Stack

**Frontend:**
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Telegram Web Apps SDK
- React Router v6
- Axios

**Backend:**
- FastAPI (Python 3.11+)
- asyncpg (async PostgreSQL driver)
- Telegram initData validation
- Multipart file upload

**Database:**
- PostgreSQL 14+

**Deployment:**
- Docker + Docker Compose
- Nginx (reverse proxy + static files)

## Project Structure

```
tg-app/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── db/            # Database connection pool
│   │   ├── dependencies/  # FastAPI dependencies (auth)
│   │   └── utils/         # Helpers and validation
│   ├── uploads/
│   │   └── screenshots/   # Uploaded screenshots
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── schema.sql         # Database schema
│   ├── init_db.py         # DB initialization script
│   ├── add_test_tasks.py  # Test tasks script
│   ├── MODERATION.md      # Admin SQL scripts
│   └── .env               # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   ├── hooks/         # Custom hooks
│   │   ├── types/         # TypeScript types
│   │   └── utils/         # Helper functions
│   ├── Dockerfile
│   ├── nginx.conf         # Nginx configuration
│   └── .env               # Frontend environment variables
├── docs/                  # Documentation
├── design/                # UI/UX designs
├── docker-compose.yml     # Docker Compose configuration
└── README.md              # This file
```

## Prerequisites

### For Local Development

- **Node.js** 18+ and npm
- **Python** 3.11+
- **PostgreSQL** 14+
- **Git**

### For Docker Deployment

- **Docker** 20.10+
- **Docker Compose** 2.0+
- Server with public IP or domain
- HTTPS certificate (required for Telegram Mini Apps)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd tg-app
```

### 2. Database Setup

Connect to your PostgreSQL server and create the database:

```sql
CREATE DATABASE avito_tasker;
```

Then run the initialization script:

```bash
cd backend
python3 init_db.py
```

This will create all required tables from `schema.sql`.

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials (see Backend Environment Variables below)

# Add test tasks (optional)
python3 add_test_tasks.py

# Run backend server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
# Edit .env with your settings (see Frontend Environment Variables below)

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Backend Environment Variables

Create `backend/.env` with the following variables:

```env
# Database Configuration
DATABASE_HOST=81.30.105.134
DATABASE_PORT=5416
DATABASE_NAME=avito_tasker
DATABASE_USER=admin
DATABASE_PASSWORD=Password123

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8210464425:AAE67y14gEU_nvLfvDrIqpC7SMiyas9SsZk
TELEGRAM_BOT_USERNAME=avito_tasker_bot

# File Upload
UPLOAD_DIR=./uploads/screenshots
MAX_FILE_SIZE=10485760  # 10MB

# Task Pricing (in rubles)
SIMPLE_TASK_PRICE=50
PHONE_TASK_PRICE=150
REFERRAL_COMMISSION=0.5  # 50%
MIN_WITHDRAWAL=100

# Task Configuration
MAX_ACTIVE_TASKS=10
TASK_LOCK_HOURS=24

# Optional
GENERAL_INSTRUCTION=Следуйте инструкциям в задаче
ENVIRONMENT=development
```

## Frontend Environment Variables

Create `frontend/.env`:

**For Local Development:**
```env
VITE_API_URL=http://localhost:8000
VITE_BOT_USERNAME=avito_tasker_bot
VITE_SUPPORT_URL=https://t.me/support
VITE_USE_MOCK_DATA=false
```

**For Production (Docker):**
```env
VITE_API_URL=
VITE_BOT_USERNAME=avito_tasker_bot
VITE_SUPPORT_URL=https://t.me/support
VITE_USE_MOCK_DATA=false
```

**Note:** When `VITE_API_URL` is empty, frontend uses relative paths which work with nginx proxy.

## Docker Deployment

### 1. Prepare the Server

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo apt install docker-compose

# Clone repository to server
git clone <repository-url>
cd tg-app
```

### 2. Configure Environment Variables

Create `backend/.env` on the server with production values (see Backend Environment Variables above).

Update `TELEGRAM_BOT_TOKEN` and database credentials as needed.

### 3. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

**Services:**
- Frontend: `http://your-server-ip:80`
- Backend: `http://your-server-ip:8000`
- Health checks: `http://your-server-ip/health` and `http://your-server-ip:8000/health`

### 4. Initialize Database (First Time Only)

```bash
# Run from inside the backend container
docker exec -it avito_tasker_backend python3 init_db.py

# Add test tasks
docker exec -it avito_tasker_backend python3 add_test_tasks.py
```

### 5. Setup HTTPS (Required for Telegram)

Telegram Mini Apps require HTTPS. Use one of these options:

**Option A: Nginx Reverse Proxy with Let's Encrypt**

```bash
# Install Nginx and Certbot
sudo apt install nginx certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Configure Nginx to proxy to Docker containers
# Edit /etc/nginx/sites-available/avito-tasker
```

**Option B: Cloudflare Tunnel (Free HTTPS)**

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login and create tunnel
cloudflared tunnel login
cloudflared tunnel create avito-tasker
cloudflared tunnel route dns avito-tasker your-domain.com

# Run tunnel
cloudflared tunnel --url http://localhost:80 run avito-tasker
```

### 6. Configure Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/setmenubutton`
3. Select your bot `@avito_tasker_bot`
4. Set button text: `Открыть приложение`
5. Set Mini App URL: `https://your-domain.com`

## Admin Moderation

All moderation is done via SQL queries. See [backend/MODERATION.md](backend/MODERATION.md) for detailed instructions.

**Common operations:**
- View pending tasks
- Approve/reject tasks (with automatic referral commission)
- View pending withdrawals
- Approve/reject withdrawals
- View user information
- Statistics dashboard

**Connect to database:**

```bash
# Using psql
psql -h 81.30.105.134 -p 5416 -U admin -d avito_tasker

# Using Docker
docker exec -it postgres_container psql -U admin -d avito_tasker
```

## Testing

### Backend API Testing

Use the interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Testing

1. Run backend and frontend locally
2. Use Telegram Bot's test environment or create a temporary public URL:

```bash
# Option A: Localtunnel
npm install -g localtunnel
localtunnel --port 5173

# Option B: Cloudflare (requires Docker)
./start-with-cloudflare.sh

# Use the generated URL in BotFather's Mini App settings
```

### End-to-End Testing

1. Create test user accounts
2. Test referral chain:
   - User A generates referral link
   - User B registers via referral link
   - User B takes and completes task
   - Admin approves task
   - Verify User A receives 50% commission

## Common Issues

### Frontend can't connect to backend

**Problem:** CORS errors or network errors

**Solution:**
- Check VITE_API_URL in frontend/.env
- For local dev: Use `http://localhost:8000`
- For Docker: Use empty string (relies on nginx proxy)

### Telegram authentication fails

**Problem:** 401 Unauthorized errors

**Solution:**
- Verify TELEGRAM_BOT_TOKEN is correct
- Check that initData is being sent from Telegram WebApp
- Test in actual Telegram (not browser directly)

### Screenshots not displaying

**Problem:** 404 errors for screenshot URLs

**Solution:**
- Check UPLOAD_DIR exists: `backend/uploads/screenshots/`
- Verify nginx proxy passes `/static/screenshots/` to backend
- Check file permissions on uploads directory

### Database connection fails

**Problem:** Can't connect to PostgreSQL

**Solution:**
- Verify database credentials in .env
- Check PostgreSQL is running and accessible
- Test connection: `psql -h HOST -p PORT -U USER -d DATABASE`

### Docker build fails

**Problem:** Build errors

**Solution:**
- Ensure .env files exist in backend/ and frontend/
- Check Docker has enough disk space
- Try: `docker-compose build --no-cache`

## Project Architecture

### Authentication Flow

1. User opens Mini App in Telegram
2. Telegram WebApp SDK provides `initData` (signed string)
3. Frontend sends `initData` in Authorization header: `tma {initData}`
4. Backend validates signature using bot token secret key
5. Backend extracts `telegram_id`, `username`, `first_name`
6. User is registered automatically on first access via `/api/auth/init`

### Task Lifecycle

1. Admin adds task to database (manually via SQL)
2. Task is marked `is_available = TRUE`
3. User calls `/api/tasks/available?type=simple`
4. Backend returns random available task
5. User calls `/api/tasks/{task_id}/assign`
6. Task assignment created with 24h deadline
7. User uploads screenshots via `/api/screenshots/upload`
8. User submits task via `/api/tasks/{assignment_id}/submit`
9. Admin reviews and approves/rejects via SQL
10. If approved:
    - User's balance credited
    - Task returned to pool
    - If user has referrer, 50% commission credited to referrer
11. If rejected:
    - Task returned to pool
    - Screenshots can be deleted manually

### Auto-Return Mechanism

Middleware runs on every API request:
- Checks for expired assignments (`deadline < NOW()`)
- Returns tasks to pool (`is_available = TRUE`)
- Deletes assignment records
- Deletes screenshot files from disk

### Referral System

1. User A generates referral link: `/api/referrals/link`
2. Link format: `https://t.me/bot?start=ref_TELEGRAM_ID_A`
3. User B clicks link and opens Mini App
4. Telegram passes `start_param=ref_TELEGRAM_ID_A`
5. On first `/api/auth/init`, User B's `referred_by` set to User A's ID
6. When User B completes a task and admin approves:
   - User B gets task payment
   - User A gets 50% commission to `referral_balance`
   - Record created in `referral_earnings` table

## API Documentation

Full API documentation available at `/docs` when backend is running.

**Key endpoints:**

- `POST /api/auth/init` - Initialize/register user
- `GET /api/config` - Get app configuration
- `GET /api/user/me` - Get current user info
- `GET /api/tasks/available` - Get available task
- `POST /api/tasks/{id}/assign` - Assign task to user
- `POST /api/tasks/{id}/submit` - Submit completed task
- `POST /api/screenshots/upload` - Upload screenshot
- `POST /api/withdrawals` - Create withdrawal request
- `GET /api/referrals/link` - Get referral link
- `GET /api/referrals/stats` - Get referral statistics
- `GET /api/referrals/list` - Get detailed referral list

## Database Schema

See [backend/schema.sql](backend/schema.sql) for full schema.

**Tables:**
- `users` - User accounts and balances
- `tasks` - Available tasks
- `task_assignments` - Task assignments to users
- `screenshots` - Uploaded screenshot records
- `withdrawals` - Withdrawal requests
- `referral_earnings` - Commission tracking

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

This project is proprietary and confidential.

## Support

For support, contact: [VITE_SUPPORT_URL from .env]

---

**Version:** 1.0
**Last Updated:** 2025-11-04
**Author:** Claude + User
