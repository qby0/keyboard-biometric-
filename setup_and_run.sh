#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║       🔐  Keystroke Biometrics                            ║"
echo "║       Биометрическая идентификация                        ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

PROJECT_DIR="/home/katae/study/bio"
cd "$PROJECT_DIR"

# Функция проверки
check_requirement() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 установлен"
        return 0
    else
        echo -e "${RED}✗${NC} $1 не найден"
        return 1
    fi
}

# Проверка системных требований
echo -e "\n${CYAN}📋 Проверка системных требований...${NC}\n"

check_requirement python3
PYTHON_OK=$?

check_requirement pip3
PIP_OK=$?

if [ $PYTHON_OK -ne 0 ] || [ $PIP_OK -ne 0 ]; then
    echo -e "\n${RED}❌ Не все требования выполнены!${NC}"
    echo -e "${YELLOW}Установите Python 3 и pip3${NC}"
    exit 1
fi

# Проверка версии Python
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python версия: $PYTHON_VERSION"

echo -e "\n${GREEN}✅ Все требования выполнены!${NC}"

# Установка backend
echo -e "\n${CYAN}📦 Настройка Backend...${NC}\n"

cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Создание виртуального окружения...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Активация виртуального окружения...${NC}"
source venv/bin/activate

echo -e "${YELLOW}Установка Python зависимостей...${NC}"
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Backend настроен успешно!"
else
    echo -e "${RED}✗${NC} Ошибка при установке зависимостей"
    exit 1
fi

# Создание директории для данных
mkdir -p data

# Меню выбора
echo -e "\n${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  Выберите режим запуска:                                   ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}1)${NC} Запустить только Backend (API)"
echo -e "${CYAN}2)${NC} Запустить Backend + Frontend (полная система)"
echo -e "${CYAN}3)${NC} Запустить Backend + выполнить тесты"
echo -e "${CYAN}4)${NC} Показать информацию о проекте"
echo -e "${CYAN}5)${NC} Выход"
echo ""
read -p "Ваш выбор (1-5): " choice

case $choice in
    1)
        echo -e "\n${GREEN}🚀 Запуск Backend...${NC}\n"
        cd "$PROJECT_DIR/backend"
        source venv/bin/activate
        python app.py
        ;;
    
    2)
        echo -e "\n${GREEN}🚀 Запуск полной системы...${NC}\n"
        
        # Запуск backend в фоне
        cd "$PROJECT_DIR/backend"
        source venv/bin/activate
        python app.py &
        BACKEND_PID=$!
        
        echo -e "${GREEN}✓${NC} Backend запущен (PID: $BACKEND_PID)"
        echo -e "${YELLOW}⏳ Ожидание инициализации Backend...${NC}"
        sleep 3
        
        # Проверка, что backend работает
        if curl -s http://localhost:5000/api/health > /dev/null; then
            echo -e "${GREEN}✓${NC} Backend работает корректно"
        else
            echo -e "${RED}✗${NC} Backend не отвечает"
            kill $BACKEND_PID 2>/dev/null
            exit 1
        fi
        
        # Запуск frontend
        echo -e "\n${GREEN}🌐 Запуск Frontend...${NC}"
        echo -e "${CYAN}Откройте браузер: ${YELLOW}http://localhost:8000${NC}\n"
        
        cd "$PROJECT_DIR/frontend"
        python3 -m http.server 8000
        
        # Остановка backend при завершении
        kill $BACKEND_PID 2>/dev/null
        ;;
    
    3)
        echo -e "\n${GREEN}🧪 Запуск Backend и тестов...${NC}\n"
        
        # Запуск backend в фоне
        cd "$PROJECT_DIR/backend"
        source venv/bin/activate
        python app.py &
        BACKEND_PID=$!
        
        echo -e "${GREEN}✓${NC} Backend запущен (PID: $BACKEND_PID)"
        echo -e "${YELLOW}⏳ Ожидание инициализации...${NC}"
        sleep 3
        
        # Установка requests если нет
        pip install -q requests
        
        # Запуск тестов
        cd "$PROJECT_DIR"
        python3 test_api.py
        
        # Остановка backend
        echo -e "\n${YELLOW}Остановка Backend...${NC}"
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✓${NC} Backend остановлен"
        ;;
    
    4)
        echo -e "\n${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${PURPLE}║  📚 Информация о проекте                                   ║${NC}"
        echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}Название:${NC} Keystroke Biometrics"
        echo -e "${CYAN}Описание:${NC} Биометрическая идентификация по паттернам нажатия клавиш"
        echo ""
        echo -e "${YELLOW}Технологии:${NC}"
        echo -e "  • Backend: Python, Flask, scikit-learn"
        echo -e "  • Frontend: JavaScript, HTML5, CSS3"
        echo -e "  • ML: Random Forest, Distance-based matching"
        echo ""
        echo -e "${YELLOW}Биометрические признаки:${NC}"
        echo -e "  • Dwell Time (время удержания клавиши)"
        echo -e "  • Flight Time (время между нажатиями)"
        echo -e "  • Inter-key Latency (общая задержка)"
        echo -e "  • Typing Speed (скорость печати)"
        echo -e "  • Rhythm Consistency (консистентность ритма)"
        echo ""
        echo -e "${YELLOW}Файлы проекта:${NC}"
        echo -e "  • ${GREEN}README.md${NC} - Полная документация"
        echo -e "  • ${GREEN}USAGE.md${NC} - Руководство пользователя"
        echo -e "  • ${GREEN}test_api.py${NC} - Тестовый скрипт"
        echo ""
        echo -e "${YELLOW}Быстрый запуск:${NC}"
        echo -e "  ${CYAN}./setup_and_run.sh${NC} - этот скрипт"
        echo -e "  ${CYAN}./start_backend.sh${NC} - только backend"
        echo -e "  ${CYAN}./start_frontend.sh${NC} - только frontend"
        echo ""
        ;;
    
    5)
        echo -e "\n${CYAN}👋 До свидания!${NC}\n"
        exit 0
        ;;
    
    *)
        echo -e "\n${RED}❌ Неверный выбор${NC}\n"
        exit 1
        ;;
esac


