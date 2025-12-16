#!/bin/bash

# 豆包浏览器服务启动脚本（有头模式）

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

# 停止正在运行的3000端口服务
echo "=== 检查并停止正在运行的3000端口服务 ==="
PORT=3000
PID=$(lsof -i:$PORT -t)
if [ -n "$PID" ]; then
    echo "找到正在运行的3000端口服务，PID: $PID"
    echo "正在停止服务..."
    kill -9 $PID
    if [ $? -eq 0 ]; then
        echo "服务已成功停止"
    else
        echo "停止服务失败，请手动检查"
        exit 1
    fi
else
    echo "没有找到正在运行的3000端口服务"
fi

echo ""

# 显示启动信息
echo "=== 豆包浏览器服务启动脚本（有头模式） ==="
echo "服务文件: $SERVER_FILE"
echo "启动端口: 3000"
echo "启动模式: 有头模式"
echo "启动命令: node $SERVER_FILE --no-headless"
echo "按 Ctrl+C 停止服务"
echo ""

# 以有头模式启动服务
node "$SERVER_FILE" --no-headless
