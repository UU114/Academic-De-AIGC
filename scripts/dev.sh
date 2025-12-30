#!/bin/bash
# AcademicGuard Development Server Startup Script
# Unix/Linux/macOS script for starting both frontend and backend

echo "===================================="
echo " AcademicGuard Development Server"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Store process IDs
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    echo "Servers stopped."
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start backend server
echo ""
echo -e "${GREEN}Starting backend server on http://127.0.0.1:8000${NC}"
echo "API Documentation: http://127.0.0.1:8000/docs"
echo ""

uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend development server
echo -e "${GREEN}Starting frontend server on http://127.0.0.1:5173${NC}"
echo ""

cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "===================================="
echo -e " ${GREEN}Servers started successfully!${NC}"
echo " Backend:  http://127.0.0.1:8000"
echo " Frontend: http://127.0.0.1:5173"
echo "===================================="
echo ""
echo "Press Ctrl+C to stop all servers..."

# Wait for processes
wait
