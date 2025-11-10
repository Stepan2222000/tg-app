# Moderation Guide

This document contains SQL scripts for manual administrative operations. All scripts should be executed in a PostgreSQL client (e.g., psql, pgAdmin, DBeaver) connected to the database.

**Database Connection:**
- Host: 81.30.105.134
- Port: 5416
- Database: avito_tasker
- User: (as configured)

---

## Table of Contents

1. [View Pending Tasks](#view-pending-tasks)
2. [View Task Screenshots](#view-task-screenshots)
3. [Approve Task](#approve-task)
4. [Reject Task](#reject-task)
5. [View Pending Withdrawals](#view-pending-withdrawals)
6. [Approve Withdrawal](#approve-withdrawal)
7. [Reject Withdrawal](#reject-withdrawal)
8. [View User Information](#view-user-information)
9. [Common Queries](#common-queries)

---

## View Pending Tasks

Get all tasks waiting for moderation approval:

```sql
SELECT
    ta.id as assignment_id,
    ta.user_id,
    u.username,
    u.first_name,
    t.id as task_id,
    t.type as task_type,
    t.price,
    t.avito_url,
    t.message_text,
    ta.phone_number,
    ta.submitted_at,
    (SELECT COUNT(*) FROM screenshots WHERE assignment_id = ta.id) as screenshot_count
FROM task_assignments ta
JOIN users u ON u.telegram_id = ta.user_id
JOIN tasks t ON t.id = ta.task_id
WHERE ta.status = 'submitted'
ORDER BY ta.submitted_at ASC;
```

---

## View Task Screenshots

View all screenshots for a specific task assignment:

```sql
-- Replace {assignment_id} with actual assignment ID
SELECT
    id as screenshot_id,
    file_path,
    uploaded_at
FROM screenshots
WHERE assignment_id = {assignment_id}
ORDER BY uploaded_at ASC;
```

**To view screenshots:**
- Screenshot files are stored in `./uploads/screenshots/` directory
- Access via: `http://your-backend-url/static/screenshots/{filename}`
- Or navigate to the backend server's filesystem: `/path/to/backend/uploads/screenshots/`

---

## Approve Task

**IMPORTANT:** This script automatically:
1. Approves the task assignment
2. Credits the user's main balance
3. Returns the task to the pool (makes it available again)
4. **Automatically calculates and credits referral commission (100%) if user was referred**

```sql
-- Replace {assignment_id} with actual assignment ID
BEGIN;

-- Get task and user info
DO $$
DECLARE
    v_user_id BIGINT;
    v_task_id INTEGER;
    v_task_price INTEGER;
    v_task_type VARCHAR(20);
    v_referrer_id BIGINT;
BEGIN
    -- Get assignment details
    SELECT user_id, task_id INTO v_user_id, v_task_id
    FROM task_assignments
    WHERE id = {assignment_id};

    -- Get task details
    SELECT price, type INTO v_task_price, v_task_type
    FROM tasks
    WHERE id = v_task_id;

    -- Get referrer if exists
    SELECT referred_by INTO v_referrer_id
    FROM users
    WHERE telegram_id = v_user_id;

    -- 1. Approve the task assignment
    UPDATE task_assignments
    SET status = 'approved'
    WHERE id = {assignment_id};

    -- 2. Credit user's main balance
    -- NEW-CRITICAL-3 FIX: Check for overflow before crediting
    IF v_task_price + (SELECT main_balance FROM users WHERE telegram_id = v_user_id) > 2000000000 THEN
        RAISE EXCEPTION 'Balance overflow: cannot credit more than 2B rubles total (current balance + ₽% would exceed limit)', v_task_price;
    END IF;

    UPDATE users
    SET main_balance = main_balance + v_task_price,
        updated_at = NOW()
    WHERE telegram_id = v_user_id;

    -- 3. Return task to pool (make available again)
    UPDATE tasks
    SET is_available = TRUE,
        updated_at = NOW()
    WHERE id = v_task_id;

    -- 4. If user has referrer, calculate and credit commission (100%)
    IF v_referrer_id IS NOT NULL THEN
        -- Calculate commission (100% of task price)
        DECLARE
            v_commission INTEGER;
            v_referral_username VARCHAR(255);
        BEGIN
            -- Commission is now 100% of task price (same as what the user earns)
            v_commission := v_task_price;

            -- Get referred user's username for record
            SELECT username INTO v_referral_username
            FROM users
            WHERE telegram_id = v_user_id;

            -- Create referral earning record
            INSERT INTO referral_earnings (
                referrer_id,
                referral_id,
                amount,
                task_assignment_id,
                task_type,
                referral_username
            )
            VALUES (
                v_referrer_id,
                v_user_id,
                v_commission,
                {assignment_id},
                v_task_type,
                v_referral_username
            );

            -- NEW-CRITICAL-3 FIX: Check for overflow before crediting referrer
            IF v_commission + (SELECT referral_balance FROM users WHERE telegram_id = v_referrer_id) > 2000000000 THEN
                RAISE EXCEPTION 'Referral balance overflow for referrer %: cannot credit ₽%', v_referrer_id, v_commission;
            END IF;

            -- Credit referrer's referral balance
            UPDATE users
            SET referral_balance = referral_balance + v_commission,
                updated_at = NOW()
            WHERE telegram_id = v_referrer_id;

            RAISE NOTICE 'Credited % commission (₽%) to referrer %', v_commission, v_commission, v_referrer_id;
        END;
    END IF;

    RAISE NOTICE 'Task assignment % approved. User % credited ₽%', {assignment_id}, v_user_id, v_task_price;
END;
$$;

COMMIT;
```

**Simplified version (if the above doesn't work in your client):**

```sql
-- Step 1: Approve task and credit user
BEGIN;

UPDATE task_assignments
SET status = 'approved'
WHERE id = {assignment_id};

UPDATE users
SET main_balance = main_balance + (
    SELECT price FROM tasks WHERE id = (
        SELECT task_id FROM task_assignments WHERE id = {assignment_id}
    )
)
WHERE telegram_id = (
    SELECT user_id FROM task_assignments WHERE id = {assignment_id}
);

UPDATE tasks
SET is_available = TRUE
WHERE id = (
    SELECT task_id FROM task_assignments WHERE id = {assignment_id}
);

-- Step 2: Handle referral commission (if user has referrer)
INSERT INTO referral_earnings (referrer_id, referral_id, amount, task_assignment_id, task_type, referral_username)
SELECT
    u.referred_by as referrer_id,
    u.telegram_id as referral_id,
    t.price as amount,
    ta.id as task_assignment_id,
    t.type as task_type,
    u.username as referral_username
FROM task_assignments ta
JOIN users u ON u.telegram_id = ta.user_id
JOIN tasks t ON t.id = ta.task_id
WHERE ta.id = {assignment_id}
  AND u.referred_by IS NOT NULL;

UPDATE users
SET referral_balance = referral_balance + (
    SELECT t.price
    FROM task_assignments ta
    JOIN tasks t ON t.id = ta.task_id
    WHERE ta.id = {assignment_id}
)
WHERE telegram_id = (
    SELECT referred_by
    FROM users
    WHERE telegram_id = (
        SELECT user_id FROM task_assignments WHERE id = {assignment_id}
    )
)
AND EXISTS (
    SELECT 1 FROM users u
    JOIN task_assignments ta ON ta.user_id = u.telegram_id
    WHERE ta.id = {assignment_id} AND u.referred_by IS NOT NULL
);

COMMIT;
```

---

## Reject Task

Reject a task and return it to the pool:

```sql
-- Replace {assignment_id} with actual assignment ID
BEGIN;

-- 1. Reject the task assignment
UPDATE task_assignments
SET status = 'rejected'
WHERE id = {assignment_id};

-- 2. Return task to pool (make available again)
UPDATE tasks
SET is_available = TRUE,
    updated_at = NOW()
WHERE id = (
    SELECT task_id FROM task_assignments WHERE id = {assignment_id}
);

COMMIT;
```

**Note:** Screenshots are NOT automatically deleted when rejecting a task. If you want to delete them, see "Delete Task Screenshots" below.

---

## View Pending Withdrawals

Get all withdrawals waiting for approval:

```sql
SELECT
    w.id as withdrawal_id,
    w.user_id,
    u.username,
    u.first_name,
    u.main_balance,
    u.referral_balance,
    (u.main_balance + u.referral_balance) as total_balance,
    w.amount,
    w.method,
    w.details,
    w.created_at
FROM withdrawals w
JOIN users u ON u.telegram_id = w.user_id
WHERE w.status = 'pending'
ORDER BY w.created_at ASC;
```

---

## Approve Withdrawal

**IMPORTANT:** This script automatically deducts the amount from user's balance (main balance first, then referral balance if needed).

```sql
-- Replace {withdrawal_id} with actual withdrawal ID
BEGIN;

-- Get withdrawal details
DO $$
DECLARE
    v_withdrawal_id INTEGER := {withdrawal_id};
    v_user_id BIGINT;
    v_amount INTEGER;
    v_main_balance INTEGER;
    v_referral_balance INTEGER;
    v_deduct_from_main INTEGER;
    v_deduct_from_referral INTEGER;
BEGIN
    -- Get withdrawal info
    SELECT user_id, amount INTO v_user_id, v_amount
    FROM withdrawals
    WHERE id = v_withdrawal_id;

    -- Get user's current balances
    SELECT main_balance, referral_balance INTO v_main_balance, v_referral_balance
    FROM users
    WHERE telegram_id = v_user_id;

    -- CRITICAL-2 FIX: Check if user has enough balance
    IF (v_main_balance + v_referral_balance) < v_amount THEN
        RAISE EXCEPTION 'Insufficient balance: user has ₽% but withdrawal amount is ₽%',
            (v_main_balance + v_referral_balance), v_amount;
    END IF;

    -- Calculate how much to deduct from each balance
    -- Priority: main_balance first, then referral_balance
    IF v_main_balance >= v_amount THEN
        v_deduct_from_main := v_amount;
        v_deduct_from_referral := 0;
    ELSE
        v_deduct_from_main := v_main_balance;
        v_deduct_from_referral := v_amount - v_main_balance;
    END IF;

    -- Deduct from balances
    UPDATE users
    SET
        main_balance = main_balance - v_deduct_from_main,
        referral_balance = referral_balance - v_deduct_from_referral,
        updated_at = NOW()
    WHERE telegram_id = v_user_id;

    -- Approve withdrawal
    UPDATE withdrawals
    SET
        status = 'approved',
        processed_at = NOW()
    WHERE id = v_withdrawal_id;

    RAISE NOTICE 'Withdrawal % approved. Deducted ₽% from main, ₽% from referral',
        v_withdrawal_id, v_deduct_from_main, v_deduct_from_referral;
END;
$$;

COMMIT;
```

**Simplified version:**

```sql
-- Replace {withdrawal_id} with actual withdrawal ID
BEGIN;

-- Deduct amount (main balance first, then referral)
UPDATE users
SET
    main_balance = GREATEST(0, main_balance - (
        SELECT amount FROM withdrawals WHERE id = {withdrawal_id}
    )),
    referral_balance = GREATEST(0, referral_balance - GREATEST(0,
        (SELECT amount FROM withdrawals WHERE id = {withdrawal_id}) - main_balance
    )),
    updated_at = NOW()
WHERE telegram_id = (
    SELECT user_id FROM withdrawals WHERE id = {withdrawal_id}
);

-- Approve withdrawal
UPDATE withdrawals
SET
    status = 'approved',
    processed_at = NOW()
WHERE id = {withdrawal_id};

COMMIT;
```

---

## Reject Withdrawal

**IMPORTANT:** This script automatically returns money to user's main balance when rejecting withdrawal.

```sql
-- Replace {withdrawal_id} with actual withdrawal ID
BEGIN;

-- HIGH-14 FIX: Return money to user when rejecting withdrawal
DO $$
DECLARE
    v_withdrawal_id INTEGER := {withdrawal_id};
    v_user_id BIGINT;
    v_amount INTEGER;
BEGIN
    -- Get withdrawal info
    SELECT user_id, amount INTO v_user_id, v_amount
    FROM withdrawals
    WHERE id = v_withdrawal_id;

    -- Return money to user's main balance
    UPDATE users
    SET main_balance = main_balance + v_amount
    WHERE telegram_id = v_user_id;

    -- Reject withdrawal
    UPDATE withdrawals
    SET
        status = 'rejected',
        processed_at = NOW()
    WHERE id = v_withdrawal_id;

    RAISE NOTICE 'Withdrawal % rejected. Returned ₽% to user %',
        v_withdrawal_id, v_amount, v_user_id;
END;
$$;

COMMIT;
```

**Note:** Money is deducted when withdrawal is created (status='pending'), so we must return it when rejecting.

---

## View User Information

Get detailed information about a specific user:

```sql
-- Replace {telegram_id} with actual user Telegram ID
SELECT
    telegram_id,
    username,
    first_name,
    main_balance,
    referral_balance,
    (main_balance + referral_balance) as total_balance,
    referred_by,
    created_at,
    updated_at,
    (SELECT COUNT(*) FROM users WHERE referred_by = {telegram_id}) as total_referrals,
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = {telegram_id}) as total_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = {telegram_id} AND status = 'approved') as approved_tasks,
    (SELECT COUNT(*) FROM withdrawals WHERE user_id = {telegram_id}) as total_withdrawals
FROM users
WHERE telegram_id = {telegram_id};
```

---

## Common Queries

### Get User's Task History

```sql
-- Replace {telegram_id} with user ID
SELECT
    ta.id as assignment_id,
    t.type as task_type,
    t.price,
    ta.status,
    ta.assigned_at,
    ta.submitted_at,
    ta.deadline,
    (SELECT COUNT(*) FROM screenshots WHERE assignment_id = ta.id) as screenshot_count
FROM task_assignments ta
JOIN tasks t ON t.id = ta.task_id
WHERE ta.user_id = {telegram_id}
ORDER BY ta.assigned_at DESC;
```

### Get User's Withdrawal History

```sql
-- Replace {telegram_id} with user ID
SELECT
    id as withdrawal_id,
    amount,
    method,
    status,
    created_at,
    processed_at
FROM withdrawals
WHERE user_id = {telegram_id}
ORDER BY created_at DESC;
```

### Get User's Referral Earnings

```sql
-- Replace {telegram_id} with user ID (referrer)
SELECT
    re.referral_id,
    u.username as referral_username,
    re.amount,
    re.task_type,
    re.earned_at
FROM referral_earnings re
LEFT JOIN users u ON u.telegram_id = re.referral_id
WHERE re.referrer_id = {telegram_id}
ORDER BY re.earned_at DESC;
```

### Get Statistics Dashboard

```sql
SELECT
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM task_assignments WHERE status = 'submitted') as pending_tasks,
    (SELECT COUNT(*) FROM withdrawals WHERE status = 'pending') as pending_withdrawals,
    (SELECT COUNT(*) FROM tasks WHERE is_available = TRUE) as available_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE status = 'assigned') as active_tasks,
    (SELECT SUM(main_balance + referral_balance) FROM users) as total_user_balance;
```

### Delete Task Screenshots (Manual Cleanup)

**WARNING:** This permanently deletes screenshot records AND files from disk.

```sql
-- Replace {assignment_id} with actual assignment ID
-- First, note the file paths to delete manually from filesystem
SELECT file_path FROM screenshots WHERE assignment_id = {assignment_id};

-- Then delete records from database
DELETE FROM screenshots WHERE assignment_id = {assignment_id};
```

After running the above, manually delete the files from `./uploads/screenshots/` directory on the server.

---

## Best Practices

1. **Always use transactions (BEGIN/COMMIT)** for multi-step operations
2. **Double-check IDs** before running approval/rejection scripts
3. **Verify screenshots** before approving tasks
4. **Keep a log** of all moderation actions (date, action, assignment_id/withdrawal_id)
5. **Regular backups** of the database
6. **Monitor user balances** to prevent fraud
7. **Check referral chains** for suspicious patterns

---

## Troubleshooting

### Task approval fails with foreign key error
**Problem:** User doesn't exist in database
**Solution:** Check if user_id exists in `users` table. User should be created via `/api/auth/init` endpoint.

### Referral commission not credited
**Problem:** User's `referred_by` field is NULL
**Solution:** This is normal if user wasn't referred by anyone. Commission only applies to referred users.

### Withdrawal approval removes too much balance
**Problem:** Calculation error
**Solution:** Check user's balances before approval. Use the "View User Information" query.

### Screenshot files missing
**Problem:** Files deleted from disk but records still in DB
**Solution:** Run cleanup query to remove orphaned screenshot records.

---

## Security Notes

- **Never expose this document** to end users
- **Restrict database access** to admins only
- **Use VPN or IP whitelist** for database connections
- **Log all admin actions** for audit trail
- **Regularly review** large withdrawals and referral earnings

---

**Last Updated:** 2025-11-04
**Version:** 1.0
