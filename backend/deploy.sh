#!/bin/bash

# QA Platform - Deploy Script
# Деплоит лабы и backend на Fly.io

set -e

echo "🚀 QA Training Platform - Deploy to Fly.io"
echo "==========================================="

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Проверка Fly CLI
if ! command -v fly &> /dev/null; then
    echo -e "${RED}❌ Fly CLI не найден. Установите: curl -L https://fly.io/install.sh | sh${NC}"
    exit 1
fi

# Проверка авторизации
if ! fly auth whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️ Не авторизован в Fly.io. Запускаю авторизацию...${NC}"
    fly auth login
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Функция деплоя
deploy_app() {
    local name=$1
    local dir=$2
    local extra_flags=${3:-""}  # Третий параметр для дополнительных флагов
    
    echo -e "\n${YELLOW}📦 Деплой $name...${NC}"
    cd "$dir"
    
    # Проверяем существует ли приложение
    if ! fly status &> /dev/null 2>&1; then
        echo -e "${YELLOW}Создаю приложение...${NC}"
        fly launch --no-deploy --copy-config --yes
    fi
    
    fly deploy $extra_flags
    
    echo -e "${GREEN}✅ $name задеплоен!${NC}"
    fly status
    
    cd - > /dev/null
}

# Функция запуска тестов миссий
run_mission_tests() {
    echo -e "\n${YELLOW}🧪 Запуск тестов миссий...${NC}"
    cd "$SCRIPT_DIR"
    
    # Проверяем наличие pytest
    if ! command -v pytest &> /dev/null; then
        echo -e "${YELLOW}⚠️ pytest не найден. Устанавливаю зависимости...${NC}"
        pip install -q pytest pytest-asyncio httpx || {
            echo -e "${RED}❌ Не удалось установить pytest${NC}"
            return 1
        }
    fi
    
    # Проверяем DATABASE_URL
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${YELLOW}⚠️ DATABASE_URL не установлен. Пропускаю тесты миссий.${NC}"
        echo -e "${YELLOW}   Установите DATABASE_URL для запуска тестов:${NC}"
        echo -e "${YELLOW}   export DATABASE_URL='postgresql://user:password@host:port/dbname'${NC}"
        return 0
    fi
    
    # Экспортируем DATABASE_URL для pytest (если еще не экспортирован)
    export DATABASE_URL
    
    # Запускаем тесты доступности (они могут работать без БД, но проверяют лабы)
    echo "Запуск тестов доступности лаб..."
    if pytest tests/test_mission_health.py -v --tb=short 2>&1; then
        echo -e "${GREEN}✅ Тесты доступности прошли${NC}"
    else
        TEST_EXIT_CODE=$?
        echo -e "${RED}❌ Тесты доступности провалились (код: $TEST_EXIT_CODE)${NC}"
        if [ "$TEST_EXIT_CODE" -eq 5 ]; then
            # Exit code 5 means no tests were collected or all tests were skipped
            echo -e "${YELLOW}   Все тесты были пропущены (возможно, нет миссий с лабами)${NC}"
        else
            read -p "Продолжить деплой несмотря на ошибки? (y/n): " continue_deploy
            if [ "$continue_deploy" != "y" ]; then
                exit 1
            fi
        fi
    fi
    
    # Запускаем тесты получения флагов (требуют БД)
    echo "Запуск тестов получения флагов..."
    if pytest tests/test_mission_flags.py -v --tb=short -x 2>&1; then
        echo -e "${GREEN}✅ Тесты флагов прошли${NC}"
    else
        TEST_EXIT_CODE=$?
        echo -e "${RED}❌ Тесты флагов провалились (код: $TEST_EXIT_CODE)${NC}"
        if [ "$TEST_EXIT_CODE" -eq 5 ]; then
            # Exit code 5 means no tests were collected or all tests were skipped
            echo -e "${YELLOW}   Все тесты были пропущены (возможно, нет миссий с лабами или триггеров)${NC}"
        else
            read -p "Продолжить деплой несмотря на ошибки? (y/n): " continue_deploy
            if [ "$continue_deploy" != "y" ]; then
                exit 1
            fi
        fi
    fi
    
    cd - > /dev/null
}

# Меню (объединённые лабы по доменам)
echo ""
echo "Что деплоить?"
echo "1) Booking Lab (qa-lab-booking)"
echo "2) E-Commerce Lab (qa-lab-ecommerce, T1+T2+T3)"
echo "3) Social Lab (qa-lab-social, T1)"
echo "4) Только Backend"
echo "5) Только Frontend"
echo "6) Всё (лабы + backend + frontend)"
echo "7) Запустить тесты миссий"
echo "8) Выход"
echo ""
read -p "Выберите опцию (1-8): " choice

case $choice in
    1)
        deploy_app "Booking Lab" "$SCRIPT_DIR/labs/booking_lab"
        echo ""
        echo -e "${YELLOW}🗄️  Обновить тексты миссий в БД?${NC}"
        echo "Booking-миссии (теория/задание/подсказки), которые видит студент в UI, лежат в БД платформы"
        echo "и обновляются при деплое backend (release_command запускает миграции/seed)."
        read -p "Деплоить backend для синка БД? (y/n): " sync_db
        if [ "$sync_db" = "y" ]; then
            deploy_app "Backend API (DB sync)" "$SCRIPT_DIR"
        else
            echo -e "${YELLOW}ℹ️  Пропускаю синк БД. Тексты в UI не изменятся без деплоя backend.${NC}"
        fi
        ;;
    2)
        deploy_app "E-Commerce Lab" "$SCRIPT_DIR/labs/ecommerce_lab"
        ;;
    3)
        deploy_app "Social Lab" "$SCRIPT_DIR/labs/social_lab"
        ;;
    4)
        deploy_app "Backend API" "$SCRIPT_DIR"
        ;;
    5)
        deploy_app "Frontend" "$SCRIPT_DIR/../frontend" "--no-cache"
        ;;
    6)
        if [ "$SKIP_TESTS" != "true" ]; then
            read -p "Запустить тесты миссий перед деплоем? (y/n): " run_tests
            if [ "$run_tests" = "y" ]; then
                run_mission_tests
            fi
        fi
        deploy_app "Booking Lab" "$SCRIPT_DIR/labs/booking_lab"
        deploy_app "E-Commerce Lab" "$SCRIPT_DIR/labs/ecommerce_lab"
        deploy_app "Social Lab" "$SCRIPT_DIR/labs/social_lab"
        deploy_app "Backend API" "$SCRIPT_DIR"
        deploy_app "Frontend" "$SCRIPT_DIR/../frontend" "--no-cache"
        ;;
    7)
        run_mission_tests
        exit 0
        ;;
    8)
        echo "Выход."
        exit 0
        ;;
    *)
        echo -e "${RED}Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}🎉 Деплой завершён!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "URLs:"
echo -e "  Frontend:       ${YELLOW}https://qa-platform-frontend.fly.dev${NC}"
echo -e "  Backend:        ${YELLOW}https://qa-platform-backend.fly.dev${NC}"
echo -e "  Booking Lab:    ${YELLOW}https://qa-lab-booking.fly.dev${NC}"
echo -e "  E-Commerce Lab: ${YELLOW}https://qa-lab-ecommerce.fly.dev${NC}"
echo -e "    - T1:         ${YELLOW}https://qa-lab-ecommerce.fly.dev/t1${NC}"
echo -e "    - T2:         ${YELLOW}https://qa-lab-ecommerce.fly.dev/t2${NC}"
echo -e "    - T3:         ${YELLOW}https://qa-lab-ecommerce.fly.dev/t3${NC}"
echo -e "  Social Lab:     ${YELLOW}https://qa-lab-social.fly.dev${NC}"
echo ""
