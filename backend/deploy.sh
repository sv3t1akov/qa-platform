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
    
    echo -e "\n${YELLOW}📦 Деплой $name...${NC}"
    cd "$dir"
    
    # Проверяем существует ли приложение
    if ! fly status &> /dev/null 2>&1; then
        echo -e "${YELLOW}Создаю приложение...${NC}"
        fly launch --no-deploy --copy-config --yes
    fi
    
    fly deploy
    
    echo -e "${GREEN}✅ $name задеплоен!${NC}"
    fly status
    
    cd - > /dev/null
}

# Меню (рекомендуемый порядок: Lab → Backend → Frontend)
echo ""
echo "Что деплоить?"
echo "1) Только E-Commerce лабу"
echo "2) Только Backend"
echo "3) Только Frontend"
echo "4) Всё (лаба + backend + frontend)"
echo "5) Выход"
echo ""
read -p "Выберите опцию (1-5): " choice

case $choice in
    1)
        deploy_app "E-Commerce Lab" "$SCRIPT_DIR/labs/ecommerce_return_refund_lab"
        ;;
    2)
        deploy_app "Backend API" "$SCRIPT_DIR"
        ;;
    3)
        deploy_app "Frontend" "$SCRIPT_DIR/../frontend"
        ;;
    4)
        deploy_app "E-Commerce Lab" "$SCRIPT_DIR/labs/ecommerce_return_refund_lab"
        deploy_app "Backend API" "$SCRIPT_DIR"
        deploy_app "Frontend" "$SCRIPT_DIR/../frontend"
        ;;
    5)
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
echo -e "  Frontend: ${YELLOW}https://qa-platform-frontend.fly.dev${NC}"
echo -e "  Backend:  ${YELLOW}https://qa-platform-backend.fly.dev${NC}"
echo -e "  Lab:      ${YELLOW}https://qa-lab-ecom-return-refund.fly.dev${NC}"
echo ""
