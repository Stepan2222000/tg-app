-- Migration: Add UNIQUE constraint to prevent double commission payments
-- Date: 2025-11-06
-- Purpose: Prevent admins from accidentally running approval script twice for same task

-- This constraint ensures that each task_assignment can only have ONE referral
-- commission record, preventing double payments if admin accidentally approves
-- the same task twice.

-- Add UNIQUE constraint on task_assignment_id (with partial index to allow NULLs)
-- Note: We use a partial index WHERE clause because some rows may have NULL task_assignment_id
ALTER TABLE referral_earnings
ADD CONSTRAINT unique_task_commission
UNIQUE (task_assignment_id)
WHERE task_assignment_id IS NOT NULL;

-- Verification query (optional, for manual testing):
-- SELECT task_assignment_id, COUNT(*)
-- FROM referral_earnings
-- WHERE task_assignment_id IS NOT NULL
-- GROUP BY task_assignment_id
-- HAVING COUNT(*) > 1;
-- (Should return 0 rows after migration)
