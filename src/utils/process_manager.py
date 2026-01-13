"""
Process and Port Management Utilities
进程和端口管理工具

Provides utilities for:
- Checking if a port is in use
- Finding and killing processes on a specific port
- PID file management for singleton enforcement
- Graceful server shutdown

提供以下功能：
- 检查端口是否被占用
- 查找并终止占用特定端口的进程
- PID文件管理以确保单例运行
- 优雅的服务器关闭
"""

import os
import sys
import signal
import socket
import logging
import platform
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# Default PID file location
# 默认PID文件位置
PID_FILE_PATH = Path(__file__).parent.parent.parent / ".server.pid"


def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    """
    Check if a port is currently in use
    检查端口是否正在被使用

    Args:
        port: Port number to check
        host: Host address to check (default: 0.0.0.0)

    Returns:
        True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host if host != "0.0.0.0" else "127.0.0.1", port))
        return result == 0


def get_process_on_port(port: int) -> Optional[List[Tuple[int, str]]]:
    """
    Get process information for processes using a specific port
    获取使用特定端口的进程信息

    Args:
        port: Port number to check

    Returns:
        List of tuples (pid, process_name) or None if no process found
    """
    system = platform.system()
    processes = []

    try:
        if system == "Windows":
            # Use netstat on Windows
            # Windows上使用netstat
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=10
            )

            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = int(parts[-1])
                        # Get process name
                        # 获取进程名称
                        try:
                            name_result = subprocess.run(
                                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            name = name_result.stdout.strip().split(",")[0].strip('"')
                        except Exception:
                            name = "unknown"
                        processes.append((pid, name))
        else:
            # Use lsof on Unix/Linux/macOS
            # Unix/Linux/macOS上使用lsof
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True,
                text=True,
                timeout=10
            )

            for pid_str in result.stdout.strip().split("\n"):
                if pid_str:
                    pid = int(pid_str)
                    # Get process name
                    # 获取进程名称
                    try:
                        name_result = subprocess.run(
                            ["ps", "-p", str(pid), "-o", "comm="],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        name = name_result.stdout.strip()
                    except Exception:
                        name = "unknown"
                    processes.append((pid, name))

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout while checking port {port}")
    except FileNotFoundError:
        logger.warning("Required system command not found")
    except Exception as e:
        logger.warning(f"Error checking port {port}: {e}")

    return processes if processes else None


def kill_process_on_port(port: int, force: bool = False) -> bool:
    """
    Kill all processes using a specific port
    终止所有使用特定端口的进程

    Args:
        port: Port number
        force: Force kill without confirmation (default: False)

    Returns:
        True if processes were killed, False otherwise
    """
    processes = get_process_on_port(port)

    if not processes:
        logger.info(f"No process found on port {port}")
        return False

    system = platform.system()
    killed_any = False

    for pid, name in processes:
        try:
            logger.info(f"Killing process {name} (PID: {pid}) on port {port}")

            if system == "Windows":
                # Use taskkill on Windows
                # Windows上使用taskkill
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    timeout=10
                )
            else:
                # Use kill on Unix
                # Unix上使用kill
                os.kill(pid, signal.SIGTERM if not force else signal.SIGKILL)

            killed_any = True
            logger.info(f"Successfully killed process {pid}")

        except ProcessLookupError:
            logger.warning(f"Process {pid} already terminated")
        except PermissionError:
            logger.error(f"Permission denied to kill process {pid}")
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")

    return killed_any


def write_pid_file(pid: Optional[int] = None, path: Optional[Path] = None) -> bool:
    """
    Write current process ID to PID file
    将当前进程ID写入PID文件

    Args:
        pid: Process ID to write (default: current process)
        path: Path to PID file (default: .server.pid)

    Returns:
        True if successful, False otherwise
    """
    pid = pid or os.getpid()
    path = path or PID_FILE_PATH

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(pid))
        logger.info(f"PID file written: {path} (PID: {pid})")
        return True
    except Exception as e:
        logger.error(f"Failed to write PID file: {e}")
        return False


def read_pid_file(path: Optional[Path] = None) -> Optional[int]:
    """
    Read process ID from PID file
    从PID文件读取进程ID

    Args:
        path: Path to PID file (default: .server.pid)

    Returns:
        Process ID or None if file doesn't exist or is invalid
    """
    path = path or PID_FILE_PATH

    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return int(f.read().strip())
    except (ValueError, IOError) as e:
        logger.warning(f"Failed to read PID file: {e}")

    return None


def remove_pid_file(path: Optional[Path] = None) -> bool:
    """
    Remove PID file
    删除PID文件

    Args:
        path: Path to PID file (default: .server.pid)

    Returns:
        True if successful or file doesn't exist, False otherwise
    """
    path = path or PID_FILE_PATH

    try:
        if path.exists():
            path.unlink()
            logger.info(f"PID file removed: {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove PID file: {e}")
        return False


def is_process_running(pid: int) -> bool:
    """
    Check if a process with given PID is running
    检查给定PID的进程是否正在运行

    Args:
        pid: Process ID to check

    Returns:
        True if process is running, False otherwise
    """
    system = platform.system()

    try:
        if system == "Windows":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return str(pid) in result.stdout
        else:
            # Send signal 0 to check if process exists
            # 发送信号0检查进程是否存在
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, PermissionError):
        return False
    except Exception:
        return False


def check_singleton(port: int) -> Tuple[bool, Optional[str]]:
    """
    Check if another instance of the server is already running
    检查是否已有另一个服务器实例在运行

    This function checks both PID file and port to ensure no duplicate instances.
    此函数同时检查PID文件和端口以确保没有重复实例。

    Args:
        port: Server port to check

    Returns:
        Tuple of (is_ok, error_message)
        - (True, None) if no other instance is running
        - (False, error_message) if another instance is detected
    """
    # Check PID file first
    # 首先检查PID文件
    old_pid = read_pid_file()

    if old_pid:
        if is_process_running(old_pid):
            return False, f"Another server instance is running (PID: {old_pid}). Use 'scripts/stop.bat' to stop it first."
        else:
            # Stale PID file, remove it
            # 过期的PID文件，删除它
            logger.info(f"Removing stale PID file (PID: {old_pid} is not running)")
            remove_pid_file()

    # Check if port is in use
    # 检查端口是否被占用
    if is_port_in_use(port):
        processes = get_process_on_port(port)
        if processes:
            proc_info = ", ".join([f"{name}(PID:{pid})" for pid, name in processes])
            return False, f"Port {port} is already in use by: {proc_info}. Kill the process or use a different port."
        else:
            return False, f"Port {port} is already in use by an unknown process."

    return True, None


def startup_check(port: int, auto_kill: bool = False) -> bool:
    """
    Perform startup checks before starting the server
    在启动服务器前执行启动检查

    Args:
        port: Server port
        auto_kill: Automatically kill existing processes on port (default: False)

    Returns:
        True if server can start, False otherwise
    """
    logger.info(f"Performing startup checks for port {port}...")

    is_ok, error_msg = check_singleton(port)

    if not is_ok:
        if auto_kill and is_port_in_use(port):
            logger.warning(f"Auto-killing processes on port {port}")
            if kill_process_on_port(port, force=True):
                # Wait a moment for port to be released
                # 等待端口释放
                import time
                time.sleep(1)

                # Check again
                # 再次检查
                if not is_port_in_use(port):
                    logger.info(f"Port {port} is now available")
                    return True

        logger.error(error_msg)
        return False

    logger.info("Startup checks passed")
    return True


def graceful_shutdown():
    """
    Perform graceful shutdown
    执行优雅关闭

    Removes PID file and performs cleanup.
    删除PID文件并执行清理。
    """
    logger.info("Performing graceful shutdown...")
    remove_pid_file()
    logger.info("Shutdown complete")


# Register shutdown handler
# 注册关闭处理器
import atexit
atexit.register(graceful_shutdown)
