# QA Training Platform - Backend

Backend API для существующего фронтенда QA Training Platform.

## 📁 Структура

```
qa-backend/
├── app/
│   └── main.py              # FastAPI backend
├── labs/
│   └── ecommerce_return_refund_lab/  # E-Commerce лаба
├── Dockerfile
├── fly.toml                 # Конфиг для деплоя backend
├── docker-compose.yml       # Локальная разработка
└── requirements.txt
```

## 🚀 Деплой на Fly.io

### Шаг 1: Деплой лабораторий

```bash
# Установить Fly CLI (если ещё не установлен)
curl -L https://fly.io/install.sh | sh

# Авторизоваться
fly auth login

# Деплой E-Commerce лабы
cd labs/ecommerce_return_refund_lab
fly deploy

# Проверить что лаба запустилась
fly status
# URL: https://qa-lab-ecom-return-refund.fly.dev
```

### Шаг 2: Деплой Backend

```bash
cd ../..  # вернуться в корень qa-backend

# Деплой backend
fly deploy

# Проверить статус
fly status
# URL: https://qa-platform-backend.fly.dev
```

### Шаг 3: Настроить фронтенд

В настройках фронтенда указать URL бэкенда:
```
VITE_API_URL=https://qa-platform-backend.fly.dev
```

## 🧪 Локальная разработка

```bash
# Запуск всего стека (backend + lab)
docker-compose up --build

# Backend: http://localhost:8080
# Lab API: http://localhost:8081
# Lab Swagger: http://localhost:8081/docs
```

## 📡 API Endpoints

### Домены и миссии

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/domains` | Список доменов |
| GET | `/api/v1/domains/{id}` | Информация о домене |
| GET | `/api/v1/domains/{id}/missions` | Миссии домена |
| GET | `/api/v1/missions/{id}` | Детали миссии |

### Лаборатории

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/labs/start` | Запуск лабы |
| GET | `/api/v1/labs/{sessionId}` | Статус сессии |
| POST | `/api/v1/labs/{sessionId}/stop` | Остановка сессии |

### Флаги

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/flags/verify` | Проверка флага |
| GET | `/api/v1/users/me/flags` | Найденные флаги |
| GET | `/api/v1/users/me/stats` | Статистика пользователя |

## 🔬 Доступные лаборатории

### E-Commerce: Return & Refund Pipeline

| Параметр | Значение |
|----------|----------|
| ID | `ecom-return-refund` |
| Флагов | 12 |
| Баллов | 1750 |
| Сложность | T4-T5 (Advanced) |
| URL | https://qa-lab-ecom-return-refund.fly.dev |

**Флаги:**

| # | Название | Баллы |
|---|----------|-------|
| 1 | Return Window Bypass | 150 |
| 2 | Food Category Inconsistency | 100 |
| 3 | Discount Double Refund | 150 |
| 4 | Restocking Fee VIP Conflict | 150 |
| 5 | Courier Weekend Slip | 100 |
| 6 | CrossBorder Courier Allowed | 150 |
| 7 | Fraud Score Bypass | 200 |
| 8 | IIN Owner Mismatch | 200 |
| 9 | Inspection Skip Threshold | 150 |
| 10 | Exchange Different Category | 100 |
| 11 | Video Requirement Bypass | 100 |
| 12 | Loyalty Points Overflow | 200 |

## 🔧 Переменные окружения

### Backend

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `FRONTEND_URL` | URL фронтенда для CORS | `https://qa-platform-frontend.fly.dev` |
| `ECOM_LAB_URL` | URL E-Commerce лабы | `https://qa-lab-ecom-return-refund.fly.dev` |
| `PLATFORM_SECRET` | Секрет для верификации | `platform-secret-key` |
| `DEBUG` | Режим отладки | `false` |
| `PORT` | Порт | `8080` |

### Lab

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `MISSION_ID` | ID миссии | `ecom-return-refund` |
| `FLAGS_SEED` | Seed для генерации флагов | `production_seed_2026` |
| `PLATFORM_SECRET` | Секрет для верификации | `platform-secret-key` |
| `DEBUG_MODE` | Режим отладки | `false` |

## 📝 Примеры запросов

### Получить домены

```bash
curl https://qa-platform-backend.fly.dev/api/v1/domains
```

### Запустить лабу

```bash
curl -X POST https://qa-platform-backend.fly.dev/api/v1/labs/start \
  -H "Content-Type: application/json" \
  -d '{"missionId": "ecom-return-refund"}'
```

### Проверить флаг

```bash
curl -X POST https://qa-platform-backend.fly.dev/api/v1/flags/verify \
  -H "Content-Type: application/json" \
  -d '{"flag": "FLAG{RETURN_WINDOW_BYPASS}"}'
```

## 🔄 Масштабирование

Fly.io автоматически останавливает машины при отсутствии трафика и запускает при новых запросах (scale-to-zero).

Для изменения ресурсов:
```bash
# Увеличить память
fly scale memory 512

# Увеличить количество машин
fly scale count 2
```

## 📊 Мониторинг

```bash
# Логи
fly logs

# Статус
fly status

# Метрики
fly dashboard
```

---

*QA Training Platform — Backend v1.0*
