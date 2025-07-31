#!/bin/bash

# 股票 MCP 服务停止脚本
# Stock MCP Server Stop Script

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/stock_mcp.pid"
LOG_FILE="$SCRIPT_DIR/stock_mcp.log"

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
    echo "股票 MCP 服务停止脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -f, --force         强制停止服务"
    echo "  -s, --status        显示服务状态"
    echo "  -l, --logs          显示最近的日志"
    echo "  --clean             清理日志和PID文件"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                  # 正常停止服务"
    echo "  $0 -f               # 强制停止服务"
    echo "  $0 -s               # 查看服务状态"
    echo "  $0 -l               # 查看最近日志"
    echo "  $0 --clean          # 清理文件"
}

# 检查服务状态
check_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            return 0  # 服务正在运行
        else
            return 1  # 服务未运行（但PID文件存在）
        fi
    else
        return 2  # 服务未运行（PID文件不存在）
    fi
}

# 显示服务状态
show_status() {
    print_info "=== 股票 MCP 服务状态 ==="
    
    local status_code
    check_status
    status_code=$?
    
    case $status_code in
        0)
            local pid=$(cat "$PID_FILE")
            print_success "服务正在运行 (PID: $pid)"
            
            # 显示进程信息
            if command -v ps &> /dev/null; then
                echo ""
                print_info "进程信息:"
                ps -p $pid -o pid,ppid,cmd,etime,pcpu,pmem 2>/dev/null || true
            fi
            
            # 显示端口信息
            if command -v netstat &> /dev/null; then
                echo ""
                print_info "监听端口:"
                netstat -tlnp 2>/dev/null | grep $pid 2>/dev/null || print_warning "无法获取端口信息"
            elif command -v lsof &> /dev/null; then
                echo ""
                print_info "监听端口:"
                lsof -p $pid -i TCP 2>/dev/null || print_warning "无法获取端口信息"
            fi
            ;;
        1)
            local pid=$(cat "$PID_FILE")
            print_warning "服务未运行，但PID文件存在 (PID: $pid)"
            print_info "建议运行: $0 --clean"
            ;;
        2)
            print_info "服务未运行"
            ;;
    esac
    
    # 显示日志文件信息
    if [ -f "$LOG_FILE" ]; then
        local log_size=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1)
        local log_lines=$(wc -l < "$LOG_FILE" 2>/dev/null)
        echo ""
        print_info "日志文件: $LOG_FILE"
        print_info "日志大小: $log_size, 行数: $log_lines"
    fi
}

# 显示最近日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_info "=== 最近的日志 (最后50行) ==="
        tail -n 50 "$LOG_FILE"
    else
        print_warning "日志文件不存在: $LOG_FILE"
    fi
}

# 停止服务
stop_service() {
    local force_mode=$1
    
    print_info "停止股票 MCP 服务..."
    
    local status_code
    check_status
    status_code=$?
    
    case $status_code in
        0)
            local pid=$(cat "$PID_FILE")
            print_info "发现运行中的服务 (PID: $pid)"
            
            if [ "$force_mode" = true ]; then
                print_warning "强制停止服务..."
                kill -9 $pid 2>/dev/null
            else
                print_info "正常停止服务..."
                kill -TERM $pid 2>/dev/null
                
                # 等待进程结束
                local count=0
                while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                    sleep 1
                    count=$((count + 1))
                    echo -n "."
                done
                echo ""
                
                # 如果进程仍在运行，强制停止
                if ps -p $pid > /dev/null 2>&1; then
                    print_warning "正常停止失败，强制停止服务..."
                    kill -9 $pid 2>/dev/null
                    sleep 1
                fi
            fi
            
            # 验证进程是否已停止
            if ps -p $pid > /dev/null 2>&1; then
                print_error "停止服务失败"
                exit 1
            else
                print_success "服务已停止"
                rm -f "$PID_FILE"
            fi
            ;;
        1)
            local pid=$(cat "$PID_FILE")
            print_warning "服务未运行，但PID文件存在 (PID: $pid)"
            print_info "清理PID文件..."
            rm -f "$PID_FILE"
            print_success "PID文件已清理"
            ;;
        2)
            print_info "服务未运行"
            ;;
    esac
}

# 清理文件
clean_files() {
    print_info "清理股票 MCP 服务文件..."
    
    # 先尝试停止服务
    if check_status; then
        print_warning "服务正在运行，先停止服务..."
        stop_service false
    fi
    
    # 清理PID文件
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
        print_success "已删除PID文件: $PID_FILE"
    fi
    
    # 询问是否删除日志文件
    if [ -f "$LOG_FILE" ]; then
        echo -n "是否删除日志文件? [y/N]: "
        read -r response
        case $response in
            [yY]|[yY][eE][sS])
                rm -f "$LOG_FILE"
                print_success "已删除日志文件: $LOG_FILE"
                ;;
            *)
                print_info "保留日志文件: $LOG_FILE"
                ;;
        esac
    fi
    
    print_success "清理完成"
}

# 主函数
main() {
    local force_mode=false
    local show_status_only=false
    local show_logs_only=false
    local clean_only=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--force)
                force_mode=true
                shift
                ;;
            -s|--status)
                show_status_only=true
                shift
                ;;
            -l|--logs)
                show_logs_only=true
                shift
                ;;
            --clean)
                clean_only=true
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
    
    print_info "=== 股票 MCP 服务停止脚本 ==="
    
    # 根据参数执行相应操作
    if [ "$show_status_only" = true ]; then
        show_status
    elif [ "$show_logs_only" = true ]; then
        show_logs
    elif [ "$clean_only" = true ]; then
        clean_files
    else
        stop_service "$force_mode"
    fi
}

# 运行主函数
main "$@"
