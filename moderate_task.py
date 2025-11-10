#!/usr/bin/env python3
"""
Interactive script for moderating tasks

Usage:
  python moderate_task.py          # Interactive mode
  python moderate_task.py list     # List pending tasks only
"""

import asyncio
import asyncpg
import sys


DB_DSN = "postgresql://admin:Password123@81.30.105.134:5416/avito_tasker"


async def get_pending_tasks(conn):
    """Get all pending tasks."""
    return await conn.fetch("""
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
        WHERE ta.status = 'submitted'
        ORDER BY ta.submitted_at ASC
    """)


async def get_task_info(conn, assignment_id: int):
    """Get task assignment details."""
    return await conn.fetchrow("""
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


def display_pending_tasks(tasks):
    """Display pending tasks in a nice table."""
    if not tasks:
        print("\n📭 Нет задач на модерации\n")
        return False

    print("\n" + "=" * 100)
    print(f"📋 ЗАДАЧИ НА МОДЕРАЦИИ ({len(tasks)} шт.)")
    print("=" * 100)
    print(f"{'ID':<6} {'Пользователь':<15} {'Тип':<10} {'Цена':<8} {'Скриншоты':<12} {'Отправлено':<20}")
    print("-" * 100)

    for task in tasks:
        submitted = task['submitted_at'].strftime('%Y-%m-%d %H:%M')
        ref_mark = " 🎁" if task['referred_by'] else ""
        print(f"{task['assignment_id']:<6} {task['username']:<15} {task['task_type']:<10} ₽{task['price']:<7} "
              f"{task['screenshot_count']:<12} {submitted:<20}{ref_mark}")

    print("=" * 100)
    print("🎁 = есть реферер (будет начислена комиссия 50%)\n")
    return True


async def moderate_one_task(conn, assignment_id: int, action: str):
    """Moderate a single task assignment."""

    task_info = await get_task_info(conn, assignment_id)

    if not task_info:
        print(f"  ⚠️  Задача #{assignment_id} не найдена или уже обработана")
        return False

    # Display task info
    print(f"  📋 Задача #{task_info['assignment_id']} - {task_info['username']} - {task_info['task_type']} - ₽{task_info['price']}", end="")

    # Perform action
    try:
        if action == 'approve':
            async with conn.transaction():
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

                # 2. Credit user's main balance (NO updated_at column in users table)
                await conn.execute(
                    "UPDATE users SET main_balance = main_balance + $1 WHERE telegram_id = $2",
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
                        "UPDATE users SET referral_balance = referral_balance + $1 WHERE telegram_id = $2",
                        commission, referrer_id
                    )

                    print(f" → ✅ Одобрено (₽{task_price} + ₽{commission} реферу)")
                else:
                    print(f" → ✅ Одобрено (₽{task_price})")

        elif action == 'reject':
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

                print(f" → ❌ Отклонено")

        return True

    except Exception as e:
        print(f" → ❌ Ошибка: {e}")
        return False


async def interactive_mode():
    """Run interactive moderation."""

    conn = await asyncpg.connect(DB_DSN)

    # Get pending tasks
    tasks = await get_pending_tasks(conn)

    # Display tasks
    has_tasks = display_pending_tasks(tasks)

    if not has_tasks:
        await conn.close()
        return

    # Ask for action
    print("Что вы хотите сделать?")
    print("  1 - Одобрить задачи")
    print("  2 - Отклонить задачи")
    print("  0 - Выход")
    print()

    choice = input("Ваш выбор (1/2/0): ").strip()

    if choice == '0':
        print("\n👋 До свидания!\n")
        await conn.close()
        return

    if choice not in ['1', '2']:
        print("\n❌ Неверный выбор\n")
        await conn.close()
        return

    action = 'approve' if choice == '1' else 'reject'
    action_name = 'одобрить' if choice == '1' else 'отклонить'

    # Ask for task IDs
    print(f"\nВведите ID задач для {action_name} (через пробел) или 'all' для всех:")
    ids_input = input("ID задач: ").strip()

    if not ids_input:
        print("\n❌ Не указаны ID задач\n")
        await conn.close()
        return

    # Parse IDs
    if ids_input.lower() == 'all':
        assignment_ids = [task['assignment_id'] for task in tasks]
        print(f"\n🔄 {action_name.capitalize()} ВСЕ задачи ({len(assignment_ids)} шт.)...")
    else:
        try:
            assignment_ids = [int(x.strip()) for x in ids_input.split()]
        except ValueError:
            print("\n❌ Неверный формат ID\n")
            await conn.close()
            return

    if not assignment_ids:
        print("\n❌ Не указаны ID задач\n")
        await conn.close()
        return

    # Confirm
    print(f"\n⚠️  Вы уверены, что хотите {action_name} {len(assignment_ids)} задач(и)?")
    confirm = input("Подтвердить? (да/y): ").strip().lower()

    if confirm not in ['да', 'y', 'yes', 'д']:
        print("\n❌ Отменено\n")
        await conn.close()
        return

    # Moderate tasks
    print("\n" + "=" * 80)
    print(f"{'ОДОБРЕНИЕ' if action == 'approve' else 'ОТКЛОНЕНИЕ'} ЗАДАЧ")
    print("=" * 80)

    success_count = 0
    fail_count = 0

    for assignment_id in assignment_ids:
        result = await moderate_one_task(conn, assignment_id, action)
        if result:
            success_count += 1
        else:
            fail_count += 1

    await conn.close()

    print("\n" + "=" * 80)
    print(f"✅ Успешно: {success_count} | ❌ Ошибок: {fail_count}")
    print("=" * 80)
    print()


async def list_mode():
    """Just list pending tasks."""
    conn = await asyncpg.connect(DB_DSN)
    tasks = await get_pending_tasks(conn)
    display_pending_tasks(tasks)
    await conn.close()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        asyncio.run(list_mode())
    else:
        asyncio.run(interactive_mode())


if __name__ == '__main__':
    main()
