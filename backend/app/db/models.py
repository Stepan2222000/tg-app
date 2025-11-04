# backend/app/db/models.py
"""
TypedDict models for database rows.
Ensures type safety without ORM overhead.
Aligned with TypeScript interfaces in frontend/src/types/index.ts
"""

from typing import TypedDict, Optional


class UserRow(TypedDict):
    """User table row - matches User interface in TypeScript."""
    telegram_id: int
    username: Optional[str]
    first_name: str
    main_balance: int
    referral_balance: int
    referred_by: Optional[int]
    created_at: str


class TaskRow(TypedDict):
    """Task table row - matches Task interface in TypeScript."""
    id: int
    type: str  # 'simple' or 'phone'
    avito_url: str
    message_text: str
    price: int
    is_available: bool
    created_at: str
    updated_at: str


class TaskAssignmentRow(TypedDict):
    """Task assignment table row - matches TaskAssignment interface in TypeScript."""
    id: int
    task_id: int
    user_id: int
    status: str  # 'assigned', 'submitted', 'approved', 'rejected'
    deadline: str
    phone_number: Optional[str]
    assigned_at: str
    submitted_at: Optional[str]
    created_at: str


class ScreenshotRow(TypedDict):
    """Screenshot table row."""
    id: int
    assignment_id: int
    file_path: str
    uploaded_at: str


class WithdrawalRow(TypedDict):
    """Withdrawal table row - matches Withdrawal interface in TypeScript."""
    id: int
    user_id: int
    amount: int
    method: str  # 'card' or 'sbp'
    details: dict  # JSON with bank details
    status: str  # 'pending', 'approved', 'rejected'
    created_at: str
    processed_at: Optional[str]


class ReferralEarningRow(TypedDict):
    """Referral earnings table row - extended version."""
    id: int
    referrer_id: int
    referral_id: int
    amount: int
    task_assignment_id: Optional[int]
    task_type: Optional[str]
    referral_username: Optional[str]
    created_at: str
