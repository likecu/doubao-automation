#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包纯文字聊天Python调用脚本
用于通过浏览器服务器进行纯文字聊天，不涉及图片
"""

import json
import os
from doubao_browser_client import DoubaoBrowserClient

class DoubaoTextChat:
    def __init__(self, server_url="http://localhost:3000"):
        """
        初始化豆包纯文字聊天类
        :param server_url: 浏览器服务器地址，默认为 http://localhost:3000
        """
        self.client = DoubaoBrowserClient(server_url)
    
    def send_message(self, message, headless=True):
        """
        通过浏览器服务器发送纯文字消息
        :param message: 要发送的消息
        :param headless: 是否使用无头模式（已废弃，由服务器端控制）
        :return: 回复结果字典
        """
        if not message:
            raise ValueError("消息不能为空")
        
        print(f"开始发送消息: {message}")
        
        try:
            # 检查服务器状态
            if not self.client.is_server_running():
                print("浏览器服务器未运行，请先启动服务器")
                print("启动命令: node browser_server.js")
                return None
            
            # 创建新页面
            page_id = self.client.create_page()
            if not page_id:
                print("创建页面失败")
                return None
            
            try:
                # 执行纯文本聊天
                result = self.client.text_chat(page_id, message)
                return result
            finally:
                # 关闭页面
                self.client.close_page(page_id)
                
        except Exception as e:
            print(f"调用服务器时发生错误: {e}")
            return None
    
    def get_response(self, message, headless=True):
        """
        获取纯文字消息的回复
        :param message: 要发送的消息
        :param headless: 是否使用无头模式（已废弃，由服务器端控制）
        :return: 回复文本
        """
        result = self.send_message(message, headless=headless)
        if result and result.get("success"):
            return result.get("response", "")
        return "回复失败"


def main():
    """
    主函数，用于命令行调用
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="豆包纯文字聊天工具")
    parser.add_argument("message", help="要发送的消息")
    parser.add_argument("--server", default="http://localhost:3000", help="浏览器服务器地址")
    # 保留headless参数以保持兼容性，但实际上由服务器端控制
    parser.add_argument("--headless", type=lambda x: x.lower() in ['true', 'yes', '1'], default=True, help="是否使用无头模式（不显示浏览器界面），可选值：true/false/yes/no/1/0")
    
    args = parser.parse_args()
    
    # 创建纯文字聊天实例
    chat = DoubaoTextChat(args.server)
    
    # 发送消息
    result = chat.send_message(args.message, headless=args.headless)
    
    if result:
        print("\n=== 聊天结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 提取关键信息
        if result.get("success"):
            print("\n=== 关键信息 ===")
            print(f"消息: {result.get('message', '')}")
            print(f"回复: {result.get('response', '')}")
            
            # 提取聊天历史
            chat_history = result.get('chatHistory', [])
            print(f"\n聊天记录数量: {len(chat_history)}")
    else:
        print("发送消息失败")


if __name__ == "__main__":
    main()