-- Avito Tasker Database Schema
-- PostgreSQL 14+
-- Aligned with TypeScript interfaces in frontend/src/types/index.ts
--
-- TIMEZONE NOTE: All timestamps use TIMESTAMPTZ for timezone-aware storage.
-- Server should run in UTC timezone for consistency.

-- ============================================================================
-- TABLE: users
-- Alignment: User interface
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    main_balance INTEGER DEFAULT 0 NOT NULL,          -- in rubles
    referral_balance INTEGER DEFAULT 0 NOT NULL,      -- in rubles
    referred_by BIGINT,                                -- FK to users.telegram_id (immutable after first set)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (referred_by) REFERENCES users(telegram_id) ON DELETE SET NULL,
    -- NEW-CRITICAL-3 FIX: Prevent integer overflow and negative balances
    -- PostgreSQL INTEGER max: 2,147,483,647
    -- Limit to 2B rubles (safe margin) to prevent overflow
    CONSTRAINT check_main_balance_range CHECK (main_balance >= 0 AND main_balance <= 2000000000),
    CONSTRAINT check_referral_balance_range CHECK (referral_balance >= 0 AND referral_balance <= 2000000000),
    -- NEW-HIGH-9 FIX: Prevent self-referral at database level
    CONSTRAINT check_no_self_referral CHECK (referred_by IS NULL OR referred_by != telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- ============================================================================
-- TABLE: tasks
-- Alignment: Task interface (id, type, avito_url, message_text, price, is_available)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL CHECK (type IN ('simple', 'phone')),
    avito_url TEXT NOT NULL,
    message_text TEXT NOT NULL,
    price INTEGER NOT NULL,                            -- in rubles
    is_available BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type);
CREATE INDEX IF NOT EXISTS idx_tasks_is_available ON tasks(is_available);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- ============================================================================
-- TABLE: task_assignments
-- Alignment: TaskAssignment interface
-- Note: screenshots stored separately in 'screenshots' table
-- ============================================================================
CREATE TABLE IF NOT EXISTS task_assignments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'assigned'
        CHECK (status IN ('assigned', 'submitted', 'approved', 'rejected')),
    deadline TIMESTAMPTZ NOT NULL,                     -- 24 hours from assignment
    phone_number VARCHAR(20),
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_assignments_user_id ON task_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_task_assignments_task_id ON task_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_task_assignments_status ON task_assignments(status);
CREATE INDEX IF NOT EXISTS idx_task_assignments_deadline ON task_assignments(deadline);
CREATE INDEX IF NOT EXISTS idx_task_assignments_assigned_at ON task_assignments(assigned_at);

-- CRITICAL-7: Prevent user from taking same task multiple times simultaneously
CREATE UNIQUE INDEX IF NOT EXISTS idx_task_assignments_user_task_active
ON task_assignments(user_id, task_id)
WHERE status = 'assigned';

-- ============================================================================
-- TABLE: screenshots
-- Separate table with (id, assignment_id FK, file_path, uploaded_at)
-- Alignment: TaskAssignment.screenshots becomes string[] of file paths via JOIN
-- ============================================================================
CREATE TABLE IF NOT EXISTS screenshots (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES task_assignments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_screenshots_assignment_id ON screenshots(assignment_id);
CREATE INDEX IF NOT EXISTS idx_screenshots_uploaded_at ON screenshots(uploaded_at);

-- ============================================================================
-- TABLE: withdrawals
-- Alignment: Withdrawal interface
-- details stored as JSONB for card/sbp flexibility
-- ============================================================================
CREATE TABLE IF NOT EXISTS withdrawals (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,                           -- in rubles
    method VARCHAR(10) NOT NULL CHECK (method IN ('card', 'sbp')),
    details JSONB NOT NULL,                            -- {card_number, cardholder_name} or {bank_name, phone_number}
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    processed_at TIMESTAMPTZ,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_withdrawals_user_id ON withdrawals(user_id);
CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON withdrawals(status);
CREATE INDEX IF NOT EXISTS idx_withdrawals_created_at ON withdrawals(created_at);
-- NEW-CRITICAL-5 FIX: Composite index for efficient queries filtering by both user_id and status
-- Used in withdrawal creation query: WHERE user_id = X AND status = 'pending'
CREATE INDEX IF NOT EXISTS idx_withdrawals_user_status ON withdrawals(user_id, status);

-- ============================================================================
-- TABLE: referral_earnings
-- Extended version with task_type and referral_username
-- Tracks all earnings from referrals for audit and stats
-- ============================================================================
CREATE TABLE IF NOT EXISTS referral_earnings (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,                       -- User who referred (earned commission)
    referral_id BIGINT NOT NULL,                       -- User who was referred
    amount INTEGER NOT NULL,                           -- Commission earned (in rubles)
    task_assignment_id INTEGER,
    task_type VARCHAR(20) CHECK (task_type IN ('simple', 'phone')),  -- Data integrity constraint
    referral_username VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (referrer_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (referral_id) REFERENCES users(telegram_id) ON DELETE CASCADE,
    FOREIGN KEY (task_assignment_id) REFERENCES task_assignments(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_referral_earnings_referrer_id ON referral_earnings(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referral_earnings_referral_id ON referral_earnings(referral_id);
CREATE INDEX IF NOT EXISTS idx_referral_earnings_created_at ON referral_earnings(created_at);
CREATE INDEX IF NOT EXISTS idx_referral_earnings_task_assignment_id ON referral_earnings(task_assignment_id);
CREATE INDEX IF NOT EXISTS idx_referral_earnings_task_type ON referral_earnings(task_type);  -- For stats queries

-- ============================================================================
-- SUMMARY OF TABLES
-- ============================================================================
-- 1. users: User accounts and balances
-- 2. tasks: Available tasks (CRUD by admin)
-- 3. task_assignments: User-task relationships with status tracking
-- 4. screenshots: File uploads for task submissions (many-to-one with task_assignments)
-- 5. withdrawals: Payout requests and history
-- 6. referral_earnings: Referral commission tracking (extended with metadata)
-- ============================================================================
