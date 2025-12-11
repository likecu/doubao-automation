#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包浏览器客户端
用于与豆包浏览器服务器通信，实现浏览器复用功能
"""

import requests
import json
import time
import os
from typing import Dict, Optional, List

class DoubaoBrowserClient:
    """
    豆包浏览器客户端类
    用于与豆包浏览器服务器通信，实现浏览器复用功能
    """
    
    def __init__(self, server_url: str = "http://localhost:3000"):
        """
        初始化豆包浏览器客户端
        :param server_url: 浏览器服务器地址，默认为 http://localhost:3000
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
    def get_status(self) -> Dict:
        """
        获取服务器状态
        :return: 服务器状态信息
        """
        url = f"{self.server_url}/status"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"获取服务器状态失败: {str(e)}"
            }
    
    def create_page(self) -> Optional[int]:
        """
        创建新页面
        :return: 页面ID，如果失败返回None
        """
        url = f"{self.server_url}/createPage"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                return result.get("pageId")
            return None
        except requests.RequestException as e:
            print(f"创建页面失败: {str(e)}")
            return None
    
    def close_page(self, page_id: int) -> bool:
        """
        关闭指定页面
        :param page_id: 页面ID
        :return: 是否成功关闭
        """
        url = f"{self.server_url}/closePage?pageId={page_id}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except requests.RequestException as e:
            print(f"关闭页面 {page_id} 失败: {str(e)}")
            return False
    
    def close_all_pages(self) -> bool:
        """
        关闭所有页面
        :return: 是否成功关闭
        """
        url = f"{self.server_url}/closeAllPages"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except requests.RequestException as e:
            print(f"关闭所有页面失败: {str(e)}")
            return False
    
    def send_message(self, page_id: int, message: str) -> bool:
        """
        发送文本消息
        :param page_id: 页面ID
        :param message: 消息内容
        :return: 是否发送成功
        """
        url = f"{self.server_url}/sendMessage"
        data = {
            "pageId": page_id,
            "message": message
        }
        try:
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except requests.RequestException as e:
            print(f"发送消息失败: {str(e)}")
            return False
    
    def upload_file(self, page_id: int, file_path: str) -> bool:
        """
        上传文件
        :param page_id: 页面ID
        :param file_path: 文件路径
        :return: 是否上传成功
        """
        # 验证文件路径
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
        
        # 转换为绝对路径
        file_path = os.path.abspath(file_path)
        
        url = f"{self.server_url}/uploadFile"
        data = {
            "pageId": page_id,
            "filePath": file_path
        }
        try:
            response = self.session.post(url, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except requests.RequestException as e:
            print(f"上传文件失败: {str(e)}")
            return False
    
    def send_message_with_file(self, page_id: int, message: str, file_path: str) -> bool:
        """
        发送包含文件的消息
        :param page_id: 页面ID
        :param message: 消息内容
        :param file_path: 文件路径
        :return: 是否发送成功
        """
        # 验证文件路径
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
        
        # 转换为绝对路径
        file_path = os.path.abspath(file_path)
        
        url = f"{self.server_url}/sendMessageWithFile"
        data = {
            "pageId": page_id,
            "message": message,
            "filePath": file_path
        }
        try:
            response = self.session.post(url, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except requests.RequestException as e:
            print(f"发送包含文件的消息失败: {str(e)}")
            return False
    
    def get_ai_response(self, page_id: int) -> Optional[str]:
        """
        获取AI回复
        :param page_id: 页面ID
        :return: AI回复内容，如果失败返回None
        """
        url = f"{self.server_url}/getAIResponse"
        data = {
            "pageId": page_id
        }
        try:
            response = self.session.post(url, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                return result.get("response")
            return None
        except requests.RequestException as e:
            print(f"获取AI回复失败: {str(e)}")
            return None
    
    def extract_chat_history(self, page_id: int) -> List[Dict]:
        """
        提取聊天记录
        :param page_id: 页面ID
        :return: 聊天记录列表
        """
        url = f"{self.server_url}/extractChatHistory"
        data = {
            "pageId": page_id
        }
        try:
            response = self.session.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                return result.get("chatHistory", [])
            return []
        except requests.RequestException as e:
            print(f"提取聊天记录失败: {str(e)}")
            return []
    
    def ocr(self, page_id: int, image_path: str, question: str = "图里有什么内容？") -> Dict:
        """
        执行OCR识别
        :param page_id: 页面ID
        :param image_path: 图片路径
        :param question: 提问内容，默认为"图里有什么内容？"
        :return: OCR识别结果
        """
        # 验证文件路径
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": f"图片不存在: {image_path}"
            }
        
        # 转换为绝对路径
        image_path = os.path.abspath(image_path)
        
        url = f"{self.server_url}/ocr"
        data = {
            "pageId": page_id,
            "imagePath": image_path,
            "question": question
        }
        try:
            response = self.session.post(url, json=data, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"OCR识别失败: {str(e)}"
            }
    
    def text_chat(self, page_id: int, message: str) -> Dict:
        """
        纯文本聊天
        :param page_id: 页面ID
        :param message: 聊天消息
        :return: 聊天结果
        """
        url = f"{self.server_url}/textChat"
        data = {
            "pageId": page_id,
            "message": message
        }
        try:
            response = self.session.post(url, json=data, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"纯文本聊天失败: {str(e)}"
            }
    
    def is_server_running(self) -> bool:
        """
        检查服务器是否正在运行
        :return: 服务器是否正在运行
        """
        status = self.get_status()
        return status.get("success", False) and status.get("running", False)


def main():
    """
    主函数，用于测试客户端功能
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="豆包浏览器客户端测试工具")
    parser.add_argument("--server", default="http://localhost:3000", help="浏览器服务器地址")
    parser.add_argument("--test", action="store_true", help="执行测试")
    parser.add_argument("--image", help="测试OCR的图片路径")
    parser.add_argument("--question", default="图里有什么内容？", help="OCR提问内容")
    
    args = parser.parse_args()
    
    # 创建客户端实例
    client = DoubaoBrowserClient(args.server)
    
    # 检查服务器状态
    print("检查服务器状态...")
    status = client.get_status()
    print(f"服务器状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    if not status.get("success"):
        print("服务器未运行或无法访问，请先启动浏览器服务器")
        print("启动命令: node browser_server.js")
        return
    
    if args.test:
        print("\n=== 开始测试客户端功能 ===")
        
        # 1. 创建页面
        print("\n1. 创建页面...")
        page_id = client.create_page()
        if not page_id:
            print("创建页面失败")
            return
        print(f"创建页面成功，页面ID: {page_id}")
        
        # 2. 测试纯文本聊天
        print("\n2. 测试纯文本聊天...")
        chat_result = client.text_chat(page_id, "你好，豆包")
        print(f"聊天结果: {json.dumps(chat_result, indent=2, ensure_ascii=False)}")
        
        # 3. 测试OCR（如果提供了图片）
        if args.image:
            print("\n3. 测试OCR识别...")
            ocr_result = client.ocr(page_id, args.image, args.question)
            print(f"OCR结果: {json.dumps(ocr_result, indent=2, ensure_ascii=False)}")
        
        # 4. 关闭页面
        print("\n4. 关闭页面...")
        if client.close_page(page_id):
            print("页面关闭成功")
        else:
            print("页面关闭失败")
        
        print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()
