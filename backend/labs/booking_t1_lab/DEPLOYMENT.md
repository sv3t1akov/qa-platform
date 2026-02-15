# Booking T1 Lab - Deployment Guide

## Структура проекта

```
booking_t1_lab/
├── app/
│   ├── __init__.py
│   ├── main.py              # Основной файл с API и багами
│   └── flags_registry.py    # Реестр всех 13 флагов
├── Dockerfile
├── fly.toml
├── requirements.txt
├── README.md
└── DEPLOYMENT.md
```

## Локальный запуск

```bash
cd backend/labs/booking_t1_lab

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Сервер будет доступен по адресу: http://localhost:8080

## Деплой на Fly.io

```bash
cd backend/labs/booking_t1_lab

# Логин в Fly.io (если еще не залогинены)
fly auth login

# Деплой
fly deploy
```

После деплоя приложение будет доступно по адресу: https://qa-lab-booking-t1.fly.dev

## Добавление в базу данных

После деплоя лабы необходимо добавить миссии и баги в базу данных платформы:

```bash
cd backend/app/db

# Выполнить seed файлы для Booking T1
psql -d qa_platform -f seed_booking_t1_missions.sql
psql -d qa_platform -f seed_booking_t1_bugs.sql
```

Или через psql напрямую:

```sql
\i seed_booking_t1_missions.sql
\i seed_booking_t1_bugs.sql
```

## Проверка работоспособности

После деплоя проверьте:

1. Health check: `GET https://qa-lab-booking-t1.fly.dev/health`
   - Должен вернуть: `{"status": "healthy", "mission": "booking-t1-lab", "bugs": 13}`

2. Проверка эндпоинтов:
   - `GET /api/v1/properties` - список отелей
   - `GET /api/v1/properties/1` - детали отеля
   - `GET /api/v1/rooms/1` - детали номера

## Тестирование багов

Для тестирования багов используйте примеры из `BOOKING_T1_SPEC_v2.md`:

### Mission 1: Properties & Rooms
- `GET /api/v1/properties/-1` → NEGATIVE_ID
- `GET /api/v1/rooms/99999999999999999` → BOUNDARY_OVERFLOW
- `GET /api/v1/rooms/42` → HIDDEN_FIELDS

### Mission 2: Availability
- `GET /api/v1/rooms/1/availability?checkIn=2020-01-15&checkOut=2020-01-18` → DATE_PAST
- `GET /api/v1/rooms/1/availability?checkIn=2026-03-20&checkOut=2026-03-15` → DATE_REVERSED
- `GET /api/v1/rooms/1/availability?checkIn=2026-03-15&checkOut=2026-03-15` → ZERO_DURATION
- `GET /api/v1/rooms/1/availability?checkIn=2026-03-15&checkOut=2026-03-18&adults=50` → CAPACITY_EXCEEDED

### Mission 3: Bookings
- `POST /api/v1/bookings` с `roomId: ""` → MISSING_REQUIRED
- `POST /api/v1/bookings` с `totalPrice: 1` → PRICE_OVERRIDE
- `POST /api/v1/bookings` с `guests: {"adults": -5}` → WRONG_STATUS_CODE
- `GET /api/v1/bookings/book-2026-00050` (как guest_alice) → IDOR_ACCESS

### Mission 4: Guest Profile
- `PUT /api/v1/guests/me` с `firstName: 12345` → TYPE_COERCION
- `PUT /api/v1/guests/me` с `email: "not-an-email"` → INVALID_FORMAT

## Переменные окружения

- `PORT` - порт сервера (по умолчанию 8080)
- `MISSION_ID` - ID миссии (по умолчанию "booking-t1-lab")
- `DEBUG_MODE` - режим отладки (по умолчанию "true")

## Структура багов

Всего 13 активных багов:
- Mission 1: 3 бага
- Mission 2: 4 бага
- Mission 3: 4 бага
- Mission 4: 2 бага

Все флаги соответствуют спецификации `BOOKING_T1_SPEC_v2.md`.
