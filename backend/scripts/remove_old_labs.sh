#!/bin/bash
#
# Удаление устаревших Fly.io приложений (лабы после объединения по доменам)
#
# Использование:
#   ./scripts/remove_old_labs.sh
#   ./scripts/remove_old_labs.sh --dry-run   # только показать, не удалять
#   ./scripts/remove_old_labs.sh --yes       # без подтверждения
#

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Приложения для удаления (заменены объединёнными лабами)
APPS_TO_REMOVE=(
    "qa-lab-booking-t1"           # → qa-lab-booking
    "qa-lab-ecom-return-refund"    # → qa-lab-ecommerce (T1)
    "qa-lab-ecom-t2"              # → qa-lab-ecommerce (T2)
    "qa-lab-ecom-t3"              # → qa-lab-ecommerce (T3)
)

DRY_RUN=false
AUTO_YES=false

for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --yes)     AUTO_YES=true ;;
    esac
done

echo "🗑️  Удаление устаревших Fly.io приложений"
echo "=========================================="
echo ""
echo "Будут удалены (заменены объединёнными лабами):"
for app in "${APPS_TO_REMOVE[@]}"; do
    echo "  - $app"
done
echo ""
echo "Остаются: qa-lab-booking, qa-lab-ecommerce, qa-platform-backend, qa-platform-frontend"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Режим --dry-run: приложения не удаляются${NC}"
    for app in "${APPS_TO_REMOVE[@]}"; do
        if fly status -a "$app" &>/dev/null; then
            echo "  [существует] $app"
        else
            echo "  [не найдено] $app"
        fi
    done
    exit 0
fi

if [ "$AUTO_YES" != true ]; then
    echo -e "${RED}Внимание: удаление необратимо!${NC}"
    read -p "Продолжить? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Отменено."
        exit 0
    fi
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

for app in "${APPS_TO_REMOVE[@]}"; do
    echo -e "\n${YELLOW}Удаление $app...${NC}"
    if fly status -a "$app" &>/dev/null; then
        fly apps destroy "$app" --yes
        echo -e "${GREEN}✅ $app удалён${NC}"
    else
        echo "  (приложение не найдено, пропуск)"
    fi
done

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Готово!${NC}"
echo -e "${GREEN}==========================================${NC}"
