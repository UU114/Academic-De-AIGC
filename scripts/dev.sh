#!/bin/bash
# AcademicGuard Development Server Startup Script
# Unix/Linux/macOS script for starting both frontend and backend
# AcademicGuard 开发服务器启动脚本

echo "===================================="
echo " AcademicGuard Development Server"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PORT=8000
PID_FILE=".server.pid"

# Store process IDs
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
# 清理函数
cleanup() {
    echo ""
    echo "Stopping servers..."

    # Use stop script for backend
    # 使用stop脚本停止后端
    if [ -f "scripts/stop.sh" ]; then
        bash scripts/stop.sh
    fi

    # Kill frontend
    # 终止前端
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi

    echo "All servers stopped."
    exit 0
}

# Set up trap for cleanup
# 设置清理陷阱
trap cleanup SIGINT SIGTERM

# Check if port is already in use
# 检查端口是否已被占用
echo ""
echo "Checking port $PORT..."

EXISTING_PIDS=$(lsof -t -i:$PORT 2>/dev/null)
if [ -n "$EXISTING_PIDS" ]; then
    echo ""
    echo -e "${YELLOW}WARNING: Port $PORT is already in use by PID: $EXISTING_PIDS${NC}"
    echo ""
    read -p "Do you want to kill the existing process and continue? (y/n): " choice
    case "$choice" in
        y|Y )
            for pid in $EXISTING_PIDS; do
                echo "Killing process $pid..."
                kill $pid 2>/dev/null
            done
            sleep 2
            ;;
        * )
            echo "Startup cancelled."
            exit 1
            ;;
    esac
fi

# Check and remove stale PID file
# 检查并删除过期的PID文件
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo ""
        echo -e "${YELLOW}WARNING: Another server instance is running (PID: $OLD_PID)${NC}"
        read -p "Do you want to kill it and continue? (y/n): " choice
        case "$choice" in
            y|Y )
                echo "Killing process $OLD_PID..."
                kill $OLD_PID 2>/dev/null
                rm -f "$PID_FILE"
                sleep 2
                ;;
            * )
                echo "Startup cancelled."
                exit 1
                ;;
        esac
    else
        echo "Removing stale PID file..."
        rm -f "$PID_FILE"
    fi
fi

# Check if virtual environment exists
# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start backend server
# 启动后端服务器
echo ""
echo -e "${GREEN}Starting backend server on http://127.0.0.1:$PORT${NC}"
echo "API Documentation: http://127.0.0.1:$PORT/docs"
echo ""

uvicorn src.main:app --host 127.0.0.1 --port $PORT --reload &
BACKEND_PID=$!

# Wait for backend to start
# 等待后端启动
sleep 3

# Verify backend started successfully
# 验证后端是否启动成功
if curl -s "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
    echo -e "${GREEN}Backend server started successfully.${NC}"
else
    echo -e "${YELLOW}WARNING: Backend may not have started properly. Check for errors.${NC}"
fi

# Start frontend development server
# 启动前端开发服务器
echo ""
echo -e "${GREEN}Starting frontend server on http://127.0.0.1:5173${NC}"
echo ""

cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "===================================="
echo -e " ${GREEN}Servers started successfully!${NC}"
echo " Backend:  http://127.0.0.1:$PORT"
echo " Frontend: http://127.0.0.1:5173"
echo "===================================="
echo ""
echo "Press Ctrl+C to stop all servers..."

# Wait for processes
# 等待进程
wait
