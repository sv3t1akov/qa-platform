#!/bin/bash
# Скрипт для выполнения SQL команды выдачи админских прав
# Использование: ./run_make_admin.sh [DATABASE_URL]

set -e

EMAIL="alexandrsvet@gmail.com"
SQL_FILE="$(dirname "$0")/make_admin.sql"

# Получить DATABASE_URL из аргументов или переменной окружения
if [ -n "$1" ]; then
    DATABASE_URL="$1"
elif [ -n "$DATABASE_URL" ]; then
    DATABASE_URL="$DATABASE_URL"
else
    echo "❌ Ошибка: DATABASE_URL не указан"
    echo "Использование: $0 [DATABASE_URL]"
    echo "Или установите переменную окружения DATABASE_URL"
    exit 1
fi

echo "🔧 Выдача админских прав пользователю: $EMAIL"
echo "📊 Подключение к базе данных..."

# Выполнить SQL скрипт
psql "$DATABASE_URL" -f "$SQL_FILE"

echo ""
echo "✅ Готово! Проверьте результат выше."
