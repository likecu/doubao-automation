#!/bin/bash

# 豆包AI标准接口服务启动脚本
echo "=== 启动豆包AI标准接口服务 ==="
echo "正在检查依赖..."

# 检查node.js是否安装
if ! command -v node &> /dev/null; then
    echo "错误: Node.js 未安装，请先安装 Node.js"
    exit 1
fi

# 检查npm是否安装
if ! command -v npm &> /dev/null; then
    echo "错误: npm 未安装，请先安装 npm"
    exit 1
fi

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install express cors
fi

echo "正在启动AI标准接口服务..."
echo "服务地址: http://localhost:3001"
echo "按 Ctrl+C 停止服务"
echo "=============================="

# 启动服务
node js/ai_server.js