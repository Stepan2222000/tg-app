#!/usr/bin/env python3
"""
Install moderation views to the database.
Run once to create all administrative views for easier moderation.
"""

import asyncio
import asyncpg
import os
import sys


async def install_views():
    """Read and execute the SQL file to create views."""

    # Database connection parameters
    dsn = (
        f"postgresql://admin:"
        f"Password123@"
        f"81.30.105.134:"
        f"5416/"
        f"avito_tasker"
    )

    # Read SQL file
    sql_file = os.path.join(os.path.dirname(__file__), 'create_moderation_views.sql')

    if not os.path.exists(sql_file):
        print(f"❌ Error: SQL file not found: {sql_file}")
        sys.exit(1)

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Connect and execute
    print("🔌 Connecting to database...")
    try:
        conn = await asyncpg.connect(dsn)
        print("✅ Connected successfully")

        print("📝 Creating moderation views...")
        # Split by semicolons and execute each statement
        # Filter out comments and empty statements
        statements = []
        current_statement = []
        in_comment = False

        for line in sql_content.split('\n'):
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Handle comment blocks
            if '/*' in stripped:
                in_comment = True
            if '*/' in stripped:
                in_comment = False
                continue
            if in_comment:
                continue

            # Skip single-line comments
            if stripped.startswith('--'):
                continue

            current_statement.append(line)

            # If line ends with semicolon, it's end of statement
            if stripped.endswith(';'):
                statement = '\n'.join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []

        # Execute each statement
        view_count = 0
        for i, statement in enumerate(statements, 1):
            try:
                await conn.execute(statement)
                # Extract view name if it's a CREATE VIEW statement
                if 'CREATE OR REPLACE VIEW' in statement:
                    view_name = statement.split('CREATE OR REPLACE VIEW')[1].split('AS')[0].strip()
                    print(f"  ✅ {view_name}")
                    view_count += 1
            except Exception as e:
                print(f"  ⚠️  Statement {i} warning: {e}")

        await conn.close()
        print(f"\n✅ Successfully created {view_count} moderation views!")

    except asyncpg.PostgresError as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(install_views())
