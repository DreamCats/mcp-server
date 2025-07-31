#!/bin/bash

# 股票 MCP 服务启动脚本
# Stock MCP Server Start Script

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_FILE="stock_mcp_server.py"
PID_FILE="$SCRIPT_DIR/stock_mcp.pid"
LOG_FILE="$SCRIPT_DIR/stock_mcp.log"
DEFAULT_PORT=8124
DEFAULT_HOST="localhost"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "股票 MCP 服务启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -p, --port PORT     指定端口号 (默认: $DEFAULT_PORT)"
    echo "  -h, --host HOST     指定主机地址 (默认: $DEFAULT_HOST)"
    echo "  -d, --daemon        后台运行模式"
    echo "  -f, --foreground    前台运行模式 (默认)"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                  # 前台运行，使用默认端口"
    echo "  $0 -p 8125          # 前台运行，使用端口8125"
    echo "  $0 -d               # 后台运行，使用默认端口"
    echo "  $0 -d -p 8125       # 后台运行，使用端口8125"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python 未安装或不在 PATH 中"
        exit 1
    fi
    
    # 确定 Python 命令
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi
    
    # 检查服务器文件
    if [ ! -f "$SCRIPT_DIR/$SERVER_FILE" ]; then
        print_error "服务器文件 $SERVER_FILE 不存在"
        exit 1
    fi
    
    # 检查 Python 包
    print_info "检查 Python 依赖包..."
    missing_packages=()
    
    for package in "akshare" "httpx" "uvicorn" "pandas"; do
        if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
            missing_packages+=($package)
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_warning "缺少以下 Python 包: ${missing_packages[*]}"
        print_info "正在安装缺少的包..."
        
        if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
            pip install -r "$SCRIPT_DIR/requirements.txt"
        else
            pip install ${missing_packages[*]}
        fi
        
        if [ $? -ne 0 ]; then
            print_error "依赖包安装失败"
            exit 1
        fi
    fi
    
    print_success "依赖检查完成"
}

# 检查服务是否已运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            return 0  # 服务正在运行
        else
            # PID 文件存在但进程不存在，清理 PID 文件
            rm -f "$PID_FILE"
            return 1  # 服务未运行
        fi
    else
        return 1  # 服务未运行
    fi
}

# 启动服务
start_service() {
    local port=$1
    local host=$2
    local daemon_mode=$3
    
    print_info "启动股票 MCP 服务..."
    
    # 检查是否已运行
    if check_running; then
        local pid=$(cat "$PID_FILE")
        print_warning "服务已在运行 (PID: $pid)"
        print_info "如需重启，请先运行: ./stop.sh"
        exit 1
    fi
    
    # 构建启动命令
    local cmd="$PYTHON_CMD $SCRIPT_DIR/$SERVER_FILE --port $port --host $host"
    
    if [ "$daemon_mode" = true ]; then
        # 后台运行模式
        print_info "以后台模式启动服务..."
        print_info "端口: $port"
        print_info "主机: $host"
        print_info "日志文件: $LOG_FILE"
        
        # 启动服务并记录 PID
        nohup $cmd > "$LOG_FILE" 2>&1 &
        local pid=$!
        echo $pid > "$PID_FILE"
        
        # 等待一下确保服务启动
        sleep 2
        
        if ps -p $pid > /dev/null 2>&1; then
            print_success "服务启动成功 (PID: $pid)"
            print_info "服务地址: http://$host:$port"
            print_info "查看日志: tail -f $LOG_FILE"
            print_info "停止服务: ./stop.sh"
        else
            print_error "服务启动失败"
            rm -f "$PID_FILE"
            exit 1
        fi
    else
        # 前台运行模式
        print_info "以前台模式启动服务..."
        print_info "端口: $port"
        print_info "主机: $host"
        print_info "按 Ctrl+C 停止服务"
        echo ""
        
        # 记录 PID（用于信号处理）
        echo $$ > "$PID_FILE"
        
        # 设置信号处理
        trap 'print_info "正在停止服务..."; rm -f "$PID_FILE"; exit 0' INT TERM
        
        # 启动服务
        exec $cmd
    fi
}

# 主函数
main() {
    local port=$DEFAULT_PORT
    local host=$DEFAULT_HOST
    local daemon_mode=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                port="$2"
                shift 2
                ;;
            -h|--host)
                host="$2"
                shift 2
                ;;
            -d|--daemon)
                daemon_mode=true
                shift
                ;;
            -f|--foreground)
                daemon_mode=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 验证端口号
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        print_error "无效的端口号: $port"
        exit 1
    fi
    
    print_info "=== 股票 MCP 服务启动脚本 ==="
    
    # 检查依赖
    check_dependencies
    
    # 启动服务
    start_service "$port" "$host" "$daemon_mode"
}

# 运行主函数
main "$@"
