# Ручное выполнение миграций на Fly.io

Если автоматические миграции не работают, выполните их вручную.

**Если видите ошибку** `column "requirements" does not exist` — см. в `DEPLOY.md` раздел «Troubleshooting: 500 на /missions» и подраздел «Почему это случилось». Там же инструкция: либо задеплой с текущим кодом (миграция применится при старте), либо выполнить вручную `ALTER TABLE missions ADD COLUMN IF NOT EXISTS requirements TEXT;`.

## Откуда взять DATABASE_URL

- **Fly Secrets:** `fly secrets list --app qa-platform-backend` — показывает только имена секретов, значение не выводится. Строку подключения задают при `fly secrets set DATABASE_URL=...` или берут из Fly Dashboard.
- **Fly Postgres:** в дашборде Fly → ваше Postgres-приложение → раздел "Connection" / "Connection string". Для подключения с локальной машины к приватной БД используйте `fly proxy 5432 -a <postgres-app-name>` и в строке подключения укажите `localhost:5432`.
- **Локально:** скопируйте значение из `.env` или из настроек деплоя, где задаётся `DATABASE_URL`.

## Способ 1: Через fly ssh (рекомендуется)

Контейнер бэкенда уже имеет `DATABASE_URL` из секретов Fly. После деплоя обновлённого кода:

```bash
fly ssh console --app qa-platform-backend

# Внутри контейнера:
cd /app
python -m app.db.migrate

exit
```

Будут применены все миграции, включая seed_social_t1_missions.sql и seed_social_t1_bugs.sql. Для миссий с `ON CONFLICT DO UPDATE` повторный запуск обновит теорию и задачу.

## Способ 2: Через psql (нужна строка подключения)

Если есть строка подключения к продовой БД:

```bash
# Из корня репозитория, с указанием пути к SQL-файлам
cd backend
psql "$DATABASE_URL" -f app/db/schema.sql
psql "$DATABASE_URL" -f app/db/seed_missions.sql
psql "$DATABASE_URL" -f app/db/seed_bugs.sql
psql "$DATABASE_URL" -f app/db/seed_social_t1_missions.sql
psql "$DATABASE_URL" -f app/db/seed_social_t1_bugs.sql
```

Если БД доступна только внутри Fly (приватная сеть):

```bash
# Терминал 1: туннель к Postgres-приложению
fly proxy 5432 -a <your-postgres-app-name>

# Терминал 2: подставьте в DATABASE_URL хост localhost и порт 5432
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
psql "$DATABASE_URL" -f app/db/seed_missions.sql
psql "$DATABASE_URL" -f app/db/seed_bugs.sql
```

## Способ 3: Локально через Python (мигратор)

При заданном `DATABASE_URL` (продовая или локальная БД):

```bash
cd backend
export DATABASE_URL="postgresql://..."
python -m app.db.migrate
```

Подключение идёт через asyncpg; применяются schema, seed_missions.sql и seed_bugs.sql.
