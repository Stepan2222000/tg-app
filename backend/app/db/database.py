# backend/app/db/database.py
"""
AsyncPG database connection pool and helper functions.
Uses connection pool for better performance (no ORM).
"""

import asyncpg
import asyncio
import os
from typing import Any, List, Optional, Dict, AsyncIterator
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

__all__ = ['Database', 'db']


class Database:
    """Database connection pool manager using asyncpg."""

    def __init__(self) -> None:
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Initialize connection pool."""
        try:
            # Build DSN from environment variables (loaded by config.py)
            dsn = (
                f"postgresql://{os.getenv('DATABASE_USER')}:"
                f"{os.getenv('DATABASE_PASSWORD')}@"
                f"{os.getenv('DATABASE_HOST')}:"
                f"{os.getenv('DATABASE_PORT')}/"
                f"{os.getenv('DATABASE_NAME')}"
            )

            self.pool = await asyncpg.create_pool(
                dsn,
                min_size=5,
                max_size=20,
                command_timeout=60,
                timeout=30
            )
            logger.info("Database pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[asyncpg.Connection]:
        """
        Get connection from pool (context manager).

        Raises:
            RuntimeError: If database pool is not initialized
            RuntimeError: If connection pool is exhausted or timeout occurs
        """
        if not self.pool:
            raise RuntimeError("Database not connected. Call db.connect() first.")

        try:
            async with self.pool.acquire() as connection:
                yield connection
        except asyncio.TimeoutError:
            logger.error("Failed to acquire connection: pool exhausted or timeout")
            raise RuntimeError("Database connection pool exhausted. Try again later.")
        except Exception as e:
            logger.error(f"Failed to acquire connection: {e}")
            raise

    # ========================================================================
    # EXECUTE - For INSERT, UPDATE, DELETE (returns affected rows count)
    # ========================================================================

    async def execute(
        self,
        query: str,
        *args: Any
    ) -> str:
        """
        Execute query without returning results (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query with $1, $2 placeholders
            *args: Query parameters

        Returns:
            Query result (e.g., "INSERT 0 1")

        Example:
            await db.execute(
                "UPDATE users SET main_balance = main_balance + $1 WHERE telegram_id = $2",
                100,
                12345
            )
        """
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)

    # ========================================================================
    # FETCH_ONE - For SELECT (returns single row as dict or None)
    # ========================================================================

    async def fetch_one(
        self,
        query: str,
        *args: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch single row from database.

        Args:
            query: SQL query with $1, $2 placeholders
            *args: Query parameters

        Returns:
            Dict with column names as keys, or None if no rows

        Example:
            user = await db.fetch_one(
                "SELECT * FROM users WHERE telegram_id = $1",
                12345
            )
        """
        async with self.get_connection() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    # ========================================================================
    # FETCH_ALL - For SELECT (returns list of dicts)
    # ========================================================================

    async def fetch_all(
        self,
        query: str,
        *args: Any
    ) -> List[Dict[str, Any]]:
        """
        Fetch all rows from database.

        Args:
            query: SQL query with $1, $2 placeholders
            *args: Query parameters

        Returns:
            List of dicts with column names as keys

        Example:
            tasks = await db.fetch_all(
                "SELECT * FROM tasks WHERE is_available = $1 ORDER BY created_at DESC",
                True
            )
        """
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    # ========================================================================
    # FETCH_VAL - For SELECT with single value (e.g., COUNT, SUM)
    # ========================================================================

    async def fetch_val(
        self,
        query: str,
        *args: Any
    ) -> Any:
        """
        Fetch single scalar value from database.

        Args:
            query: SQL query with $1, $2 placeholders
            *args: Query parameters

        Returns:
            Single value or None

        Example:
            count = await db.fetch_val(
                "SELECT COUNT(*) FROM task_assignments WHERE user_id = $1 AND status = 'assigned'",
                12345
            )
        """
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)

    # ========================================================================
    # TRANSACTION - For multi-step operations (atomic)
    # ========================================================================

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        """
        Context manager for database transactions.
        Ensures atomicity for multi-step operations.

        IMPORTANT: Inside the transaction block, use the connection directly
        with conn.execute(), conn.fetchrow(), etc., NOT db.execute().

        Yields:
            asyncpg.Connection: Database connection with active transaction

        Example:
            async with db.transaction() as conn:
                await conn.execute(
                    "UPDATE users SET main_balance = main_balance + $1 WHERE telegram_id = $2",
                    100, 12345
                )
                await conn.execute(
                    "INSERT INTO referral_earnings (...) VALUES (...)",
                    ...
                )
                # Both execute or both rollback on error
        """
        async with self.get_connection() as conn:
            transaction = conn.transaction()
            await transaction.start()
            try:
                yield conn
                await transaction.commit()
            except Exception as e:
                await transaction.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
                raise

    # ========================================================================
    # BULK OPERATIONS - For efficiency
    # ========================================================================

    async def executemany(
        self,
        query: str,
        args_list: List[tuple]
    ) -> None:
        """
        Execute same query multiple times with different parameters.

        Args:
            query: SQL query with $1, $2 placeholders
            args_list: List of parameter tuples

        Example:
            await db.executemany(
                "INSERT INTO tasks (type, avito_url, message_text, price) VALUES ($1, $2, $3, $4)",
                [
                    ('simple', 'https://...', 'text1', 50),
                    ('phone', 'https://...', 'text2', 150),
                ]
            )
        """
        async with self.get_connection() as conn:
            await conn.executemany(query, args_list)


# Global database instance
db = Database()
