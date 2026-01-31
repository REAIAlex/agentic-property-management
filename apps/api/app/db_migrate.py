"""Simple migration runner - executes SQL migration files against the database."""
import asyncio
import os
from pathlib import Path

import asyncpg
from app.config import settings


async def run_migrations():
    # Convert async SQLAlchemy URL to asyncpg format
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(db_url)
    migrations_dir = Path(__file__).parent.parent.parent.parent / "db" / "migrations"

    migration_files = sorted(migrations_dir.glob("*.sql"))
    for migration_file in migration_files:
        print(f"Running migration: {migration_file.name}")
        sql = migration_file.read_text()
        try:
            await conn.execute(sql)
            print(f"  Completed: {migration_file.name}")
        except Exception as e:
            print(f"  Error in {migration_file.name}: {e}")
            # Continue with other migrations - some may already be applied

    await conn.close()
    print("Migrations complete.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
