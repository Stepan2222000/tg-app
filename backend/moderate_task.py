#!/usr/bin/env python3
"""
Script for moderating tasks (approve or reject)
Usage: python3 moderate_task.py <assignment_id> [approve|reject]
"""

import asyncio
import asyncpg
import sys


async def moderate_task(assignment_id: int, action: str):
    """Moderate a task assignment."""

    dsn = "postgresql://admin:Password123@81.30.105.134:5416/avito_tasker"

    try:
        conn = await asyncpg.connect(dsn)

        # Get task details
        task_info = await conn.fetchrow("""
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
                u.referred_by,
                (SELECT username FROM users WHERE telegram_id = u.referred_by) as referrer_username,
                (SELECT COUNT(*) FROM screenshots WHERE assignment_id = ta.id) as screenshot_count
            FROM task_assignments ta
            JOIN users u ON u.telegram_id = ta.user_id
            JOIN tasks t ON t.id = ta.task_id
            WHERE ta.id = $1 AND ta.status = 'submitted'
        """, assignment_id)

        if not task_info:
            print(f"❌ Task assignment #{assignment_id} not found or not in 'submitted' status")
            await conn.close()
            return False

        # Display task info
        print("=" * 70)
        print("📋 Task Assignment Details")
        print("=" * 70)
        print(f"Assignment ID:    {task_info['assignment_id']}")
        print(f"User:             {task_info['username']} ({task_info['first_name']})")
        print(f"User ID:          {task_info['user_id']}")
        print(f"Task Type:        {task_info['task_type']}")
        print(f"Price:            ₽{task_info['price']}")
        print(f"Screenshots:      {task_info['screenshot_count']}")
        print(f"Submitted:        {task_info['submitted_at']}")

        if task_info['referred_by']:
            referral_commission = round(task_info['price'] * 0.5)
            print(f"Referrer:         {task_info['referrer_username']} (will get ₽{referral_commission})")
        else:
            print(f"Referrer:         None")

        if task_info['phone_number']:
            print(f"Phone Number:     {task_info['phone_number']}")

        print("-" * 70)
        print(f"Avito URL:        {task_info['avito_url']}")
        print(f"Message:          {task_info['message_text'][:100]}...")
        print("=" * 70)

        # Get screenshot paths
        screenshots = await conn.fetch(
            "SELECT file_path FROM screenshots WHERE assignment_id = $1 ORDER BY uploaded_at",
            assignment_id
        )

        if screenshots:
            print("\n📸 Screenshots:")
            for i, shot in enumerate(screenshots, 1):
                filename = shot['file_path'].split('/')[-1]
                print(f"  {i}. http://localhost:8000/static/screenshots/{filename}")
                print(f"     File: {shot['file_path']}")

        print("\n" + "=" * 70)

        # Perform action
        if action == 'approve':
            print(f"✅ APPROVING task #{assignment_id}...")

            # Execute approval in transaction
            async with conn.transaction():
                # Get task details
                user_id = task_info['user_id']
                task_id = task_info['task_id']
                task_price = task_info['price']
                task_type = task_info['task_type']
                referrer_id = task_info['referred_by']

                # 1. Approve assignment
                await conn.execute(
                    "UPDATE task_assignments SET status = 'approved' WHERE id = $1",
                    assignment_id
                )

                # 2. Credit user's main balance
                await conn.execute(
                    "UPDATE users SET main_balance = main_balance + $1, updated_at = NOW() WHERE telegram_id = $2",
                    task_price, user_id
                )

                # 3. Return task to pool
                await conn.execute(
                    "UPDATE tasks SET is_available = TRUE, updated_at = NOW() WHERE id = $1",
                    task_id
                )

                # 4. If referrer exists, credit referral commission
                if referrer_id:
                    commission = round(task_price * 0.5)

                    await conn.execute("""
                        INSERT INTO referral_earnings (
                            referrer_id, referral_id, amount, task_assignment_id,
                            task_type, referral_username
                        )
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, referrer_id, user_id, commission, assignment_id,
                         task_type, task_info['username'])

                    await conn.execute(
                        "UPDATE users SET referral_balance = referral_balance + $1, updated_at = NOW() WHERE telegram_id = $2",
                        commission, referrer_id
                    )

                    print(f"   💰 Credited ₽{commission} referral commission to {task_info['referrer_username']}")

                print(f"   ✅ Task approved!")
                print(f"   💰 User {task_info['username']} credited ₽{task_price}")
                print(f"   🔄 Task returned to pool")

        elif action == 'reject':
            print(f"❌ REJECTING task #{assignment_id}...")

            async with conn.transaction():
                # 1. Reject assignment
                await conn.execute(
                    "UPDATE task_assignments SET status = 'rejected' WHERE id = $1",
                    assignment_id
                )

                # 2. Return task to pool
                await conn.execute(
                    "UPDATE tasks SET is_available = TRUE, updated_at = NOW() WHERE id = $1",
                    task_info['task_id']
                )

                print(f"   ❌ Task rejected")
                print(f"   🔄 Task returned to pool")
                print(f"   💾 Screenshots kept for review")

        await conn.close()
        print("\n✅ Done!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 moderate_task.py <assignment_id> [approve|reject]")
        print("")
        print("Examples:")
        print("  python3 moderate_task.py 15 approve")
        print("  python3 moderate_task.py 15 reject")
        sys.exit(1)

    try:
        assignment_id = int(sys.argv[1])
    except ValueError:
        print("❌ Error: assignment_id must be a number")
        sys.exit(1)

    action = sys.argv[2].lower()

    if action not in ['approve', 'reject']:
        print("❌ Error: action must be 'approve' or 'reject'")
        sys.exit(1)

    success = asyncio.run(moderate_task(assignment_id, action))
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
