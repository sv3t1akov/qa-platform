# E-Commerce Return & Refund Lab

## 🎯 Обзор миссии

| Параметр | Значение |
|----------|----------|
| **Код миссии** | ECOM-ADV-001 |
| **Название** | Return & Refund Pipeline |
| **Домен** | E-Commerce / Marketplace |
| **Сложность** | T4-T5 (Advanced) |
| **Флагов** | 12 |
| **Параметров в контракте** | 127 |

## 📁 Структура проекта

```
ecommerce_return_refund_lab/
├── app/
│   ├── __init__.py
│   └── main.py              # Основной FastAPI application
├── tests/
│   └── test_flags.py        # Тесты для верификации флагов
├── Dockerfile               # Docker образ
├── docker-compose.yml       # Локальная разработка
├── fly.toml                 # Конфигурация Fly.io
├── requirements.txt         # Python зависимости
└── README.md
```

## 🚀 Быстрый старт

### Локальный запуск (Docker)

```bash
# Клонировать и перейти в директорию
cd ecommerce_return_refund_lab

# Запустить через Docker Compose
docker-compose up --build

# API доступен по адресу:
# http://localhost:8080
# Документация: http://localhost:8080/docs
```

### Локальный запуск (Python)

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
.\venv\Scripts\activate   # Windows

# Установить зависимости
pip install -r requirements.txt

# Запустить
cd app
uvicorn main:app --reload --port 8080
```

### Деплой на Fly.io

```bash
# Установить Fly CLI
curl -L https://fly.io/install.sh | sh

# Авторизоваться
fly auth login

# Создать приложение (первый раз)
fly launch --name qa-lab-ecom-return-refund

# Деплой
fly deploy

# Проверить статус
fly status
fly logs
```

## 📋 API Endpoints

### Основные endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/v1/returns` | Создание заявки на возврат |
| `GET` | `/api/v1/returns/{id}` | Получение статуса заявки |
| `GET` | `/api/v1/returns` | История возвратов |
| `POST` | `/api/v1/returns/{id}/cancel` | Отмена заявки |
| `GET` | `/api/v1/returns/{id}/refund-calculation` | Расчёт суммы возврата |

### Вспомогательные endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/hints` | Подсказки для студентов |
| `GET` | `/api/v1/products/{id}` | Информация о товаре |
| `GET` | `/api/v1/logistics/slots` | Доступные слоты курьера |
| `GET` | `/api/v1/customers/{id}/returns/stats` | Статистика возвратов |

### Endpoints для платформы

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/v1/flags/verify` | Верификация флага |
| `GET` | `/api/v1/flags/list` | Список всех флагов |
| `POST` | `/api/v1/test/seed-data` | Создание тестовых данных |
| `DELETE` | `/api/v1/test/reset` | Сброс тестовых данных |

## 🏴 Флаги миссии

| # | Тип уязвимости | Сложность | Баллы |
|---|----------------|-----------|-------|
| 1 | Business Logic | T4 | 150 |
| 2 | Incomplete Validation | T3 | 100 |
| 3 | Calculation Error | T4 | 150 |
| 4 | Conflicting Requirements | T4 | 150 |
| 5 | Incomplete Business Rule | T3 | 100 |
| 6 | Missing Cross-Reference | T4 | 150 |
| 7 | Security Bypass | T5 | 200 |
| 8 | Authorization Bypass | T5 | 200 |
| 9 | Threshold Bypass | T4 | 150 |
| 10 | Missing Validation | T3 | 100 |
| 11 | Input Validation Bypass | T3 | 100 |
| 12 | Integer Overflow | T5 | 200 |

**Максимум баллов:** 1750

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SESSION_ID` | ID сессии студента | `local-dev` |
| `USER_ID` | ID пользователя | `dev-user` |
| `MISSION_ID` | ID миссии | `ecom-return-refund` |
| `FLAGS_SEED` | Seed для генерации флагов | `dev_seed_12345` |
| `DEBUG_MODE` | Режим отладки | `true` |
| `PLATFORM_SECRET` | Секрет для верификации | `dev-secret` |
| `PORT` | Порт приложения | `8080` |

## 🧪 Тестирование

### Пример запроса на создание возврата

```bash
curl -X POST "http://localhost:8080/api/v1/returns" \
  -H "Content-Type: application/json" \
  -d '{
    "order": {
      "orderId": "550e8400-e29b-41d4-a716-446655440000",
      "orderDate": "2024-01-15",
      "deliveryDate": "2024-01-18"
    },
    "items": [{
      "itemId": "item-001",
      "productId": "PHONE-X",
      "category": "ELECTRONICS",
      "quantity": 1,
      "unitPrice": 35000000,
      "reason": {
        "code": "DEFECTIVE",
        "description": "Экран не включается после зарядки. Пробовал разные зарядные устройства - не помогает."
      },
      "evidence": {
        "photos": ["https://storage.example.com/photo1.jpg"]
      }
    }],
    "seller": {
      "sellerId": "seller-001",
      "sellerCountry": "KZ"
    },
    "customer": {
      "customerId": "customer-001",
      "contact": {
        "firstName": "Иван",
        "lastName": "Иванов",
        "phone": "+77001234567",
        "email": "ivan@example.com"
      },
      "pickupAddress": {
        "country": "KZ",
        "region": "Алматы",
        "city": "Алматы",
        "street": "Абая",
        "building": "150"
      }
    },
    "logistics": {
      "returnMethod": "COURIER_PICKUP",
      "pickup": {
        "preferredDate": "2024-01-25",
        "preferredTimeSlot": "MORNING_9_12",
        "contactPerson": "Иван Иванов",
        "contactPhone": "+77001234567"
      },
      "dimensions": {
        "weight": 500,
        "length": 20,
        "width": 10,
        "height": 5
      }
    },
    "refund": {
      "preferredMethod": "ORIGINAL_PAYMENT"
    },
    "options": {
      "consents": {
        "personalDataProcessing": true,
        "thirdPartySharing": true
      }
    }
  }'
```

### Проверка флага (для платформы)

```bash
curl -X POST "http://localhost:8080/api/v1/flags/verify" \
  -H "Content-Type: application/json" \
  -H "X-Platform-Secret: dev-secret" \
  -d '{"flag": "FLAG{RETURN_WINDOW_BYPASS}"}'
```

## 📚 Интеграция с платформой

### Запуск через оркестратор

```python
# В FlyOrchestrator добавить:
lab_config = {
    "mission_id": "ecom-return-refund",
    "image": "registry.fly.io/qa-lab-ecom-return-refund:latest",
    "env": {
        "SESSION_ID": session_id,
        "USER_ID": user_id,
        "FLAGS_SEED": generate_seed(user_id, mission_id),
        "PLATFORM_SECRET": platform_secret
    },
    "ttl_hours": 4  # Больше времени для сложной миссии
}
```

### Верификация флагов

```python
async def verify_student_flag(session_url: str, flag: str, platform_secret: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{session_url}/api/v1/flags/verify",
            json={"flag": flag},
            headers={"X-Platform-Secret": platform_secret}
        )
        return response.json()
```

## 🔒 Безопасность

- Endpoint `/api/v1/flags/list` защищён секретом
- Endpoint `/api/v1/flags/verify` защищён секретом
- Тестовые endpoints (`/api/v1/test/*`) должны быть отключены в production
- Флаги генерируются на основе seed — уникальны для каждой сессии

## 📝 Changelog

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0.0 | 2026-01-31 | Начальная версия |

---

*QA Training Platform — E-Commerce Domain*
