#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包聊天OCR识别Python调用脚本
用于调用Node.js脚本进行图片OCR识别，返回识别结果
"""

import os
from doubao_common import (
    execute_node_script,
    parse_json_output,
    validate_file_path,
    handle_script_result,
    format_headless_param
)

class DoubaoOCR:
    def __init__(self, node_script_path):
        """
        初始化豆包OCR识别类
        :param node_script_path: Node.js脚本路径
        """
        self.node_script_path = validate_file_path(node_script_path)
    
    def recognize_image(self, image_path, question="图里有什么内容？", headless=True):
        """
        调用Node.js脚本识别图片内容
        :param image_path: 图片路径
        :param question: 向豆包提问的问题
        :param headless: 是否使用无头模式（默认为True，不显示浏览器界面）
        :return: 识别结果字典
        """
        # 验证并获取绝对路径
        image_path = validate_file_path(image_path)
        
        print(f"开始识别图片: {image_path}")
        print(f"提问内容: {question}")
        
        try:
            # 调用Node.js脚本
            args = [
                "--image", image_path,
                "--question", question,
                "--headless", format_headless_param(headless)
            ]
            
            # 执行命令并获取输出
            result = execute_node_script(self.node_script_path, args, timeout=60)
            
            # 处理执行结果
            output = handle_script_result(result)
            if output is None:
                return None
            
            print(f"脚本输出: {output}")
            
            # 从输出中提取JSON部分
            return parse_json_output(output)
            
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
    import json
    from doubao_common import get_default_node_script
    
    parser = argparse.ArgumentParser(description="豆包图片OCR识别工具")
    parser.add_argument("image_path", help="图片路径")
    parser.add_argument("--question", default="图里有什么内容？", help="提问内容")
    # 获取默认Node.js脚本路径
    default_node_script = get_default_node_script("test_upload_image.js")
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