#!/usr/bin/env python3
"""
Скрипт для добавления Booking T1 миссий и багов в базу данных
Использует SQLAlchemy async, как и основной backend
"""
import asyncio
import os
import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from app.db.session import engine, AsyncSessionLocal

async def execute_sql_file(file_path: str):
    """Выполнить SQL файл"""
    file_path = Path(__file__).parent / file_path
    if not file_path.exists():
        print(f"❌ Файл {file_path} не найден!")
        return False
    
    print(f"📄 Выполняю {file_path.name}...")
    
    try:
        async with AsyncSessionLocal() as session:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Выполняем SQL
            await session.execute(text(sql_content))
            await session.commit()
            print(f"✅ {file_path.name} выполнен успешно")
            return True
    except Exception as e:
        print(f"❌ Ошибка при выполнении {file_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_results():
    """Проверить результаты добавления"""
    try:
        async with AsyncSessionLocal() as session:
            # Проверка миссий
            result = await session.execute(
                text("SELECT COUNT(*) FROM missions WHERE domain_id = 'booking'")
            )
            missions_count = result.scalar()
            
            # Проверка багов
            result = await session.execute(
                text("SELECT COUNT(*) FROM bugs WHERE mission_id LIKE 'book-t1-%'")
            )
            bugs_count = result.scalar()
            
            print(f"\n📊 Результаты:")
            print(f"   Миссий для Booking: {missions_count}")
            print(f"   Багов для Booking T1: {bugs_count}")
            
            return missions_count > 0 and bugs_count > 0
    except Exception as e:
        print(f"❌ Ошибка при проверке результатов: {e}")
        return False

async def main():
    """Основная функция"""
    print("=" * 50)
    print("📦 Добавление Booking T1 миссий в базу данных")
    print("=" * 50)
    
    # Проверка DATABASE_URL
    if not os.getenv("DATABASE_URL"):
        print("❌ Ошибка: DATABASE_URL не установлен!")
        print("   Установите переменную окружения:")
        print("   export DATABASE_URL='postgresql://user:password@host:port/dbname'")
        sys.exit(1)
    
    if not engine:
        print("❌ Ошибка: Не удалось подключиться к базе данных!")
        print("   Проверьте DATABASE_URL")
        sys.exit(1)
    
    print(f"✅ Подключение к БД установлено")
    
    # Выполнение seed файлов
    success = True
    
    success &= await execute_sql_file("seed_booking_t1_missions.sql")
    success &= await execute_sql_file("seed_booking_t1_bugs.sql")
    
    if not success:
        print("\n❌ Произошли ошибки при добавлении данных")
        sys.exit(1)
    
    # Проверка результатов
    if await check_results():
        print("\n" + "=" * 50)
        print("🎉 Booking T1 миссии успешно добавлены!")
        print("=" * 50)
    else:
        print("\n⚠️ Данные добавлены, но проверка не прошла")
        print("   Проверьте логи выше для деталей")

if __name__ == "__main__":
    asyncio.run(main())
