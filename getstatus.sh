#!/bin/bash

# 辅助函数：尝试curl请求
function try_curl() {
    local url=$1
    local desc=$2
    
    echo -n "   ${desc}... "
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" = "200" ]; then
        echo "✅ 成功 (状态码: $response)"
        # 打印响应内容
        curl -s "$url" | jq . 2>/dev/null || curl -s "$url"
        return 0
    else
        echo "❌ 失败 (状态码: $response)"
        return 1
    fi
}

# 辅助函数：发送聊天请求
function send_chat_request() {
    local url=$1
    local message=$2
    local desc=$3
    
    echo -n "   ${desc}... "
    
    # 创建页面
    local create_page_response=$(curl -s "http://localhost:3000/createPage")
    local page_id=$(echo $create_page_response | jq -r '.pageId' 2>/dev/null)
    
    if [ -z "$page_id" ] || [ "$page_id" = "null" ]; then
        echo "❌ 失败：无法创建页面"
        echo "   错误：$create_page_response"
        return 1
    fi
    
    # 发送消息
    local send_response=$(curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "{\"pageId\": $page_id, \"message\": \"$message\"}")
    
    if echo $send_response | jq -e '.success' > /dev/null 2>&1; then
        echo "✅ 成功发送消息"
        
        # 获取AI回复
        echo -n "   获取AI回复... "
        local ai_response=$(curl -s -X POST "http://localhost:3000/getAIResponse" \
            -H "Content-Type: application/json" \
            -d "{\"pageId\": $page_id}")
        
        local ai_content=$(echo $ai_response | jq -r '.response' 2>/dev/null)
        if [ -z "$ai_content" ] || [ "$ai_content" = "null" ]; then
            ai_content=$ai_response
        fi
        
        echo "✅ 成功获取回复"
        echo "   AI回复：$ai_content"
        
        # 关闭页面
        curl -s "http://localhost:3000/closePage?pageId=$page_id" > /dev/null
        return 0
    else
        echo "❌ 失败：无法发送消息"
        echo "   错误：$send_response"
        # 关闭页面
        curl -s "http://localhost:3000/closePage?pageId=$page_id" > /dev/null
        return 1
    fi
}

# 豆包服务状态检查脚本

echo "=== 豆包服务状态检查 ==="
echo "检查时间: $(date)"
echo ""

# 检查3000端口服务状态（浏览器服务）
echo "1. 检查3000端口服务状态（浏览器服务）:"
if try_curl "http://localhost:3000/status" "状态查询"; then
    # 如果服务正常，发送测试消息
    echo ""
    echo "2. 测试浏览器服务聊天功能:"
    send_chat_request "http://localhost:3000/textChat" "地球是圆的吗？" "提问：地球是圆的吗？"
else
    echo "   ⚠️  服务不可用，跳过聊天测试"
fi

# 检查3001端口服务状态（AI接口服务）
echo ""
echo "3. 检查3001端口服务状态（AI接口服务）:"
try_curl "http://localhost:3001/health" "健康检查"

echo ""
echo "4. 检查端口占用情况:"
lsof -i :3000 -i :3001 || echo "   没有服务在3000或3001端口运行"

echo ""
echo "5. 检查相关Node.js进程:"
ps aux | grep -E "ai_server|browser_server" | grep -v grep || echo "   没有找到ai_server或browser_server进程"

echo ""
echo "=== 检查完成 ==="
