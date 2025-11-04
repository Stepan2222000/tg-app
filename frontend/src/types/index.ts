// User types
export interface User {
  telegram_id: number;
  username: string | null;
  first_name: string;
  main_balance: number;
  referral_balance: number;
  referred_by: number | null;
  created_at: string;
}

// Task types
export type TaskType = 'simple' | 'phone';

export interface Task {
  id: number;
  type: TaskType;
  avito_url: string;
  message_text: string;
  price: number;
  is_available: boolean;
  created_at: string;
  updated_at: string;
}

// Task Assignment types
export type TaskAssignmentStatus = 'assigned' | 'submitted' | 'approved' | 'rejected';

export interface TaskAssignment {
  id: number;
  task_id: number;
  user_id: number;
  status: TaskAssignmentStatus;
  deadline: string;
  phone_number: string | null;
  screenshots: string[];
  assigned_at: string;
  submitted_at: string | null;
  created_at: string;
  task?: Task; // Populated task data
}

// Withdrawal types
export type WithdrawalMethod = 'card' | 'sbp';
export type WithdrawalStatus = 'pending' | 'approved' | 'rejected';

export interface WithdrawalDetails {
  // For card
  card_number?: string;
  cardholder_name?: string;
  // For SBP
  bank_name?: string;
  phone_number?: string;
}

export interface Withdrawal {
  id: number;
  user_id: number;
  amount: number;
  method: WithdrawalMethod;
  details: WithdrawalDetails;
  status: WithdrawalStatus;
  created_at: string;
  processed_at: string | null;
}

// Referral types
export interface Referral {
  telegram_id: number;
  username?: string;
  simple_tasks: number;
  phone_tasks: number;
  earnings: number;
}

export interface ReferralStats {
  total_referrals: number;
  total_earnings: number;
  referrals: Referral[];
}

// Config types
export interface Config {
  simple_task_price: number;
  phone_task_price: number;
  min_withdrawal: number;
  max_active_tasks: number;
  instructions: string;
  // NEW-CRITICAL-E FIX: These fields removed from public API
  // (kept optional for backwards compatibility with mocks)
  referral_commission?: number;
  task_lock_hours?: number;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
