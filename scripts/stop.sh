#!/bin/bash
# AcademicGuard Server Stop Script
# Unix/Linux/macOS script for stopping the server
# AcademicGuard 服务器停止脚本

echo "===================================="
echo " AcademicGuard Server Stop"
echo "===================================="
echo ""

PID_FILE=".server.pid"
PORT=8000

# Check if PID file exists
# 检查PID文件是否存在
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Found PID file with PID: $PID"

    # Try to kill the process
    # 尝试终止进程
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping server process $PID..."
        kill $PID 2>/dev/null

        # Wait for process to stop
        # 等待进程停止
        sleep 2

        # Force kill if still running
        # 如果仍在运行则强制终止
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force killing process $PID..."
            kill -9 $PID 2>/dev/null
        fi

        echo "Server stopped successfully."
    else
        echo "Process $PID is not running."
    fi

    # Remove PID file
    # 删除PID文件
    rm -f "$PID_FILE"
    echo "PID file removed."
else
    echo "No PID file found."
fi

# Also check and kill any process on the port
# 同时检查并终止端口上的任何进程
echo ""
echo "Checking port $PORT..."

PIDS=$(lsof -t -i:$PORT 2>/dev/null)
if [ -n "$PIDS" ]; then
    for PID in $PIDS; do
        echo "Found process $PID on port $PORT"
        kill $PID 2>/dev/null
        echo "Killed process $PID"
    done
else
    echo "No process found on port $PORT"
fi

echo ""
echo "===================================="
echo " Server cleanup complete"
echo "===================================="
