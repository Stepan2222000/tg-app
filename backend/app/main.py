# backend/app/main.py
"""
FastAPI application initialization.
Sets up the API server with CORS, middleware, and routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
import aiofiles.os

from app.db.database import db
from app.api import auth, config, tasks, screenshots, withdrawals, referrals

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv('ENVIRONMENT') == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up Avito Tasker API...")
    await db.connect()
    logger.info("✅ Database pool initialized")

    yield

    # Shutdown
    logger.info("Shutting down Avito Tasker API...")
    await db.disconnect()
    logger.info("⏹️  Database pool closed")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Avito Tasker API",
    description="Backend for Telegram Mini App task completion platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - environment-based configuration
# CRITICAL-5 FIX: NEVER use wildcard, even in dev (CSRF vulnerability)
if os.getenv('ENVIRONMENT') == 'development':
    allowed_origins = [
        "http://localhost:5173",      # Vite dev server
        "http://127.0.0.1:5173"
    ]
    # Regex for development tunnels (localtunnel, Cloudflare)
    allow_origin_regex = r"https://.*\.(loca\.lt|trycloudflare\.com)"
else:
    # In production, only allow Telegram's WebApp origin
    # Telegram Mini Apps run on https://web.telegram.org
    allowed_origins = [
        "https://web.telegram.org",
        os.getenv('FRONTEND_URL', 'https://web.telegram.org')
    ]
    allow_origin_regex = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Auto-return expired tasks middleware
# OPTIMIZED: Only runs on task-related endpoints to reduce DB load
@app.middleware("http")
async def auto_return_expired_tasks_middleware(request: Request, call_next):
    """
    Middleware to automatically return expired tasks to the pool.

    PERFORMANCE OPTIMIZATION: Only runs on /api/tasks/* endpoints to avoid
    unnecessary DB queries on every request (health checks, static files, etc.)

    Uses SELECT FOR UPDATE SKIP LOCKED to prevent race conditions between
    concurrent requests trying to process the same expired assignments.

    Checks for task_assignments where status='assigned' AND deadline < NOW().
    For each expired assignment:
    1. Locks and fetches expired assignments with screenshots in single query (prevents N+1)
    2. Updates task (is_available=TRUE) and deletes assignment in transaction
    3. Deletes screenshot files from disk

    Does NOT block requests on errors - logs and continues.
    """
    # Only run cleanup on task-related endpoints
    if request.url.path.startswith("/api/tasks"):
        try:
            # Use transaction with FOR UPDATE SKIP LOCKED to prevent race conditions
            # Multiple concurrent requests will process different assignments
            async with db.transaction() as conn:
                # Step 1: Get expired assignment IDs with locking (no GROUP BY)
                # LIMIT 50 to avoid processing too many at once
                expired_assignments = await conn.fetch(
                    """
                    SELECT id as assignment_id, task_id, user_id
                    FROM task_assignments
                    WHERE status = 'assigned' AND deadline < NOW()
                    ORDER BY deadline ASC
                    LIMIT 50
                    FOR UPDATE SKIP LOCKED
                    """
                )

                expired_data = []
                files_to_delete = []  # CRITICAL-1 FIX: Collect files for cleanup outside transaction

                if expired_assignments:
                    # Step 2: Get screenshots for these assignments (no lock needed)
                    assignment_ids = [row['assignment_id'] for row in expired_assignments]
                    screenshots_data = await conn.fetch(
                        """
                        SELECT assignment_id, file_path
                        FROM screenshots
                        WHERE assignment_id = ANY($1)
                        ORDER BY uploaded_at ASC
                        """,
                        assignment_ids
                    )

                    # Group screenshots by assignment_id
                    screenshot_map = {}
                    for row in screenshots_data:
                        aid = row['assignment_id']
                        if aid not in screenshot_map:
                            screenshot_map[aid] = []
                        screenshot_map[aid].append(row['file_path'])

                    # Reconstruct expired_data with screenshots
                    for assignment in expired_assignments:
                        aid = assignment['assignment_id']
                        expired_data.append({
                            'assignment_id': aid,
                            'task_id': assignment['task_id'],
                            'user_id': assignment['user_id'],
                            'screenshot_paths': screenshot_map.get(aid, [])
                        })

                if expired_data:
                    logger.info(f"Found {len(expired_data)} expired task assignments to auto-return")

                    for row in expired_data:
                        try:
                            assignment_id = row['assignment_id']
                            task_id = row['task_id']
                            user_id = row['user_id']
                            screenshot_paths = row['screenshot_paths']

                            # Return task to pool and delete assignment within transaction
                            await conn.execute(
                                "UPDATE tasks SET is_available = TRUE, updated_at = NOW() WHERE id = $1",
                                task_id
                            )
                            await conn.execute(
                                "DELETE FROM task_assignments WHERE id = $1",
                                assignment_id
                            )

                            logger.info(f"Auto-returned task {task_id} from user {user_id} (assignment {assignment_id})")

                            # CRITICAL-1 FIX: Collect file paths during transaction
                            if screenshot_paths and isinstance(screenshot_paths, list):
                                files_to_delete.extend(screenshot_paths)

                        except Exception as e:
                            logger.error(f"Failed to auto-return assignment {row.get('assignment_id', 'unknown')}: {e}")
                            continue

            # Transaction committed - now safe to delete files
            # CRITICAL-1 FIX: Delete files after transaction with proper error handling
            for file_path_str in files_to_delete:
                try:
                    file_path = Path(file_path_str)
                    if file_path.exists():
                        await aiofiles.os.remove(str(file_path))
                        logger.debug(f"Deleted expired screenshot file: {file_path}")
                except Exception as file_error:
                    logger.warning(f"Failed to delete screenshot file {file_path_str}: {file_error}")

        except Exception as e:
            logger.error(f"Auto-return middleware error: {e}")
            # Don't block the request even if middleware fails

    # Continue with request processing
    response = await call_next(request)
    return response


# Create uploads directory if not exists
upload_dir = Path(os.getenv('UPLOAD_DIR', './uploads/screenshots'))
upload_dir.mkdir(parents=True, exist_ok=True)

# Mount static files for screenshots (after uploads directory is created)
if upload_dir.exists():
    app.mount("/static/screenshots", StaticFiles(directory=str(upload_dir)), name="screenshots")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(screenshots.router, prefix="/api/screenshots", tags=["screenshots"])
app.include_router(withdrawals.router, prefix="/api/withdrawals", tags=["withdrawals"])
app.include_router(referrals.router, prefix="/api/referrals", tags=["referrals"])


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "avito-tasker-api",
        "version": "1.0.0"
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API info."""
    return {
        "message": "Avito Tasker API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv('ENVIRONMENT') == 'development'
    )
