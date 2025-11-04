import type { User, Withdrawal } from '../types';

export const mockUser: User = {
  telegram_id: 123456789,
  username: 'demo_user',
  first_name: 'Demo',
  main_balance: 3500,
  referral_balance: 1500,
  referred_by: null,
  created_at: new Date().toISOString(),
};

export const mockPendingWithdrawal: Withdrawal = {
  id: 1,
  user_id: 123456789,
  amount: 1000,
  method: 'card',
  details: {
    card_number: '1234 **** **** 5678',
    cardholder_name: 'Demo User',
  },
  status: 'pending',
  created_at: new Date().toISOString(),
  processed_at: null,
};
