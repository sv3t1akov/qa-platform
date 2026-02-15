#!/bin/bash
# Скрипт для добавления Booking T1 миссий через Fly Proxy к базе данных
# Использует fly proxy для создания туннеля к БД

set -e

echo "🚀 Добавление Booking T1 миссий через Fly Proxy"
echo "================================================="
echo ""
echo "Этот скрипт создаст туннель к базе данных и выполнит добавление миссий."
echo ""
echo "⚠️  ВАЖНО: Вам нужно будет:"
echo "   1. Получить DATABASE_URL из Fly Dashboard"
echo "   2. Заменить хост на localhost:5432 в DATABASE_URL"
echo ""
read -p "Нажмите Enter для продолжения или Ctrl+C для отмены..."

# Проверка Fly CLI
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI не найден. Установите: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Имя приложения Postgres (измените если нужно)
POSTGRES_APP="qa-platform-db"

echo ""
echo "📡 Создаю туннель к базе данных..."
echo "   Приложение: $POSTGRES_APP"
echo ""
echo "⚠️  Оставьте этот терминал открытым!"
echo "   В другом терминале выполните:"
echo ""
echo "   export DATABASE_URL=\"postgresql://user:password@localhost:5432/dbname\""
echo "   cd backend/app/db"
echo "   python3 add_booking_t1.py"
echo ""
echo "   (замените user:password:dbname на реальные значения из Fly Dashboard)"
echo ""
echo "Нажмите Ctrl+C чтобы остановить туннель"
echo ""

# Создаем туннель
fly proxy 5432 -a "$POSTGRES_APP"
