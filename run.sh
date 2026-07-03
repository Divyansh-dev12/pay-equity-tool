#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Pay Equity Analyzer - Starting both servers...${NC}\n"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv and install deps if needed
source venv/bin/activate
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -q -r backend/requirements.txt
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing Node dependencies...${NC}"
    cd frontend && npm install --silent && cd ..
fi

# Start backend in background
echo -e "${GREEN}✓ Starting backend (FastAPI)${NC}"
(cd backend && python3 -m uvicorn main:app --reload --port 8000) &
BACKEND_PID=$!

# Start frontend in background
echo -e "${GREEN}✓ Starting frontend (React/Vite)${NC}"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Wait a moment for servers to start
sleep 3

echo -e "\n${GREEN}Both servers started!${NC}"
echo -e "${BLUE}Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}Backend:${NC}  http://localhost:8000"
echo -e "${BLUE}API Docs:${NC} http://localhost:8000/docs\n"
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
