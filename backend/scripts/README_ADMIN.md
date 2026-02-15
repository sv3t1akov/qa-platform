# Выдача админских прав пользователю

## Описание

Скрипт `make_admin.py` выдает админские права указанному пользователю и открывает доступ ко всем заданиям, добавляя все найденные флаги.

## Использование

### Локальная разработка

```bash
cd backend
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
python scripts/make_admin.py alexandrsvet@gmail.com
```

### Продакшн (Fly.io)

```bash
cd backend
fly ssh console -a qa-platform-backend
export DATABASE_URL="$(fly secrets list | grep DATABASE_URL | awk '{print $2}')"
python scripts/make_admin.py alexandrsvet@gmail.com
```

Или через fly ssh exec:

```bash
cd backend
fly ssh exec -a qa-platform-backend -- python scripts/make_admin.py alexandrsvet@gmail.com
```

## Что делает скрипт

1. Находит пользователя по email
2. Устанавливает роль `admin`
3. Добавляет все найденные флаги для всех багов во всех миссиях
4. Это гарантирует:
   - Прогресс 100% по всем тирам
   - Все тиры разблокированы
   - Доступ ко всем заданиям

## Изменения в коде

После выполнения скрипта, админы автоматически получают доступ ко всем заданиям благодаря обновленной логике в `app/api/missions.py`:

- Функция `_check_tier_unlocked` проверяет роль и всегда возвращает `True` для админов
- В `get_domain_missions` все тиры автоматически разблокированы для админов
- В `get_mission` проверка доступа пропускается для админов
