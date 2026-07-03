#!/bin/bash

echo "Starting Pay Equity Analyzer..."
echo ""

# Activate venv
source venv/bin/activate

# Start backend in background
echo "Starting Backend (FastAPI on port 8000)..."
cd backend
python3 -m uvicorn main:app --reload --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Start frontend in background
echo "Starting Frontend (React on port 3000)..."
cd ../frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "================================================"
echo "✓ Both servers started!"
echo "================================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Backend Log:  tail -f /tmp/backend.log"
echo "Frontend Log: tail -f /tmp/frontend.log"
echo ""

# Keep script running
wait
