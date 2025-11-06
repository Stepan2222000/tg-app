# backend/app/api/tasks.py
"""
Task management endpoints.
Handles task lifecycle: available tasks, assignment, submission, and cancellation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles.os
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.dependencies.auth import get_current_user
from app.db.database import db
from app.utils.config import config
from app.utils.datetime import to_iso8601
from app.utils.validation import validate_phone_number

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/available")
async def get_available_task(
    type: str = Query(..., description="Task type: 'simple' or 'phone'"),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get one random available task by type.

    PROTECTED endpoint - requires valid Telegram initData in Authorization header.

    Query parameters:
        type: Task type ('simple' or 'phone')

    Returns:
        Task object with all fields

    Raises:
        400: Invalid task type
        404: No available tasks of this type
    """
    # Validate task type
    if type not in ['simple', 'phone']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task type. Must be 'simple' or 'phone'"
        )

    # Get random available task
    task = await db.fetch_one(
        """
        SELECT * FROM tasks
        WHERE is_available = TRUE AND type = $1
        ORDER BY RANDOM()
        LIMIT 1
        """,
        type
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No available tasks of type '{type}'"
        )

    # Serialize datetime fields
    task_response = dict(task)
    if task_response.get('created_at'):
        task_response['created_at'] = to_iso8601(task_response['created_at'])
    if task_response.get('updated_at'):
        task_response['updated_at'] = to_iso8601(task_response['updated_at'])

    logger.debug(f"Returned available task {task['id']} of type '{type}'")
    return task_response


@router.get("/active")
async def get_active_tasks(
    user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get list of user's active task assignments.

    Requires authentication.

    Returns:
        List of active task assignments with task details and screenshots
        Empty list if no active tasks

    Raises:
        401: Not authenticated
    """
    telegram_id = user["telegram_id"]

    # OPTIMIZED: Get active assignments with task details AND screenshots in ONE query
    # Using json_agg to aggregate screenshots, preventing N+1 query problem
    assignments = await db.fetch_all(
        """
        SELECT
            ta.id,
            ta.task_id,
            ta.status,
            ta.deadline,
            ta.phone_number,
            ta.assigned_at,
            ta.submitted_at,
            t.type,
            t.avito_url,
            t.message_text,
            t.price,
            COALESCE(
                json_agg(s.file_path ORDER BY s.uploaded_at ASC)
                FILTER (WHERE s.file_path IS NOT NULL),
                '[]'
            ) as screenshots
        FROM task_assignments ta
        JOIN tasks t ON t.id = ta.task_id
        LEFT JOIN screenshots s ON s.assignment_id = ta.id
        WHERE ta.user_id = $1 AND ta.status = 'assigned'
        GROUP BY ta.id, t.id
        ORDER BY ta.assigned_at DESC
        """,
        telegram_id
    )

    # Format response with deserialized screenshots array
    result = []
    for assignment in assignments:
        assignment_dict = dict(assignment)

        # Parse screenshots JSON (already comes as list from json_agg)
        import json
        screenshots_data = assignment_dict.get('screenshots', '[]')
        if isinstance(screenshots_data, str):
            assignment_dict['screenshots'] = json.loads(screenshots_data) if screenshots_data != '[]' else []
        else:
            assignment_dict['screenshots'] = screenshots_data if screenshots_data else []

        # Serialize datetime fields
        if assignment_dict.get('deadline'):
            assignment_dict['deadline'] = to_iso8601(assignment_dict['deadline'])
        if assignment_dict.get('assigned_at'):
            assignment_dict['assigned_at'] = to_iso8601(assignment_dict['assigned_at'])
        if assignment_dict.get('submitted_at'):
            assignment_dict['submitted_at'] = to_iso8601(assignment_dict['submitted_at'])

        result.append(assignment_dict)

    logger.debug(f"Returned {len(result)} active tasks for user {telegram_id}")
    return result


@router.get("/{assignment_id}")
async def get_task_details(
    assignment_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get detailed task assignment information.

    Requires authentication and ownership.

    Path parameters:
        assignment_id: Task assignment ID

    Returns:
        Task assignment with full task details and screenshots

    Raises:
        401: Not authenticated
        403: Not authorized (not owner)
        404: Assignment not found
    """
    telegram_id = user["telegram_id"]

    # Get assignment record
    assignment = await db.fetch_one(
        "SELECT * FROM task_assignments WHERE id = $1",
        assignment_id
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task assignment not found"
        )

    # Check ownership
    if assignment['user_id'] != telegram_id:
        logger.warning(f"User {telegram_id} attempted to access assignment {assignment_id} owned by {assignment['user_id']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task assignment"
        )

    # Get screenshots
    screenshots = await db.fetch_all(
        "SELECT id, file_path, uploaded_at FROM screenshots WHERE assignment_id = $1 ORDER BY uploaded_at ASC",
        assignment_id
    )

    # Fetch full task payload to match assignment response format
    task_full = await db.fetch_one(
        "SELECT * FROM tasks WHERE id = $1",
        assignment['task_id']
    )

    if not task_full:
        logger.error(
            "Task %s referenced by assignment %s not found",
            assignment['task_id'],
            assignment_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task data is unavailable"
        )

    # Build response
    result = dict(assignment)
    result['screenshots'] = []
    for screenshot in screenshots:
        screenshot_dict = dict(screenshot)
        if screenshot_dict.get('uploaded_at'):
            screenshot_dict['uploaded_at'] = to_iso8601(screenshot_dict['uploaded_at'])
        result['screenshots'].append(screenshot_dict)

    # Serialize datetime fields
    if result.get('deadline'):
        result['deadline'] = to_iso8601(result['deadline'])
    if result.get('created_at'):
        result['created_at'] = to_iso8601(result['created_at'])
    if result.get('assigned_at'):
        result['assigned_at'] = to_iso8601(result['assigned_at'])
    if result.get('submitted_at'):
        result['submitted_at'] = to_iso8601(result['submitted_at'])

    # Attach full task data with serialized datetimes
    task_dict = dict(task_full)
    if task_dict.get('created_at'):
        task_dict['created_at'] = to_iso8601(task_dict['created_at'])
    if task_dict.get('updated_at'):
        task_dict['updated_at'] = to_iso8601(task_dict['updated_at'])

    result['task'] = task_dict

    logger.debug(f"Returned details for assignment {assignment_id} to user {telegram_id}")
    return result


@router.post("/{task_id}/assign")
async def assign_task(
    task_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Assign task to current user.

    Checks:
    - User has not reached MAX_ACTIVE_TASKS limit (10)
    - Task exists and is available
    - Uses transaction with SELECT FOR UPDATE to prevent race conditions

    Requires authentication.

    Path parameters:
        task_id: Task ID to assign

    Returns:
        Created task assignment with task details

    Raises:
        400: User has reached task limit
        404: Task not found
        409: Task no longer available
    """
    telegram_id = user["telegram_id"]

    # Use transaction with FOR UPDATE to prevent race conditions
    # Check limit, availability, and assign - all atomically
    try:
        async with db.transaction() as conn:
            # Check active tasks limit within transaction
            # FIXED: Split into two queries to avoid "FOR UPDATE with aggregate functions" error
            # First lock the rows, then count them
            # This prevents race condition where multiple concurrent requests
            # could all pass the limit check before any assignment is created

            # Step 1: Lock all user's active assignment rows
            await conn.execute(
                """
                SELECT 1
                FROM task_assignments
                WHERE user_id = $1 AND status = 'assigned'
                FOR UPDATE
                """,
                telegram_id
            )

            # Step 2: Now safely count them
            active_count = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM task_assignments
                WHERE user_id = $1 AND status = 'assigned'
                """,
                telegram_id
            )

            if active_count >= config.MAX_ACTIVE_TASKS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum active tasks limit reached ({config.MAX_ACTIVE_TASKS})"
                )

            # Lock task row and check availability
            task = await conn.fetchrow(
                "SELECT id, type, price, is_available FROM tasks WHERE id = $1 FOR UPDATE",
                task_id
            )

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found"
                )

            if not task['is_available']:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Task is no longer available"
                )

            # Update task availability
            await conn.execute(
                "UPDATE tasks SET is_available = FALSE, updated_at = NOW() WHERE id = $1",
                task_id
            )

            # Create assignment with deadline = NOW() + TASK_LOCK_HOURS
            assignment = await conn.fetchrow(
                """
                INSERT INTO task_assignments (task_id, user_id, status, deadline)
                VALUES ($1, $2, 'assigned', NOW() + INTERVAL '1 hour' * $3)
                RETURNING *
                """,
                task_id, telegram_id, config.TASK_LOCK_HOURS
            )

        # Get full task details for response
        task_full = await db.fetch_one(
            "SELECT * FROM tasks WHERE id = $1",
            task_id
        )

        # Build response
        result = dict(assignment)
        result['task'] = dict(task_full)

        # Serialize datetime fields
        if result.get('deadline'):
            result['deadline'] = to_iso8601(result['deadline'])
        if result.get('assigned_at'):
            result['assigned_at'] = to_iso8601(result['assigned_at'])
        if result['task'].get('created_at'):
            result['task']['created_at'] = to_iso8601(result['task']['created_at'])
        if result['task'].get('updated_at'):
            result['task']['updated_at'] = to_iso8601(result['task']['updated_at'])

        logger.info(f"User {telegram_id} assigned task {task_id} (assignment {assignment['id']})")
        return result

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to assign task {task_id} to user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign task"
        )


@router.post("/{assignment_id}/submit")
async def submit_task(
    assignment_id: int,
    phone_number: Optional[str] = Body(None, embed=True),
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit task for moderation.

    Validation:
    - User owns the assignment
    - Status is 'assigned' (not already submitted)
    - At least 1 screenshot uploaded
    - For 'phone' tasks: phone_number required and valid

    Requires authentication.

    Path parameters:
        assignment_id: Task assignment ID

    Body:
        phone_number (optional): Phone number for 'phone' type tasks (format: +7XXXXXXXXXX)

    Returns:
        Updated task assignment

    Raises:
        400: Invalid state or missing required fields
        403: Not authorized
        404: Assignment not found
    """
    telegram_id = user["telegram_id"]

    # Get assignment with task type
    assignment = await db.fetch_one(
        """
        SELECT ta.id, ta.user_id, ta.status, t.type, t.id as task_id
        FROM task_assignments ta
        JOIN tasks t ON t.id = ta.task_id
        WHERE ta.id = $1
        """,
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

    # Check status
    if assignment['status'] != 'assigned':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit task in status '{assignment['status']}'"
        )

    # Check screenshots count
    screenshot_count = await db.fetch_val(
        "SELECT COUNT(*) FROM screenshots WHERE assignment_id = $1",
        assignment_id
    )

    if screenshot_count < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one screenshot is required to submit task"
        )

    # Validate phone number for 'phone' tasks
    task_type = assignment['type']
    if task_type == 'phone':
        if not phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required for phone tasks"
            )

        if not validate_phone_number(phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format (must be +7XXXXXXXXXX)"
            )

    # Update assignment
    updated_assignment = await db.fetch_one(
        """
        UPDATE task_assignments
        SET status = 'submitted', submitted_at = NOW(), phone_number = $2
        WHERE id = $1
        RETURNING *
        """,
        assignment_id, phone_number
    )

    # Build response
    result = dict(updated_assignment)
    if result.get('deadline'):
        result['deadline'] = to_iso8601(result['deadline'])
    if result.get('assigned_at'):
        result['assigned_at'] = to_iso8601(result['assigned_at'])
    if result.get('submitted_at'):
        result['submitted_at'] = to_iso8601(result['submitted_at'])

    logger.info(f"User {telegram_id} submitted task assignment {assignment_id} (task {assignment['task_id']})")
    return result


@router.post("/{assignment_id}/cancel")
async def cancel_task(
    assignment_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel task assignment (user gives up).

    Validation:
    - User owns the assignment
    - Status is 'assigned' (can only cancel before submission)

    Actions:
    - Returns task to available pool
    - Deletes assignment and screenshot records from DB (CASCADE)
    - Deletes screenshot files from disk

    Requires authentication.

    Path parameters:
        assignment_id: Task assignment ID

    Returns:
        Success message with task_id

    Raises:
        400: Invalid status
        403: Not authorized
        404: Assignment not found
    """
    telegram_id = user["telegram_id"]

    # Get assignment
    assignment = await db.fetch_one(
        """
        SELECT ta.id, ta.user_id, ta.status, ta.task_id
        FROM task_assignments ta
        WHERE ta.id = $1
        """,
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

    # Check status
    if assignment['status'] != 'assigned':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task in status '{assignment['status']}'. Only 'assigned' tasks can be cancelled."
        )

    task_id = assignment['task_id']

    # Get screenshots for file deletion (before transaction)
    screenshots = await db.fetch_all(
        "SELECT file_path FROM screenshots WHERE assignment_id = $1",
        assignment_id
    )

    # Transaction: update task and delete assignment
    try:
        async with db.transaction() as conn:
            # Return task to pool
            await conn.execute(
                "UPDATE tasks SET is_available = TRUE, updated_at = NOW() WHERE id = $1",
                task_id
            )

            # Delete assignment (CASCADE will delete screenshots from DB)
            await conn.execute(
                "DELETE FROM task_assignments WHERE id = $1",
                assignment_id
            )

        # Delete screenshot files from disk (after successful transaction)
        for screenshot in screenshots:
            try:
                file_path = Path(screenshot['file_path'])
                if file_path.exists():
                    await aiofiles.os.remove(str(file_path))
                    logger.debug(f"Deleted screenshot file: {file_path}")
            except Exception as file_error:
                logger.warning(f"Failed to delete screenshot file {file_path}: {file_error}")

        logger.info(f"User {telegram_id} cancelled task assignment {assignment_id} (task {task_id})")
        return {
            "message": "Task cancelled successfully",
            "task_id": task_id
        }

    except Exception as e:
        logger.error(f"Failed to cancel assignment {assignment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel task"
        )
