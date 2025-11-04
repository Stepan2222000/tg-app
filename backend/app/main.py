# backend/app/main.py
"""
FastAPI application initialization.
Sets up the API server with CORS, middleware, and routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
