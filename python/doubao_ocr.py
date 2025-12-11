#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包聊天OCR识别Python调用脚本
用于调用豆包浏览器服务器进行图片OCR识别，返回识别结果
"""

import os
from doubao_browser_client import DoubaoBrowserClient
from doubao_common import validate_file_path

class DoubaoOCR:
    def __init__(self, server_url="http://localhost:3000"):
        """
        初始化豆包OCR识别类
        :param server_url: 浏览器服务器地址，默认为 http://localhost:3000
        """
        self.client = DoubaoBrowserClient(server_url)
    
    def recognize_image(self, image_path, question="图里有什么内容？", headless=True):
        """
        通过浏览器服务器识别图片内容
        :param image_path: 图片路径
        :param question: 向豆包提问的问题
        :param headless: 是否使用无头模式（已废弃，由服务器端控制）
        :return: 识别结果字典
        """
        # 验证并获取绝对路径
        image_path = validate_file_path(image_path)
        
        print(f"开始识别图片: {image_path}")
        print(f"提问内容: {question}")
        
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
                # 执行OCR识别
                result = self.client.ocr(page_id, image_path, question)
                return result
            finally:
                # 关闭页面
                self.client.close_page(page_id)
                
        except Exception as e:
            print(f"调用服务器时发生错误: {e}")
            return None
    
    def get_ocr_result(self, image_path, question="图里有什么内容？", headless=True):
        """
        获取OCR识别结果
        :param image_path: 图片路径
        :param question: 向豆包提问的问题
        :param headless: 是否使用无头模式（已废弃，由服务器端控制）
        :return: 识别结果字符串
        """
        result = self.recognize_image(image_path, question, headless=headless)
        if result and result.get("success"):
            return result.get("response", "")
        return "识别失败"


def main():
    """
    主函数，用于命令行调用
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="豆包图片OCR识别工具")
    parser.add_argument("image_path", help="图片路径")
    parser.add_argument("--question", default="图里有什么内容？", help="提问内容")
    parser.add_argument("--server", default="http://localhost:3000", help="浏览器服务器地址")
    # 保留headless参数以保持兼容性，但实际上由服务器端控制
    parser.add_argument("--headless", type=lambda x: x.lower() in ['true', 'yes', '1'], default=True, help="是否使用无头模式（不显示浏览器界面），可选值：true/false/yes/no/1/0")
    
    args = parser.parse_args()
    
    # 创建OCR实例
    ocr = DoubaoOCR(args.server)
    
    # 执行识别
    result = ocr.recognize_image(args.image_path, args.question, headless=args.headless)
    
    if result:
        print("\n=== 识别结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 提取关键信息
        if result.get("success"):
            print("\n=== 关键信息 ===")
            print(f"提问: {result.get('message', '')}")
            print(f"回复: {result.get('response', '')}")
            
            # 提取聊天历史
            chat_history = result.get('chatHistory', [])
            print(f"\n聊天记录数量: {len(chat_history)}")
            
            # 打印每条聊天记录
            for i, msg in enumerate(chat_history):
                print(f"\n消息 {i+1}:")
                print(f"  类型: {msg.get('type', '')}")
                print(f"  内容: {msg.get('content', '')}")
                print(f"  时间: {msg.get('timestamp', '')}")
    else:
        print("识别失败")


if __name__ == "__main__":
    main()