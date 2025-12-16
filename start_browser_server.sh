#!/bin/bash

# 豆包浏览器服务综合启动脚本
# 支持有头模式、调试模式和无头模式

# 切换到脚本所在目录
SCRIPT_DIR=$(dirname "$(realpath "$0")")
cd "$SCRIPT_DIR"

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "错误: Node.js未安装，请先安装Node.js"
    exit 1
fi

# 检查browser_server.js是否存在
SERVER_FILE="js/browser_server.js"
if [ ! -f "$SERVER_FILE" ]; then
    echo "错误: 找不到浏览器服务器文件: $SERVER_FILE"
    echo "请确保文件存在，或者从源代码重新构建"
    exit 1
fi

# 解析命令行参数
echo "=== 解析启动参数 ==="

# 默认值
DEBUG_MODE=false
HEADLESS_MODE=false
PORT=3000

# 解析参数
for arg in "$@"; do
    case $arg in
        --debug|-d)
            DEBUG_MODE=true
            HEADLESS_MODE=false
            echo "  ✅ 启用DEBUG模式"
            ;;
        --headless|-h)
            HEADLESS_MODE=true
            echo "  ✅ 启用无头模式"
            ;;
        --no-headless|-nh)
            HEADLESS_MODE=false
            echo "  ✅ 强制有头模式"
            ;;
        --port|-p)
            PORT="${2}"
            shift # 跳过值
            echo "  ✅ 自定义端口: ${PORT}"
            ;;
        --help|-?)
            echo "=== 豆包浏览器服务启动脚本帮助 ==="
            echo "使用方法: ./start_browser_server.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --debug, -d          启用DEBUG模式（有头模式+调试器）"
            echo "  --headless, -h       启用无头模式"
            echo "  --no-headless, -nh   强制有头模式"
            echo "  --port, -p <端口>    自定义服务端口（默认: 3000）"
            echo "  --help, -?           显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  ./start_browser_server.sh           # 默认有头模式"
            echo "  ./start_browser_server.sh -d        # 调试模式（有头+调试器）"
            echo "  ./start_browser_server.sh -h        # 无头模式"
            echo "  ./start_browser_server.sh -p 3001   # 自定义端口"
            exit 0
            ;;
        *)
            echo "  ⚠️  未知参数: $arg"
            echo "  使用 --help 查看可用选项"
            ;;
    esac
done

# 停止正在运行的相同端口服务
echo ""
echo "=== 检查并停止正在运行的${PORT}端口服务 ==="
PID=$(lsof -i:${PORT} -t)
if [ -n "$PID" ]; then
    echo "  ⚠️  找到正在运行的${PORT}端口服务，PID: $PID"
    echo "  🛑 正在停止服务..."
    kill -9 $PID
    if [ $? -eq 0 ]; then
        echo "  ✅ 服务已成功停止"
    else
        echo "  ❌ 停止服务失败，请手动检查"
        exit 1
    fi
else
    echo "  ✅ 没有找到正在运行的${PORT}端口服务"
fi

# 构建启动命令
echo ""
echo "=== 构建启动命令 ==="

# 基础命令
START_CMD="node"

# 添加调试选项
if [ "$DEBUG_MODE" = true ]; then
    START_CMD="$START_CMD --inspect=9229"
    echo "  🛠️  调试端口: 9229"
fi

# 添加脚本路径
START_CMD="$START_CMD \"$SERVER_FILE\""

# 添加浏览器模式选项
if [ "$HEADLESS_MODE" = true ]; then
    START_CMD="$START_CMD --headless"
    MODE="无头模式"
elif [ "$DEBUG_MODE" = true ]; then
    START_CMD="$START_CMD --debug"
    MODE="DEBUG模式（有头）"
else
    START_CMD="$START_CMD --no-headless"
    MODE="有头模式"
fi

# 显示启动信息
echo ""
echo "=== 豆包浏览器服务启动 ==="
echo "  服务文件: $SERVER_FILE"
echo "  启动端口: ${PORT}"
echo "  启动模式: ${MODE}"
echo "  启动命令: $START_CMD"
echo "  按 Ctrl+C 停止服务"
echo ""
echo "  🚀 正在启动服务..."
echo ""

# 执行启动命令
eval $START_CMD
