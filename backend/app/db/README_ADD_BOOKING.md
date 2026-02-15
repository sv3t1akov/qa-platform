# Добавление Booking T1 миссий в базу данных

## Вариант 1: Через Fly Proxy (если backend не запущен)

### Шаг 1: Получите DATABASE_URL из Fly Dashboard

1. Откройте [Fly Dashboard](https://fly.io/dashboard)
2. Перейдите в ваше Postgres приложение (например, `qa-platform-db`)
3. Найдите раздел "Connection" или "Connection string"
4. Скопируйте строку подключения, она выглядит примерно так:
   ```
   postgresql://user:password@qa-platform-db.flycast:5432/dbname
   ```

### Шаг 2: Создайте туннель к БД

**Терминал 1** (оставьте открытым):
```bash
cd backend/app/db
./add_booking_via_proxy.sh
```

Или вручную:
```bash
fly proxy 5432 -a qa-platform-db
```

### Шаг 3: Выполните скрипт

**Терминал 2** (новый терминал):
```bash
# Замените хост в DATABASE_URL на localhost:5432
# Например, если было: postgresql://user:pass@qa-platform-db.flycast:5432/dbname
# Станет: postgresql://user:pass@localhost:5432/dbname

export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

cd backend/app/db
python3 add_booking_t1.py
```

---

## Вариант 2: Запустить backend и использовать SSH

Если backend не запущен, сначала запустите его:

```bash
# Запустить backend
fly apps start qa-platform-backend

# Подождите пока он запустится (проверьте статус)
fly status -a qa-platform-backend

# Затем выполните через SSH
cd backend/app/db
./add_booking_via_ssh.sh
```

---

## Вариант 3: Через Fly Postgres Connect (если установлен)

Если у вас установлен `fly postgres connect`:

```bash
# Подключиться к БД
fly postgres connect -a qa-platform-db

# Внутри psql выполните:
\i /path/to/seed_booking_t1_missions.sql
\i /path/to/seed_booking_t1_bugs.sql
```

---

## Проверка результата

После выполнения любого из вариантов проверьте:

```bash
# Через Python (если есть доступ к БД)
cd backend
export DATABASE_URL="postgresql://..."
python3 -c "
import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(\"SELECT COUNT(*) FROM missions WHERE domain_id = 'booking'\"))
        print(f'Миссий для Booking: {result.scalar()}')
        result = await session.execute(text(\"SELECT COUNT(*) FROM bugs WHERE mission_id LIKE 'book-t1-%'\"))
        print(f'Багов для Booking T1: {result.scalar()}')

asyncio.run(check())
"
```

Ожидаемый результат:
- Миссий для Booking: **4**
- Багов для Booking T1: **13**

---

## Где найти DATABASE_URL?

1. **Fly Dashboard** → Ваше Postgres приложение → Connection string
2. **Или из конфигурации**, где вы устанавливали секрет:
   ```bash
   fly secrets set DATABASE_URL="postgresql://..." -a qa-platform-backend
   ```
