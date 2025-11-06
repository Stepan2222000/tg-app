# backend/app/api/screenshots.py
"""
Screenshot upload and deletion endpoints.
Handles multipart file uploads with validation and ownership checks.
"""

import logging
import aiofiles
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.dependencies.auth import get_current_user
from app.db.database import db
from app.utils.config import config
from app.utils.datetime import to_iso8601
from app.utils.filesystem import (
    build_static_url,
    cleanup_empty_dirs,
    ensure_subdirectory,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_screenshot(
    file: UploadFile = File(...),
    assignment_id: int = Form(...),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload screenshot for task assignment.

    Multipart form data:
        file: Image file (PNG or JPG, max 10MB)
        assignment_id: Task assignment ID

    Validation:
    - User owns the assignment
    - Assignment status is 'assigned' (not submitted/approved)
    - Screenshot count < 5 (allows re-upload after delete)
    - File type: image/jpeg or image/png
    - File size: <= MAX_FILE_SIZE (10MB)

    Returns:
        Screenshot object with id, file_path, url, uploaded_at

    Raises:
        400: Invalid state, file type, size, or count limit
        403: Not authorized
        404: Assignment not found
    """
    telegram_id = user["telegram_id"]

    # Get assignment with ownership check
    assignment = await db.fetch_one(
        "SELECT id, user_id, status FROM task_assignments WHERE id = $1",
        assignment_id
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task assignment not found"
        )

    # Check ownership
    if assignment['user_id'] != telegram_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task assignment"
        )

    # Check status (can only upload to 'assigned' tasks)
    if assignment['status'] != 'assigned':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload screenshots to task with status '{assignment['status']}'"
        )

    # Check screenshot count (max 5, but allow re-upload after delete)
    screenshot_count = await db.fetch_val(
        "SELECT COUNT(*) FROM screenshots WHERE assignment_id = $1",
        assignment_id
    )

    if screenshot_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 screenshots allowed per task"
        )

    # Validate content type
    allowed_content_types = ['image/jpeg', 'image/png', 'image/jpg']
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPG and PNG images are allowed."
        )

    # Read file and validate size
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {config.MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )

    # NEW-CRITICAL-6 FIX: Simplified and secure extension logic
    # Use whitelist mapping based on content type (don't trust user input at all)
    CONTENT_TYPE_TO_EXT = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',  # Some browsers send this
        'image/png': 'png'
    }

    extension = CONTENT_TYPE_TO_EXT.get(file.content_type)
    if not extension:
        # If content type not in whitelist, reject the upload
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type: {file.content_type}. Only JPEG and PNG images are allowed."
        )

    # Generate unique filename (UUID prevents path traversal and collisions)
    unique_filename = f"{uuid.uuid4()}.{extension}"

    # SECURITY: Construct and validate file path to prevent path traversal
    upload_dir = Path(config.UPLOAD_DIR).resolve()  # Resolve to absolute path
    assignment_dir = ensure_subdirectory(upload_dir, telegram_id, assignment_id)
    file_path = (assignment_dir / unique_filename).resolve()

    # Ensure file path is within upload directory (prevent path traversal attacks)
    if not str(file_path).startswith(str(upload_dir)):
        logger.error(f"Path traversal attempt detected: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )

    # Save file to disk
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        logger.debug(f"Saved screenshot file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file {file_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )

    # Insert into database
    try:
        screenshot = await db.fetch_one(
            """
            INSERT INTO screenshots (assignment_id, file_path)
            VALUES ($1, $2)
            RETURNING *
            """,
            assignment_id, str(file_path)
        )

        # Build response
        result = dict(screenshot)
        result['url'] = build_static_url(file_path, upload_dir)

        # Serialize datetime
        if result.get('uploaded_at'):
            result['uploaded_at'] = to_iso8601(result['uploaded_at'])

        logger.info(f"User {telegram_id} uploaded screenshot {screenshot['id']} for assignment {assignment_id}")
        return result

    except Exception as e:
        # If database insert fails, delete the file
        logger.error(f"Failed to insert screenshot record: {e}")
        try:
            await aiofiles.os.remove(str(file_path))
            logger.debug(f"Cleaned up file after DB error: {file_path}")
            try:
                file_path.relative_to(upload_dir)
                cleanup_empty_dirs(file_path.parent, upload_dir)
            except ValueError:
                pass
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup file after DB error: {cleanup_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save screenshot"
        )


@router.delete("/{screenshot_id}")
async def delete_screenshot(
    screenshot_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete screenshot with ownership check.

    Validation:
    - User owns the assignment
    - Assignment status is 'assigned' (cannot delete from submitted/approved tasks)

    Path parameters:
        screenshot_id: Screenshot ID

    Returns:
        Success message with screenshot_id

    Raises:
        400: Invalid status
        403: Not authorized
        404: Screenshot not found
    """
    telegram_id = user["telegram_id"]

    # Get screenshot with ownership check (JOIN to task_assignments)
    screenshot = await db.fetch_one(
        """
        SELECT s.id, s.assignment_id, s.file_path, ta.user_id, ta.status
        FROM screenshots s
        JOIN task_assignments ta ON ta.id = s.assignment_id
        WHERE s.id = $1
        """,
        screenshot_id
    )

    if not screenshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screenshot not found"
        )

    # Check ownership
    if screenshot['user_id'] != telegram_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this screenshot"
        )

    # Check status (can only delete from 'assigned' tasks)
    if screenshot['status'] != 'assigned':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete screenshots from task with status '{screenshot['status']}'"
        )

    # Delete from database
    try:
        await db.execute(
            "DELETE FROM screenshots WHERE id = $1",
            screenshot_id
        )
    except Exception as e:
        logger.error(f"Failed to delete screenshot {screenshot_id} from database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete screenshot"
        )

    # Delete file from disk (ignore if file doesn't exist)
    try:
        file_path = Path(screenshot['file_path'])
        if file_path.exists():
            await aiofiles.os.remove(str(file_path))
            logger.debug(f"Deleted screenshot file: {file_path}")
            base_dir = Path(config.UPLOAD_DIR).resolve()
            try:
                file_path.relative_to(base_dir)
                cleanup_empty_dirs(file_path.parent, base_dir)
            except ValueError:
                # Legacy path outside the structured uploads directory
                pass
        else:
            logger.warning(f"Screenshot file not found on disk: {file_path}")
    except Exception as file_error:
        logger.warning(f"Failed to delete screenshot file {file_path}: {file_error}")
        # Don't raise error - DB record is already deleted

    logger.info(f"User {telegram_id} deleted screenshot {screenshot_id} (assignment {screenshot['assignment_id']})")
    return {
        "message": "Screenshot deleted successfully",
        "screenshot_id": screenshot_id
    }
