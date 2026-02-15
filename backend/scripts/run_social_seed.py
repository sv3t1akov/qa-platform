#!/usr/bin/env python3
"""
Ручной запуск seed для Social T1.
Использование: DATABASE_URL=postgresql://... python scripts/run_social_seed.py
"""
import asyncio
import os
import sys

# Добавляем backend в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    from app.db.migrate import run_migration
    print("Running migrations (including Social T1 seed)...")
    await run_migration()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
