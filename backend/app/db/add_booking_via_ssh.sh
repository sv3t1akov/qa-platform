#!/bin/bash
# Скрипт для добавления Booking T1 миссий через SSH в контейнер backend
# Это самый простой способ, так как DATABASE_URL уже настроен в контейнере

set -e

echo "🚀 Добавление Booking T1 миссий через SSH в контейнер backend"
echo "================================================================"

# Проверка Fly CLI
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI не найден. Установите: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

echo ""
echo "📦 Подключаюсь к контейнеру backend..."
echo ""

# Выполняем команды внутри контейнера
fly ssh console -a qa-platform-backend -C "cd /app/app/db && python3 add_booking_t1.py"

echo ""
echo "✅ Готово! Проверьте результат выше."
