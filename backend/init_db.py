#!/usr/bin/env python3
# backend/init_db.py
"""
Database initialization script.
Creates tables from schema.sql and validates setup.

Usage:
    python init_db.py
"""

import asyncpg
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def init_database():
    """Create database tables from schema.sql."""

    dsn = (
        f"postgresql://{os.getenv('DATABASE_USER')}:"
        f"{os.getenv('DATABASE_PASSWORD')}@"
        f"{os.getenv('DATABASE_HOST')}:"
        f"{os.getenv('DATABASE_PORT')}/"
        f"{os.getenv('DATABASE_NAME')}"
    )

    try:
        # Connect to database
        print(f"Connecting to {os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}...")
        connection = await asyncpg.connect(dsn)
        print("✅ Connected successfully!")

        # Read schema.sql
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            print(f"❌ Error: schema.sql not found at {schema_path}")
            return False

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()

        print(f"Executing schema from {schema_path}...")

        # Execute schema (all statements)
        await connection.execute(schema)

        print("✅ Database tables created successfully!")

        # Validate tables exist
        tables = await connection.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        expected_tables = {
            'users',
            'tasks',
            'task_assignments',
            'screenshots',
            'withdrawals',
            'referral_earnings'
        }

        existing_tables = {row['tablename'] for row in tables}

        print("\n📋 Created tables:")
        for table in sorted(existing_tables):
            status = "✅" if table in expected_tables else "⚠️"
            print(f"  {status} {table}")

        missing = expected_tables - existing_tables
        if missing:
            print(f"\n❌ Warning: Missing tables: {missing}")
            return False

        print("\n✅ All expected tables created!")

        # Show table schemas
        print("\n" + "=" * 80)
        print("TABLE SCHEMAS")
        print("=" * 80 + "\n")

        for table in sorted(expected_tables):
            columns = await connection.fetch(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """)

            print(f"📊 {table}:")
            for col in columns:
                null_str = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"   - {col['column_name']}: {col['data_type']} {null_str}")
            print()

        # Show indexes
        print("=" * 80)
        print("INDEXES")
        print("=" * 80 + "\n")

        indexes = await connection.fetch("""
            SELECT tablename, indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)

        current_table = None
        for idx in indexes:
            if idx['tablename'] != current_table:
                current_table = idx['tablename']
                print(f"📊 {current_table}:")
            print(f"   - {idx['indexname']}")

        await connection.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("AVITO TASKER - DATABASE INITIALIZATION")
    print("=" * 80 + "\n")

    success = await init_database()

    print("\n" + "=" * 80)
    if success:
        print("✅ Database initialization completed successfully!")
        print("=" * 80 + "\n")
        exit(0)
    else:
        print("❌ Database initialization failed!")
        print("=" * 80 + "\n")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
