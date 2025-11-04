import type { ReferralStats } from '../types';

export const mockReferralStats: ReferralStats = {
  total_referrals: 12,
  total_earnings: 1250,
  referrals: [
    {
      telegram_id: 87654321,
      username: 'alice_wonder',
      simple_tasks: 15,
      phone_tasks: 5,
      earnings: 435,
    },
    {
      telegram_id: 55555555,
      username: 'bob_builder',
      simple_tasks: 10,
      phone_tasks: 3,
      earnings: 300,
    },
    {
      telegram_id: 12345678,
      username: 'john_doe',
      simple_tasks: 8,
      phone_tasks: 2,
      earnings: 250,
    },
    {
      telegram_id: 98765432,
      simple_tasks: 4,
      phone_tasks: 1,
      earnings: 115,
    },
    {
      telegram_id: 99999999,
      simple_tasks: 6,
      phone_tasks: 1,
      earnings: 100,
    },
    {
      telegram_id: 11111111,
      username: 'crypto_king',
      simple_tasks: 2,
      phone_tasks: 0,
      earnings: 50,
    },
  ],
};
