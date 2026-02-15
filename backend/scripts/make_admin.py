#!/usr/bin/env python3
"""
Скрипт для выдачи админских прав пользователю и открытия доступа ко всем заданиям
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию backend в путь
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, update
from app.db.session import AsyncSessionLocal, engine
from app.models.user import User, UserRole
from app.models.mission import Mission, Bug, UserFoundFlag
from datetime import datetime
import uuid


async def make_admin_and_unlock_all(email: str):
    """Выдает админские права пользователю и открывает доступ ко всем заданиям"""
    async with AsyncSessionLocal() as db:
        try:
            # Найти пользователя по email
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ Пользователь с email {email} не найден")
                return False
            
            print(f"✅ Найден пользователь: {user.email} (ID: {user.id})")
            print(f"   Текущая роль: {user.role.value}")
            
            # Установить роль admin
            if user.role != UserRole.admin:
                user.role = UserRole.admin
                await db.commit()
                print(f"✅ Роль изменена на: admin")
            else:
                print(f"ℹ️  Пользователь уже имеет роль admin")
            
            # Получить все миссии
            missions_result = await db.execute(select(Mission))
            all_missions = missions_result.scalars().all()
            print(f"✅ Найдено миссий: {len(all_missions)}")
            
            # Получить все баги для всех миссий
            bugs_result = await db.execute(select(Bug))
            all_bugs = bugs_result.scalars().all()
            print(f"✅ Найдено багов: {len(all_bugs)}")
            
            # Получить уже найденные флаги пользователя
            found_flags_result = await db.execute(
                select(UserFoundFlag.bug_id).where(UserFoundFlag.user_id == user.id)
            )
            found_bug_ids = {row[0] for row in found_flags_result.all()}
            print(f"✅ Уже найдено флагов: {len(found_bug_ids)}")
            
            # Добавить все недостающие флаги (чтобы прогресс был 100% и все тиры разблокированы)
            new_flags_count = 0
            for bug in all_bugs:
                if bug.id not in found_bug_ids:
                    new_flag = UserFoundFlag(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        bug_id=bug.id,
                        found_at=datetime.utcnow()
                    )
                    db.add(new_flag)
                    new_flags_count += 1
            
            if new_flags_count > 0:
                await db.commit()
                print(f"✅ Добавлено новых флагов: {new_flags_count}")
            else:
                print(f"ℹ️  Все флаги уже найдены")
            
            print(f"\n✅ Готово! Пользователь {email} теперь имеет:")
            print(f"   - Роль: admin")
            print(f"   - Найдено флагов: {len(found_bug_ids) + new_flags_count} из {len(all_bugs)}")
            print(f"   - Доступ ко всем заданиям открыт")
            
            return True
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    email = "alexandrsvet@gmail.com"
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    print(f"🔧 Выдача админских прав пользователю: {email}\n")
    
    success = await make_admin_and_unlock_all(email)
    
    if success:
        print("\n✅ Операция завершена успешно!")
        sys.exit(0)
    else:
        print("\n❌ Операция завершена с ошибками")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
