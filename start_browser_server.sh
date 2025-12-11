#!/bin/bash

# 豆包浏览器服务启动脚本

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

# 显示启动信息
echo "=== 豆包浏览器服务启动脚本 ==="
echo "服务文件: $SERVER_FILE"
echo "启动命令: node $SERVER_FILE"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务
node "$SERVER_FILE"
