#!/usr/bin/env /Volumes/600g/app1/okx-py/bin/python3

import requests
import json
import sys

def test_mcp_port_3001():
    """
    测试mcp是否能使用3001端口
    """
    print("=== 测试mcp是否能使用3001端口 ===")
    
    base_url = "http://localhost:3001"
    
    success_count = 0
    total_tests = 4
    
    try:
        # 测试1：健康检查接口
        print("\n1. 测试健康检查接口...")
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code == 200:
            print(f"✅ 健康检查成功: {health_response.json()}")
            success_count += 1
        else:
            print(f"❌ 健康检查失败: 状态码 {health_response.status_code}")
        
        # 测试2：聊天补全接口
        print("\n2. 测试聊天补全接口...")
        chat_data = {
            "messages": [
                {"role": "user", "content": "你好，测试mcp 3001端口"}
            ]
        }
        chat_response = requests.post(f"{base_url}/v1/chat/completions", json=chat_data)
        if chat_response.status_code == 200:
            chat_result = chat_response.json()
            print(f"✅ 聊天补全成功: {chat_result['choices'][0]['message']['content']}")
            success_count += 1
        else:
            print(f"❌ 聊天补全失败: 状态码 {chat_response.status_code}")
        
        # 测试3：OCR识别接口结构
        print("\n3. 测试OCR识别接口结构...")
        ocr_response = requests.post(f"{base_url}/v1/ocr/recognize", json={})
        if ocr_response.status_code == 400:
            print("✅ OCR接口存在，返回了预期的400错误")
            success_count += 1
        else:
            print(f"❌ OCR接口测试失败: 状态码 {ocr_response.status_code}")
        
        # 测试4：是/否判断接口结构
        print("\n4. 测试是/否判断接口结构...")
        mod_response = requests.post(f"{base_url}/v1/moderations", json={})
        if mod_response.status_code == 400:
            print("✅ 是/否判断接口存在，返回了预期的400错误")
            success_count += 1
        else:
            print(f"❌ 是/否判断接口测试失败: 状态码 {mod_response.status_code}")
        
        # 测试总结
        print("\n=== 测试总结 ===")
        print(f"测试结果: {success_count}/{total_tests} 测试通过")
        
        if success_count == total_tests:
            print("✅ 所有测试通过！mcp可以正常使用3001端口")
            print(f"✅ 服务地址: {base_url}")
            print(f"✅ 可用API:")
            print(f"   - GET  /health                     - 健康检查")
            print(f"   - POST /v1/chat/completions        - 聊天补全")
            print(f"   - POST /v1/ocr/recognize           - OCR识别")
            print(f"   - POST /v1/moderations             - 是/否判断")
            print(f"   - POST /v1/files/upload            - 文件上传")
            return 0
        else:
            print(f"❌ 部分测试失败，mcp可能无法正常使用3001端口")
            return 1
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_mcp_port_3001())
