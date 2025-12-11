#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包纯文字聊天Python调用脚本
用于调用Node.js脚本进行纯文字聊天，不涉及图片
"""

import subprocess
import json
import sys
import os
import time

class DoubaoTextChat:
    def __init__(self, node_script_path):
        """
        初始化豆包纯文字聊天类
        :param node_script_path: Node.js脚本路径
        """
        self.node_script_path = node_script_path
        if not os.path.exists(node_script_path):
            raise FileNotFoundError(f"Node.js脚本不存在: {node_script_path}")
    
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
            cmd = [
                "node", 
                self.node_script_path,
                message,
                "--headless",
                str(headless).lower()  # 将布尔值转换为字符串并转为小写
            ]
            
            # 执行命令并获取输出
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 延长超时时间为5分钟
            )
            
            if result.returncode != 0:
                print(f"Node.js脚本执行失败，返回码: {result.returncode}")
                print(f"错误输出: {result.stderr}")
                print(f"标准输出: {result.stdout}")
                return None
            
            print(f"完整输出: {result.stdout}")
            
            # 解析JSON输出（从输出中提取JSON部分）
            try:
                # 找到JSON的起始位置（第一个{）
                json_start = result.stdout.find('{')
                if json_start == -1:
                    print("未找到JSON数据")
                    return None
                
                # 找到JSON的结束位置（最后一个}）
                json_end = result.stdout.rfind('}') + 1
                if json_end <= json_start:
                    print("未找到完整的JSON数据")
                    return None
                
                # 提取JSON部分
                json_str = result.stdout[json_start:json_end]
                print(f"提取的JSON字符串: {json_str}")
                
                # 解析JSON
                output_data = json.loads(json_str)
                print(f"解析后的JSON数据: {output_data}")
                return output_data
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"错误位置: {e.pos}")
                print(f"原始输出: {result.stdout}")
                print(f"JSON部分: {json_str}")
                return None
                
        except subprocess.TimeoutExpired:
            print("脚本执行超时")
            return None
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
    
    parser = argparse.ArgumentParser(description="豆包纯文字聊天工具")
    parser.add_argument("message", help="要发送的消息")
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_node_script = os.path.join(script_dir, "doubao_chat_bot.js")
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