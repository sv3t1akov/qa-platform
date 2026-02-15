# QA Training Platform – Fly.io Deployment

## Prerequisites

- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- Fly.io account: `fly auth login`

## Deployment Order

Deploy in this order so URLs and CORS are correct:

1. **E-Commerce T1 Lab** (for return/refund missions)
2. **E-Commerce T2 Lab** (for boundary values missions: Price Boundary, Quantity Limits, Pagination & Sorting Abuse, etc.)
3. **E-Commerce T3 Lab** (for business logic & multi-step scenarios: Cart State, Order State Machine, Return Flow, Inventory, Discount, Loyalty, Payment)
4. **Backend API**
5. **Frontend**

## Quick Deploy

From project root:

```bash
cd backend
./deploy.sh
# Choose 6) Всё (все лабы + backend + frontend)
```

Or deploy individually:

```bash
# Lab T1 (ecommerce return/refund)
cd backend/labs/ecommerce_return_refund_lab && fly deploy

# Lab T2 (ecommerce boundary values)
cd backend/labs/ecommerce_t2_lab && fly deploy

# Lab T3 (ecommerce business logic & multi-step)
cd backend/labs/ecommerce_t3_lab && fly deploy

# Backend
cd backend && fly deploy

# Frontend (builds with backend URL baked in)
cd frontend && fly deploy
```

## Environment Variables

### Frontend (build-time, set in `frontend/fly.toml` or Docker build args)

| Variable         | Description                          | Production (Fly)                          |
|-----------------|--------------------------------------|-------------------------------------------|
| `VITE_API_URL`  | Backend API base URL                 | `https://qa-platform-backend.fly.dev`    |
| `VITE_DEMO_MODE`| `true` = mock data, `false` = API    | `false`                                   |

Local development: copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_URL=http://localhost:8080` and `VITE_DEMO_MODE=false` to use a local backend.

### Backend (runtime, set in `backend/fly.toml` or Fly secrets)

| Variable         | Description                    | Default (Fly)                              |
|-----------------|--------------------------------|--------------------------------------------|
| `FRONTEND_URL`  | Allowed CORS origin            | `https://qa-platform-frontend.fly.dev`    |
| `ECOM_LAB_URL`  | E-Commerce lab base URL        | `https://qa-lab-ecom-return-refund.fly.dev` |
| `PLATFORM_SECRET` | Secret for lab flag verification | `platform-secret-key` (change in prod)   |
| `DEBUG`         | Enable debug/reload            | `false`                                    |

## URLs After Deploy

| App    | URL |
|--------|-----|
| Frontend | https://qa-platform-frontend.fly.dev |
| Backend  | https://qa-platform-backend.fly.dev |
| Lab T1 (E-Commerce Return/Refund) | https://qa-lab-ecom-return-refund.fly.dev |
| Lab T2 (E-Commerce Boundary Values) | https://qa-lab-ecom-t2.fly.dev |
| Lab T3 (E-Commerce Business Logic & Multi-Step) | https://qa-lab-ecom-t3.fly.dev |

## Health Checks

- **Frontend**: `GET /health` (nginx)
- **Backend**: `GET /health` (FastAPI)
- **Lab T1**: `GET /health` (lab app)
- **Lab T2**: `GET /health` (lab app)
- **Lab T3**: `GET /health` (lab app)

## Troubleshooting: Backend 502 на /auth/login

Если логин возвращает 502 Bad Gateway и CORS-ошибку в браузере:

1. **Cold start** — при `min_machines_running = 0` машина останавливается. Первый запрос после простоя может получить 502. Решение: `min_machines_running = 1` в `backend/fly.toml`.

2. **OOM (Argon2)** — Argon2 с `memory_cost=65536` (64 MB) при VM 256 MB может вызвать нехватку памяти при проверке пароля. Решение: `ARGON2_MEMORY_COST=8192` (8 MB) в env.

3. **Логи** — проверьте: `fly logs -a qa-platform-backend`. Ищите OOM, таймауты, ошибки БД.

4. **Health vs Login** — если `/health` возвращает 200, а `/auth/login` — 502, проблема в логике login (БД, память), а не в cold start.

## Troubleshooting: Lab 503/502

If a lab returns 503 or 502 for `/health` or other endpoints:

### Lab T1 (Return/Refund)

1. **Logs**  
   `fly logs -a qa-lab-ecom-return-refund`  
   Check for import errors, OOM, or port binding issues.

2. **Startup time**  
   In `backend/labs/ecommerce_return_refund_lab/fly.toml`, `grace_period` is 30s and health check `timeout` is 10s. If the app starts slowly, increase these.

3. **Memory**  
   Lab VM is 1024 MB. If logs show OOM, consider increasing `memory_mb` in `fly.toml`.

4. **Local check**  
   Run the lab locally to confirm it works:  
   `cd backend/labs/ecommerce_return_refund_lab && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080`  
   Then: `curl -s http://127.0.0.1:8080/health` and `curl -s http://127.0.0.1:8080/products/1`.

### Lab T2 (Boundary Values)

1. **Logs**  
   `fly logs -a qa-lab-ecom-t2`  
   Check for import errors, OOM, or port binding issues.

2. **Startup time**  
   In `backend/labs/ecommerce_t2_lab/fly.toml`, `grace_period` is 30s and health check `timeout` is 10s. If the app starts slowly, increase these.

3. **Memory**  
   Lab VM is 1024 MB. If logs show OOM, consider increasing `memory_mb` in `fly.toml`.

4. **Local check**  
   Run the lab locally to confirm it works:  
   `cd backend/labs/ecommerce_t2_lab && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080`  
   Then: `curl -s http://127.0.0.1:8080/health` and `curl -s http://127.0.0.1:8080/products`.

### Lab T3 (Business Logic & Multi-Step)

1. **Logs**  
   `fly logs -a qa-lab-ecom-t3`  
   Check for import errors, OOM, or port binding issues.

2. **Startup time**  
   In `backend/labs/ecommerce_t3_lab/fly.toml`, `grace_period` is 30s and health check `timeout` is 10s. If the app starts slowly, increase these.

3. **Memory**  
   Lab VM is 1024 MB. If logs show OOM, consider increasing `memory_mb` in `fly.toml`.

4. **Local check**  
   Run the lab locally to confirm it works:  
   `cd backend/labs/ecommerce_t3_lab && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080`  
   Then: `curl -s http://127.0.0.1:8080/health` and `curl -s http://127.0.0.1:8080/cart`.

### DNS Resolution Error (ENOTFOUND)

If you see `getaddrinfo ENOTFOUND qa-lab-ecom-t2.fly.dev` or `getaddrinfo ENOTFOUND qa-lab-ecom-t3.fly.dev`:

1. **Check if lab is deployed**  
   `fly status -a qa-lab-ecom-t2` or `fly status -a qa-lab-ecom-t3`  
   If app doesn't exist, deploy it: `cd backend/labs/ecommerce_t2_lab && fly deploy` or `cd backend/labs/ecommerce_t3_lab && fly deploy`

2. **Verify app name**  
   Check `backend/labs/ecommerce_t2_lab/fly.toml` - `app = "qa-lab-ecom-t2"` should match the URL in database.  
   Check `backend/labs/ecommerce_t3_lab/fly.toml` - `app = "qa-lab-ecom-t3"` should match the URL in database.

3. **Check DNS**  
   The app should be accessible at `https://qa-lab-ecom-t2.fly.dev` or `https://qa-lab-ecom-t3.fly.dev` after deployment. Verify with: `curl -I https://qa-lab-ecom-t2.fly.dev/health` or `curl -I https://qa-lab-ecom-t3.fly.dev/health`

## Troubleshooting: 500 на /missions, column "requirements" does not exist

Если в логах бэкенда на Fly.io видно `ProgrammingError: column "requirements" does not exist` и фронт отдаёт 500 при запросе миссий, значит в продовой БД нет колонки `missions.requirements`, которую ожидает код.

### Почему это случилось

1. **Миграции не применены на Fly Postgres (самое частое)**  
   В коде и в `schema.sql` колонка уже есть, но на проде миграции не запускались после добавления поля. Полный `schema.sql` при уже существующих таблицах не добавляет новые колонки — он только создаёт таблицы «с нуля». Поэтому для существующей БД нужны инкрементальные миграции (например `migrations/add_requirements_column.sql`).

2. **Миграция есть, но не попала в деплой / не выполняется в релизе**  
   Файл миграции добавлен в репозиторий, но деплой прошёл без перезапуска приложения или скрипт миграций не вызывается при старте (или вызывается после старых образов без этой миграции).

3. **В БД колонка называется иначе**  
   В базе колонка может называться по-другому (`requirement`, `requirements_text`, `requirements_json` и т.п.), а код ожидает ровно `requirements`. Либо наоборот: в коде переименовали поле, а в БД осталось старое имя.

4. **Пересоздавали базу (или другой app/db), а DDL не накатывали**  
   После создания новой БД или переключения на другой инстанс Postgres забыли выполнить полный DDL (schema + миграции), поэтому структура отстаёт от кода.

### Что сделать

- **Вариант А (рекомендуется):** Задеплоить бэкенд с текущим кодом — при старте выполнится `app.db.migrate`, в том числе `migrations/add_requirements_column.sql`. Либо вручную выполнить миграции (см. раздел «Обновление миссий в продовой БД» ниже).
- **Вариант Б:** Подключиться к продовой БД и выполнить вручную:
  ```sql
  ALTER TABLE missions ADD COLUMN IF NOT EXISTS requirements TEXT;
  ```

После добавления колонки перезапуск бэкенда не обязателен; следующий запрос к `/missions` уже не должен падать с этой ошибкой.

## Обновление миссий в продовой БД (теория, задача, подсказки)

Чтобы применить обновлённый `seed_missions.sql` (например, новая теория и описание задач) к **уже развёрнутой** продовой БД, можно использовать один из способов ниже.

### Способ 1: Через Fly SSH (рекомендуется)

Бэкенд при старте может сам применять миграции; либо можно выполнить сид вручную из контейнера (после деплоя бэкенда с новым кодом):

```bash
# 1. Задеплойте бэкенд с обновлённым seed_missions.sql
cd backend
fly deploy --app qa-platform-backend

# 2. Подключитесь к контейнеру бэкенда
fly ssh console --app qa-platform-backend

# 3. Внутри контейнера выполните миграции (применится schema + seed_missions + seed_bugs)
cd /app
python -m app.db.migrate

# 4. Выйдите из консоли
exit
```

Убедитесь, что в контейнере есть переменная `DATABASE_URL` (она задаётся через Fly secrets или [env] в fly.toml). Если миграции при старте приложения уже настроены в `main.py`, после деплоя они могут выполниться автоматически при первом запросе.

### Способ 2: Через psql (если есть доступ к строке подключения)

Если у вас есть строка подключения к продовой PostgreSQL (например, из Fly Postgres или другого хоста):

```bash
# 1. Узнать DATABASE_URL (значение секрета в Fly не показывается, только имя)
fly secrets list --app qa-platform-backend

# Строку подключения можно взять в Fly Dashboard:
# Account → Your Postgres app → "Connection string" (или из настроек бэкенда, где задавали DATABASE_URL).

# 2. Если БД доступна только внутри Fly (private network), поднять туннель:
fly proxy 5432 -a <имя-вашего-postgres-приложения>

# 3. В другом терминале — выполнить сид (подставьте свой DATABASE_URL):
cd backend
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
psql "$DATABASE_URL" -f app/db/seed_missions.sql
# При необходимости затем:
psql "$DATABASE_URL" -f app/db/seed_bugs.sql
```

Если PostgreSQL развёрнут на Fly с публичным адресом, вместо `fly proxy` можно подставлять хост из строки подключения и выполнять `psql` с этой строкой.

### Способ 3: Локально с DATABASE_URL продовой БД

Если вы задаёте `DATABASE_URL` продовой БД у себя локально (через .env или экспорт) и БД доступна с вашей машины (VPN или публичный доступ):

```bash
cd backend
export DATABASE_URL="postgresql://..."   # ваша продовая строка подключения
python -m app.db.migrate
```

Скрипт `app.db.migrate` применит schema, затем `seed_missions.sql` и `seed_bugs.sql`.

### Важно

- В `seed_missions.sql` для миссий ecom-t1-002 … ecom-t5-001 используется `ON CONFLICT (id) DO UPDATE SET ...`, поэтому повторный запуск сида **обновит** существующие строки (теория, задача, подсказки), а не только вставит новые.
- Перед выполнением сида желательно сделать бэкап БД (например, `pg_dump` или снимок в Fly).

## Changing Backend URL for Frontend

Frontend uses `VITE_API_URL` at **build time**. To point to another backend:

1. **Fly.io**: set `[build.args]` in `frontend/fly.toml`:
   ```toml
   [build.args]
     VITE_API_URL = "https://your-backend.fly.dev"
     VITE_DEMO_MODE = "false"
   ```
2. **Local**: set in `frontend/.env` and run `npm run build`.

## 🧪 Mission Tests

Automated tests verify that all missions work correctly: labs are accessible and flags can be retrieved according to bug conditions.

### Running Tests

#### Prerequisites

1. Install test dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Set `DATABASE_URL` environment variable:
   ```bash
   export DATABASE_URL="postgresql://user:password@host:port/dbname"
   ```

#### Test Commands

```bash
# Run all mission tests
cd backend
pytest tests/test_mission_*.py -v

# Run only health check tests (lab availability)
pytest tests/test_mission_health.py -v

# Run only flag retrieval tests
pytest tests/test_mission_flags.py -v

# Run tests for a specific mission (if parametrized)
pytest tests/test_mission_flags.py::test_mission_all_flags -v

# Run with detailed output
pytest tests/test_mission_*.py -v --tb=long

# Skip tests (for local development)
export SKIP_MISSION_TESTS=true
pytest tests/test_mission_*.py -v
```

### Test Structure

- **`tests/test_mission_health.py`** - Tests lab availability via health endpoints
- **`tests/test_mission_flags.py`** - Tests flag retrieval for all bugs
- **`tests/test_lab_integration.py`** - Integration tests for existing lab tests
- **`tests/mission_triggers.py`** - Configuration of triggers for each bug

### Before Deployment

The deploy script (`backend/deploy.sh`) includes an option to run tests before deployment:

```bash
cd backend
./deploy.sh
# Choose option 4 (Deploy everything)
# When prompted, choose 'y' to run tests before deployment
```

Or run tests separately:

```bash
cd backend
./deploy.sh
# Choose option 5 (Run mission tests)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | Required |
| `TEST_DATABASE_URL` | Test database URL (falls back to `DATABASE_URL`) | `DATABASE_URL` |
| `TEST_LAB_TIMEOUT` | Timeout for lab requests (seconds) | `10.0` |
| `SKIP_MISSION_TESTS` | Skip mission tests if set to `true` | `false` |

### Test Configuration

Tests are configured in `backend/pytest.ini`:

- **Markers**: `mission_health`, `mission_flags`, `slow`
- **Async mode**: `auto` (pytest-asyncio)
- **Test paths**: `tests/`
- **Output**: Verbose with short traceback

### Adding New Bug Triggers

When adding a new mission or bug, update `tests/mission_triggers.py`:

```python
MISSION_TRIGGERS = {
    "bug-id": {
        "method": "GET",  # or POST, PUT, etc.
        "url": "/endpoint",
        "params": {"param": "value"},  # Query parameters
        "body": {"key": "value"},  # Request body (or callable)
        "expected_status": [200, 201],  # Expected HTTP status codes
        "flag_location": "response_body",
        "flag_field": "flag",  # Field containing flag
        "setup": [...],  # Optional setup requests
        "repeat": 1,  # Number of times to repeat request
    }
}
```

### Troubleshooting

**Tests fail with "DATABASE_URL not set"**
- Set `DATABASE_URL` environment variable
- Or set `TEST_DATABASE_URL` for a separate test database

**Tests fail with "No missions with labs found"**
- Check that missions in database have `base_url` set
- Verify database connection

**Flag not found in response**
- Check trigger configuration in `mission_triggers.py`
- Verify lab is deployed and accessible
- Check flag format matches database (`FLAG{...}`)
- Review response in test output for debugging

**Lab health check fails**
- Verify lab is deployed: `fly status -a qa-lab-...`
- Check lab logs: `fly logs -a qa-lab-...`
- Verify `base_url` in database matches actual lab URL
