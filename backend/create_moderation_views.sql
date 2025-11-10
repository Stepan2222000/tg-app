-- Moderation Views
-- Convenient views for administrators to review pending tasks and withdrawals
-- Execute this file once to create all views

-- ============================================================================
-- VIEW: v_pending_tasks
-- Complete information about all tasks waiting for moderation
-- ============================================================================
CREATE OR REPLACE VIEW v_pending_tasks AS
SELECT
    ta.id as assignment_id,
    ta.user_id,
    u.username,
    u.first_name,
    u.main_balance as user_main_balance,
    u.referral_balance as user_referral_balance,
    (u.main_balance + u.referral_balance) as user_total_balance,
    t.id as task_id,
    t.type as task_type,
    t.price,
    t.avito_url,
    t.message_text,
    ta.phone_number,
    ta.assigned_at,
    ta.submitted_at,
    ta.deadline,
    EXTRACT(EPOCH FROM (NOW() - ta.submitted_at))/3600 as hours_waiting,
    (SELECT COUNT(*) FROM screenshots WHERE assignment_id = ta.id) as screenshot_count,
    (SELECT array_agg(file_path ORDER BY uploaded_at) FROM screenshots WHERE assignment_id = ta.id) as screenshot_paths,
    -- User statistics
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = ta.user_id AND status = 'approved') as user_approved_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = ta.user_id AND status = 'rejected') as user_rejected_tasks,
    -- Referral info
    u.referred_by as referrer_id,
    (SELECT username FROM users WHERE telegram_id = u.referred_by) as referrer_username,
    CASE
        WHEN u.referred_by IS NOT NULL
        THEN ROUND(t.price * 0.5)::INTEGER
        ELSE 0
    END as referral_commission_will_be_paid
FROM task_assignments ta
JOIN users u ON u.telegram_id = ta.user_id
JOIN tasks t ON t.id = ta.task_id
WHERE ta.status = 'submitted'
ORDER BY ta.submitted_at ASC;

COMMENT ON VIEW v_pending_tasks IS 'All tasks waiting for admin moderation with complete context';

-- ============================================================================
-- VIEW: v_pending_withdrawals
-- Complete information about all withdrawal requests
-- ============================================================================
CREATE OR REPLACE VIEW v_pending_withdrawals AS
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
    w.created_at,
    EXTRACT(EPOCH FROM (NOW() - w.created_at))/3600 as hours_waiting,
    -- User statistics
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = w.user_id AND status = 'approved') as user_approved_tasks,
    (SELECT COUNT(*) FROM withdrawals WHERE user_id = w.user_id AND status = 'approved') as user_previous_withdrawals,
    (SELECT SUM(amount) FROM withdrawals WHERE user_id = w.user_id AND status = 'approved') as user_total_withdrawn,
    -- Validation flags
    (u.main_balance + u.referral_balance) >= w.amount as has_sufficient_balance,
    CASE
        WHEN w.amount <= u.main_balance THEN 'only_main'
        WHEN w.amount <= (u.main_balance + u.referral_balance) THEN 'main_and_referral'
        ELSE 'insufficient'
    END as balance_deduction_type
FROM withdrawals w
JOIN users u ON u.telegram_id = w.user_id
WHERE w.status = 'pending'
ORDER BY w.created_at ASC;

COMMENT ON VIEW v_pending_withdrawals IS 'All withdrawal requests waiting for admin approval';

-- ============================================================================
-- VIEW: v_user_stats
-- Complete user statistics for quick reference
-- ============================================================================
CREATE OR REPLACE VIEW v_user_stats AS
SELECT
    u.telegram_id,
    u.username,
    u.first_name,
    u.main_balance,
    u.referral_balance,
    (u.main_balance + u.referral_balance) as total_balance,
    u.referred_by,
    (SELECT username FROM users WHERE telegram_id = u.referred_by) as referrer_username,
    u.created_at,
    -- Task statistics
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = u.telegram_id) as total_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = u.telegram_id AND status = 'assigned') as active_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = u.telegram_id AND status = 'submitted') as submitted_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = u.telegram_id AND status = 'approved') as approved_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE user_id = u.telegram_id AND status = 'rejected') as rejected_tasks,
    -- Withdrawal statistics
    (SELECT COUNT(*) FROM withdrawals WHERE user_id = u.telegram_id) as total_withdrawal_requests,
    (SELECT COUNT(*) FROM withdrawals WHERE user_id = u.telegram_id AND status = 'approved') as approved_withdrawals,
    (SELECT SUM(amount) FROM withdrawals WHERE user_id = u.telegram_id AND status = 'approved') as total_withdrawn,
    -- Referral statistics (as referrer)
    (SELECT COUNT(*) FROM users WHERE referred_by = u.telegram_id) as total_referrals,
    (SELECT COUNT(*) FROM referral_earnings WHERE referrer_id = u.telegram_id) as total_referral_earnings_count,
    (SELECT SUM(amount) FROM referral_earnings WHERE referrer_id = u.telegram_id) as total_referral_earnings_amount,
    -- Quality metrics
    CASE
        WHEN (SELECT COUNT(*) FROM task_assignments WHERE user_id = u.telegram_id AND status IN ('approved', 'rejected')) > 0
        THEN ROUND(
            (SELECT COUNT(*)::DECIMAL FROM task_assignments WHERE user_id = u.telegram_id AND status = 'approved') * 100.0 /
            (SELECT COUNT(*) FROM task_assignments WHERE user_id = u.telegram_id AND status IN ('approved', 'rejected'))
        , 2)
        ELSE NULL
    END as approval_rate_percent
FROM users u
ORDER BY u.created_at DESC;

COMMENT ON VIEW v_user_stats IS 'Complete statistics for all users';

-- ============================================================================
-- VIEW: v_recent_activity
-- Recent activity across all operations for monitoring
-- ============================================================================
CREATE OR REPLACE VIEW v_recent_activity AS
-- Recent task submissions
SELECT
    'task_submitted' as activity_type,
    ta.id as record_id,
    ta.user_id,
    u.username,
    t.price as amount,
    ta.submitted_at as activity_time,
    'assignment_id: ' || ta.id || ', task_type: ' || t.type as details
FROM task_assignments ta
JOIN users u ON u.telegram_id = ta.user_id
JOIN tasks t ON t.id = ta.task_id
WHERE ta.status = 'submitted' AND ta.submitted_at > NOW() - INTERVAL '7 days'

UNION ALL

-- Recent task approvals
SELECT
    'task_approved' as activity_type,
    ta.id as record_id,
    ta.user_id,
    u.username,
    t.price as amount,
    ta.submitted_at as activity_time,  -- Using submitted_at as we don't have approved_at
    'assignment_id: ' || ta.id || ', task_type: ' || t.type as details
FROM task_assignments ta
JOIN users u ON u.telegram_id = ta.user_id
JOIN tasks t ON t.id = ta.task_id
WHERE ta.status = 'approved' AND ta.submitted_at > NOW() - INTERVAL '7 days'

UNION ALL

-- Recent withdrawal requests
SELECT
    'withdrawal_requested' as activity_type,
    w.id as record_id,
    w.user_id,
    u.username,
    w.amount,
    w.created_at as activity_time,
    'method: ' || w.method || ', status: ' || w.status as details
FROM withdrawals w
JOIN users u ON u.telegram_id = w.user_id
WHERE w.created_at > NOW() - INTERVAL '7 days'

UNION ALL

-- Recent referral earnings
SELECT
    'referral_earned' as activity_type,
    re.id as record_id,
    re.referrer_id as user_id,
    u.username,
    re.amount,
    re.created_at as activity_time,
    'from_user: ' || re.referral_username || ', task_type: ' || re.task_type as details
FROM referral_earnings re
JOIN users u ON u.telegram_id = re.referrer_id
WHERE re.created_at > NOW() - INTERVAL '7 days'

ORDER BY activity_time DESC;

COMMENT ON VIEW v_recent_activity IS 'Recent activity across all operations (last 7 days)';

-- ============================================================================
-- VIEW: v_admin_dashboard
-- Quick overview for admin dashboard
-- ============================================================================
CREATE OR REPLACE VIEW v_admin_dashboard AS
SELECT
    -- Pending items
    (SELECT COUNT(*) FROM task_assignments WHERE status = 'submitted') as pending_tasks,
    (SELECT COUNT(*) FROM withdrawals WHERE status = 'pending') as pending_withdrawals,

    -- Active items
    (SELECT COUNT(*) FROM tasks WHERE is_available = TRUE) as available_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE status = 'assigned') as active_assignments,

    -- Total users
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours') as new_users_24h,
    (SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '7 days') as new_users_7d,

    -- Financial overview
    (SELECT SUM(main_balance + referral_balance) FROM users) as total_user_balance,
    (SELECT SUM(main_balance) FROM users) as total_main_balance,
    (SELECT SUM(referral_balance) FROM users) as total_referral_balance,

    -- Task statistics
    (SELECT COUNT(*) FROM task_assignments WHERE status = 'approved') as total_approved_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE status = 'rejected') as total_rejected_tasks,
    (SELECT COUNT(*) FROM task_assignments WHERE submitted_at > NOW() - INTERVAL '24 hours') as tasks_submitted_24h,

    -- Withdrawal statistics
    (SELECT COUNT(*) FROM withdrawals WHERE status = 'approved') as total_approved_withdrawals,
    (SELECT SUM(amount) FROM withdrawals WHERE status = 'approved') as total_withdrawn_amount,
    (SELECT COUNT(*) FROM withdrawals WHERE created_at > NOW() - INTERVAL '24 hours') as withdrawal_requests_24h,

    -- Referral statistics
    (SELECT COUNT(*) FROM users WHERE referred_by IS NOT NULL) as total_referred_users,
    (SELECT SUM(amount) FROM referral_earnings) as total_referral_commissions_paid;

COMMENT ON VIEW v_admin_dashboard IS 'Quick overview dashboard for administrators';

-- ============================================================================
-- Grant permissions (adjust as needed for your setup)
-- ============================================================================
-- GRANT SELECT ON v_pending_tasks TO admin;
-- GRANT SELECT ON v_pending_withdrawals TO admin;
-- GRANT SELECT ON v_user_stats TO admin;
-- GRANT SELECT ON v_recent_activity TO admin;
-- GRANT SELECT ON v_admin_dashboard TO admin;

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Example 1: View all pending tasks with full context
-- SELECT * FROM v_pending_tasks;

-- Example 2: View pending tasks sorted by waiting time
-- SELECT assignment_id, username, task_type, price, hours_waiting, screenshot_count
-- FROM v_pending_tasks
-- ORDER BY hours_waiting DESC;

-- Example 3: View all pending withdrawals
-- SELECT * FROM v_pending_withdrawals;

-- Example 4: Check user statistics before approving
-- SELECT * FROM v_user_stats WHERE telegram_id = 123456789;

-- Example 5: Quick dashboard overview
-- SELECT * FROM v_admin_dashboard;

-- Example 6: Recent activity feed
-- SELECT * FROM v_recent_activity LIMIT 50;

-- Example 7: Find users with low approval rates
-- SELECT telegram_id, username, total_tasks, approved_tasks, rejected_tasks, approval_rate_percent
-- FROM v_user_stats
-- WHERE total_tasks > 5 AND approval_rate_percent < 50
-- ORDER BY approval_rate_percent ASC;
