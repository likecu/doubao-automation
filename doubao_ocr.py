#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包聊天OCR识别Python调用脚本
用于调用Node.js脚本进行图片OCR识别，返回识别结果
"""

import subprocess
import json
import sys
import os
import time

class DoubaoOCR:
    def __init__(self, node_script_path):
        """
        初始化豆包OCR识别类
        :param node_script_path: Node.js脚本路径
        """
        self.node_script_path = node_script_path
        if not os.path.exists(node_script_path):
            raise FileNotFoundError(f"Node.js脚本不存在: {node_script_path}")
    
    def recognize_image(self, image_path, question="图里有什么内容？", headless=True):
        """
        调用Node.js脚本识别图片内容
        :param image_path: 图片路径
        :param question: 向豆包提问的问题
        :param headless: 是否使用无头模式（默认为True，不显示浏览器界面）
        :return: 识别结果字典
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        # 确保路径是绝对路径
        image_path = os.path.abspath(image_path)
        
        print(f"开始识别图片: {image_path}")
        print(f"提问内容: {question}")
        
        try:
            # 调用Node.js脚本
            cmd = [
                "node", 
                self.node_script_path,
                "--image", image_path,
                "--question", question,
                "--headless", str(headless).lower()  # 将布尔值转换为字符串并转为小写
            ]
            
            # 执行命令并获取输出
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 设置超时时间为60秒
            )
            
            if result.returncode != 0:
                print(f"Node.js脚本执行失败: {result.stderr}")
                return None
            
            print(f"脚本输出: {result.stdout}")
            
            # 从输出中提取JSON部分
            try:
                # 查找第一个JSON开始位置
                start_idx = result.stdout.find('{')
                if start_idx == -1:
                    print("未找到JSON格式的输出")
                    return None
                
                # 查找最后一个JSON结束位置
                end_idx = result.stdout.rfind('}')
                if end_idx == -1:
                    print("未找到JSON结束标记")
                    return None
                
                # 提取JSON部分
                json_str = result.stdout[start_idx:end_idx + 1]
                print(f"提取到的JSON: {json_str}")
                
                # 解析JSON
                output_data = json.loads(json_str)
                return output_data
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"原始输出: {result.stdout}")
                return None
                
        except subprocess.TimeoutExpired:
            print("脚本执行超时")
            return None
        except Exception as e:
            print(f"调用脚本时发生错误: {e}")
            return None
    
    def get_ocr_result(self, image_path, question="图里有什么内容？", headless=True):
        """
        获取OCR识别结果
        :param image_path: 图片路径
        :param question: 向豆包提问的问题
        :param headless: 是否使用无头模式（默认为True，不显示浏览器界面）
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
    
    parser = argparse.ArgumentParser(description="豆包图片OCR识别工具")
    parser.add_argument("image_path", help="图片路径")
    parser.add_argument("--question", default="图里有什么内容？", help="提问内容")
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_node_script = os.path.join(script_dir, "test_upload_image.js")
    parser.add_argument("--node_script", default=default_node_script, help="Node.js脚本路径")
    parser.add_argument("--headless", type=lambda x: x.lower() in ['true', 'yes', '1'], default=True, help="是否使用无头模式（不显示浏览器界面），可选值：true/false/yes/no/1/0")
    
    args = parser.parse_args()
    
    # 创建OCR实例
    ocr = DoubaoOCR(args.node_script)
    
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