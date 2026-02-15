#!/bin/bash
# Скрипт для добавления Booking T1 миссий в базу данных

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}📦 Добавление Booking T1 миссий в базу данных...${NC}"

# Проверка переменных окружения
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️ DATABASE_URL не установлен, используем значения по умолчанию${NC}"
    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-5432}"
    DB_NAME="${DB_NAME:-qa_platform}"
    DB_USER="${DB_USER:-postgres}"
    DB_PASSWORD="${DB_PASSWORD:-postgres}"
    
    if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "postgres" ]; then
        PGPASSWORD_CMD=""
    else
        export PGPASSWORD="$DB_PASSWORD"
    fi
    
    PSQL_CMD="psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
else
    PSQL_CMD="psql $DATABASE_URL"
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Проверка существования файлов
if [ ! -f "$SCRIPT_DIR/seed_booking_t1_missions.sql" ]; then
    echo -e "${RED}❌ Файл seed_booking_t1_missions.sql не найден!${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/seed_booking_t1_bugs.sql" ]; then
    echo -e "${RED}❌ Файл seed_booking_t1_bugs.sql не найден!${NC}"
    exit 1
fi

# Выполнение seed файлов
echo -e "${YELLOW}Выполняю seed_booking_t1_missions.sql...${NC}"
$PSQL_CMD -f "$SCRIPT_DIR/seed_booking_t1_missions.sql"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Миссии добавлены${NC}"
else
    echo -e "${RED}❌ Ошибка при добавлении миссий${NC}"
    exit 1
fi

echo -e "${YELLOW}Выполняю seed_booking_t1_bugs.sql...${NC}"
$PSQL_CMD -f "$SCRIPT_DIR/seed_booking_t1_bugs.sql"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Баги добавлены${NC}"
else
    echo -e "${RED}❌ Ошибка при добавлении багов${NC}"
    exit 1
fi

# Проверка результата
echo -e "\n${YELLOW}Проверка добавленных данных...${NC}"
MISSIONS_COUNT=$($PSQL_CMD -t -c "SELECT COUNT(*) FROM missions WHERE domain_id = 'booking';")
BUGS_COUNT=$($PSQL_CMD -t -c "SELECT COUNT(*) FROM bugs WHERE mission_id LIKE 'book-t1-%';")

echo -e "${GREEN}✅ Добавлено миссий для Booking: $MISSIONS_COUNT${NC}"
echo -e "${GREEN}✅ Добавлено багов для Booking T1: $BUGS_COUNT${NC}"

echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}🎉 Booking T1 миссии успешно добавлены!${NC}"
echo -e "${GREEN}==========================================${NC}"
