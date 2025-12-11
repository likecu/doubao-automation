#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包纯文字聊天Python调用脚本
用于调用Node.js脚本进行纯文字聊天，不涉及图片
"""

import json
import os
from doubao_common import (
    execute_node_script,
    parse_json_output,
    validate_file_path,
    handle_script_result,
    format_headless_param
)

class DoubaoTextChat:
    def __init__(self, node_script_path):
        """
        初始化豆包纯文字聊天类
        :param node_script_path: Node.js脚本路径
        """
        self.node_script_path = validate_file_path(node_script_path)
    
    def send_message(self, message, headless=True):
        """
        调用Node.js脚本发送纯文字消息
        :param message: 要发送的消息
        :param headless: 是否使用无头模式（默认为True，不显示浏览器界面）
        :return: 回复结果字典
        """
        if not message:
            raise ValueError("消息不能为空")
        
        print(f"开始发送消息: {message}")
        
        try:
            # 调用Node.js脚本
            args = [
                message,
                "--headless",
                format_headless_param(headless)
            ]
            
            # 执行命令并获取输出
            result = execute_node_script(self.node_script_path, args, timeout=300)
            
            # 处理执行结果
            output = handle_script_result(result)
            if output is None:
                return None
            
            print(f"完整输出: {output}")
            
            # 解析JSON输出
            output_data = parse_json_output(output)
            if output_data:
                print(f"解析后的JSON数据: {output_data}")
            return output_data
            
        except Exception as e:
            print(f"调用脚本时发生错误: {e}")
            return None
    
    def get_response(self, message, headless=True):
        """
        获取纯文字消息的回复
        :param message: 要发送的消息
        :param headless: 是否使用无头模式（默认为True，不显示浏览器界面）
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
    from doubao_common import get_default_node_script
    
    parser = argparse.ArgumentParser(description="豆包纯文字聊天工具")
    parser.add_argument("message", help="要发送的消息")
    # 获取默认Node.js脚本路径
    default_node_script = get_default_node_script("doubao_chat_bot.js")
    parser.add_argument("--node_script", default=default_node_script, help="Node.js脚本路径")
    parser.add_argument("--headless", type=lambda x: x.lower() in ['true', 'yes', '1'], default=True, help="是否使用无头模式（不显示浏览器界面），可选值：true/false/yes/no/1/0")
    
    args = parser.parse_args()
    
    # 创建纯文字聊天实例
    chat = DoubaoTextChat(args.node_script)
    
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