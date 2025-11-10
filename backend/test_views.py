#!/usr/bin/env python3
"""Quick test of moderation views"""

import asyncio
import asyncpg


async def test_views():
    dsn = "postgresql://admin:Password123@81.30.105.134:5416/avito_tasker"
    conn = await asyncpg.connect(dsn)

    print("=" * 60)
    print("Testing Moderation Views")
    print("=" * 60)
    print()

    # Test 1: Admin Dashboard
    print("📊 Admin Dashboard:")
    print("-" * 60)
    dashboard = await conn.fetchrow("SELECT * FROM v_admin_dashboard")
    if dashboard:
        for key, value in dashboard.items():
            print(f"  {key:30s} : {value}")
    print()

    # Test 2: Pending tasks
    print("📝 Pending Tasks:")
    print("-" * 60)
    tasks = await conn.fetch("SELECT assignment_id, username, task_type, price, hours_waiting, screenshot_count FROM v_pending_tasks LIMIT 5")
    if tasks:
        for task in tasks:
            print(f"  Assignment #{task['assignment_id']} | {task['username']} | {task['task_type']} | ₽{task['price']} | {task['hours_waiting']:.1f}h | {task['screenshot_count']} screenshots")
    else:
        print("  No pending tasks")
    print()

    # Test 3: Pending withdrawals
    print("💰 Pending Withdrawals:")
    print("-" * 60)
    withdrawals = await conn.fetch("SELECT withdrawal_id, username, amount, method, has_sufficient_balance FROM v_pending_withdrawals LIMIT 5")
    if withdrawals:
        for w in withdrawals:
            balance_ok = "✅" if w['has_sufficient_balance'] else "❌"
            print(f"  Withdrawal #{w['withdrawal_id']} | {w['username']} | ₽{w['amount']} | {w['method']} | {balance_ok}")
    else:
        print("  No pending withdrawals")
    print()

    # Test 4: User stats (top 3 users by balance)
    print("👥 Top Users by Balance:")
    print("-" * 60)
    users = await conn.fetch("SELECT username, total_balance, approved_tasks, total_referrals FROM v_user_stats ORDER BY total_balance DESC LIMIT 3")
    if users:
        for user in users:
            print(f"  {user['username']:20s} | ₽{user['total_balance']:6d} | {user['approved_tasks']:3d} tasks | {user['total_referrals']:3d} referrals")
    else:
        print("  No users yet")
    print()

    # Test 5: Recent activity
    print("🔥 Recent Activity (last 10):")
    print("-" * 60)
    activity = await conn.fetch("SELECT activity_type, username, amount, activity_time FROM v_recent_activity LIMIT 10")
    if activity:
        for act in activity:
            time_str = act['activity_time'].strftime('%Y-%m-%d %H:%M')
            print(f"  {time_str} | {act['activity_type']:20s} | {act['username']:15s} | ₽{act['amount']}")
    else:
        print("  No recent activity")
    print()

    await conn.close()

    print("=" * 60)
    print("✅ All views are working correctly!")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test_views())
