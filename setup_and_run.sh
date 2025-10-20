#!/bin/bash

# Colors for output
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
echo "║         Keystroke Biometrics                            ║"
echo "║       Biometric Identification                            ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

PROJECT_DIR="/home/katae/study/bio"
cd "$PROJECT_DIR"

# Requirement check helper
check_requirement() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

# System requirements check
echo -e "\n${CYAN}📋 Checking system requirements...${NC}\n"

check_requirement python3
PYTHON_OK=$?

check_requirement pip3
PIP_OK=$?

if [ $PYTHON_OK -ne 0 ] || [ $PIP_OK -ne 0 ]; then
    echo -e "\n${RED}❌ Missing requirements!${NC}"
    echo -e "${YELLOW}Please install Python 3 and pip3${NC}"
    exit 1
fi

# Проверка версии Python
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION"

echo -e "\n${GREEN}✅ All requirements satisfied!${NC}"

# Backend setup
echo -e "\n${CYAN}📦 Setting up Backend...${NC}\n"

cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Backend setup complete!"
else
    echo -e "${RED}✗${NC} Failed to install dependencies"
    exit 1
fi

# Create data directory
mkdir -p data

# Start menu
echo -e "\n${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  Select run mode:                                           ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}1)${NC} Run Backend only (API)"
echo -e "${CYAN}2)${NC} Run Backend + Frontend (full system)"
echo -e "${CYAN}3)${NC} Run Backend + execute tests"
echo -e "${CYAN}4)${NC} Show project info"
echo -e "${CYAN}5)${NC} Exit"
echo ""
read -p "Your choice (1-5): " choice

case $choice in
    1)
        echo -e "\n${GREEN}🚀 Starting Backend...${NC}\n"
        cd "$PROJECT_DIR/backend"
        source venv/bin/activate
        python app.py
        ;;
    
    2)
        echo -e "\n${GREEN}🚀 Starting full system...${NC}\n"
        
        # Run backend in background
        cd "$PROJECT_DIR/backend"
        source venv/bin/activate
        python app.py &
        BACKEND_PID=$!
        
        echo -e "${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"
        echo -e "${YELLOW}⏳ Waiting for Backend to initialize...${NC}"
        sleep 3
        
        # Check backend health
        if curl -s http://localhost:5000/api/health > /dev/null; then
            echo -e "${GREEN}✓${NC} Backend is healthy"
        else
            echo -e "${RED}✗${NC} Backend is not responding"
            kill $BACKEND_PID 2>/dev/null
            exit 1
        fi
        
        # Start frontend
        echo -e "\n${GREEN}🌐 Starting Frontend...${NC}"
        echo -e "${CYAN}Open browser at: ${YELLOW}http://localhost:8000${NC}\n"
        
        cd "$PROJECT_DIR/frontend"
        python3 -m http.server 8000
        
        # Stop backend when frontend server exits
        kill $BACKEND_PID 2>/dev/null
        ;;
    
    3)
        echo -e "\n${GREEN}🧪 Starting Backend and tests...${NC}\n"
        
        # Run backend in background
        cd "$PROJECT_DIR/backend"
        source venv/bin/activate
        python app.py &
        BACKEND_PID=$!
        
        echo -e "${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"
        echo -e "${YELLOW}⏳ Waiting for initialization...${NC}"
        sleep 3
        
        # Ensure requests is installed
        pip install -q requests
        
        # Run tests
        cd "$PROJECT_DIR"
        python3 test_api.py
        
        # Stop backend
        echo -e "\n${YELLOW}Stopping Backend...${NC}"
        kill $BACKEND_PID 2>/dev/null
        echo -e "${GREEN}✓${NC} Backend stopped"
        ;;
    
    4)
        echo -e "\n${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${PURPLE}║  Project Information                                        ║${NC}"
        echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}Name:${NC} Keystroke Biometrics"
        echo -e "${CYAN}Description:${NC} Biometric identification by typing patterns"
        echo ""
        echo -e "${YELLOW}Stack:${NC}"
        echo -e "  • Backend: Python, Flask, scikit-learn"
        echo -e "  • Frontend: JavaScript, HTML5, CSS3"
        echo -e "  • ML: Distance-based matching"
        echo ""
        echo -e "${YELLOW}Biometric features:${NC}"
        echo -e "  • Dwell Time"
        echo -e "  • Flight Time"
        echo -e "  • Inter-key Latency"
        echo -e "  • Typing Speed"
        echo -e "  • Rhythm Consistency"
        echo ""
        echo -e "${YELLOW}Project files:${NC}"
        echo -e "  • ${GREEN}README.md${NC} - Documentation"
        echo -e "  • ${GREEN}USAGE.md${NC} - User guide"
        echo -e "  • ${GREEN}test_api.py${NC} - Test script"
        echo ""
        echo -e "${YELLOW}Quick start:${NC}"
        echo -e "  ${CYAN}./setup_and_run.sh${NC} - this script"
        echo -e "  ${CYAN}./start_backend.sh${NC} - backend only"
        echo -e "  ${CYAN}./start_frontend.sh${NC} - frontend only"
        echo ""
        ;;
    
    5)
        echo -e "\n${CYAN}👋 Goodbye!${NC}\n"
        exit 0
        ;;
    
    *)
        echo -e "\n${RED}❌ Invalid choice${NC}\n"
        exit 1
        ;;
esac


