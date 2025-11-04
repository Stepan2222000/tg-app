#!/usr/bin/env python3
# backend/add_test_tasks.py
"""
Add test tasks to database.
Inserts 4 test tasks from tech-stack.md into the tasks table.

Usage:
    python add_test_tasks.py
"""

import asyncpg
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def add_test_tasks():
    """Add 4 test tasks to the database."""

    dsn = (
        f"postgresql://{os.getenv('DATABASE_USER')}:"
        f"{os.getenv('DATABASE_PASSWORD')}@"
        f"{os.getenv('DATABASE_HOST')}:"
        f"{os.getenv('DATABASE_PORT')}/"
        f"{os.getenv('DATABASE_NAME')}"
    )

    # Get prices from environment
    simple_task_price = int(os.getenv('SIMPLE_TASK_PRICE', '50'))
    phone_task_price = int(os.getenv('PHONE_TASK_PRICE', '150'))

    # Define test tasks from tech-stack.md
    test_tasks = [
        {
            "type": "simple",
            "avito_url": "https://www.avito.ru/brands/82268a835092c9677ebe7278a13a866d",
            "message_text": "добрый вечер, я диспетчер",
            "price": simple_task_price
        },
        {
            "type": "simple",
            "avito_url": "https://www.avito.ru/brands/fc6076e06d696884d07f26a4828dc6e3",
            "message_text": "друг мой, здравствуй",
            "price": simple_task_price
        },
        {
            "type": "phone",
            "avito_url": "https://www.avito.ru/brands/94b135edb89761f77fdfab2f5a82a345",
            "message_text": "привет, отправь номер",
            "price": phone_task_price
        },
        {
            "type": "phone",
            "avito_url": "https://www.avito.ru/brands/16f6fd2b4f11b60a3ec2ab2084d34bf6",
            "message_text": "hello, you good boy",
            "price": phone_task_price
        }
    ]

    connection = None  # CRITICAL-4 FIX: Initialize to None for finally block
    try:
        # Connect to database
        print(f"Connecting to {os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}...")
        connection = await asyncpg.connect(dsn)
        print("✅ Connected successfully!")

        # Check how many tasks already exist
        existing_count = await connection.fetchval("SELECT COUNT(*) FROM tasks")
        print(f"📊 Current tasks in database: {existing_count}")

        # Insert test tasks
        added_count = 0
        for i, task in enumerate(test_tasks, 1):
            try:
                # Check if task with this URL already exists
                existing = await connection.fetchval(
                    "SELECT id FROM tasks WHERE avito_url = $1",
                    task["avito_url"]
                )

                if existing:
                    print(f"⏭️  Task #{i} already exists (ID: {existing}), skipping...")
                    continue

                # Insert task
                task_id = await connection.fetchval(
                    """
                    INSERT INTO tasks (type, avito_url, message_text, price, is_available)
                    VALUES ($1, $2, $3, $4, TRUE)
                    RETURNING id
                    """,
                    task["type"],
                    task["avito_url"],
                    task["message_text"],
                    task["price"]
                )

                print(f"✅ Task #{i} added successfully (ID: {task_id})")
                print(f"   Type: {task['type']}")
                print(f"   URL: {task['avito_url']}")
                print(f"   Message: {task['message_text']}")
                print(f"   Price: ₽{task['price']}")
                print()

                added_count += 1

            except Exception as e:
                print(f"❌ Error adding task #{i}: {e}")

        # Final count
        final_count = await connection.fetchval("SELECT COUNT(*) FROM tasks")
        print(f"📊 Final tasks in database: {final_count}")
        print(f"✅ Successfully added {added_count} new test tasks!")

        # Show summary
        print("\n" + "="*60)
        print("SUMMARY:")
        print(f"  - Simple tasks (₽{simple_task_price}): 2")
        print(f"  - Phone tasks (₽{phone_task_price}): 2")
        print(f"  - Total added: {added_count}")
        print("="*60)

        return True

    except asyncpg.PostgresError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # CRITICAL-4 FIX: Always close connection, even on error
        if connection:
            await connection.close()
            print("🔌 Database connection closed.")


if __name__ == "__main__":
    success = asyncio.run(add_test_tasks())
    if success:
        print("\n✅ Test tasks added successfully!")
        print("You can now test the application with these tasks.")
    else:
        print("\n❌ Failed to add test tasks.")
        print("Please check the error messages above.")

    exit(0 if success else 1)
