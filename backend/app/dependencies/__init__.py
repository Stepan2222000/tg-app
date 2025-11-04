# backend/app/dependencies/__init__.py
"""
FastAPI dependencies for authentication and authorization.
"""

from app.dependencies.auth import get_current_user

__all__ = ['get_current_user']
