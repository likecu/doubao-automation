#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包屏幕截图OCR识别工具
功能：
1. 截取当前屏幕
2. 调用豆包API询问屏幕内容
3. 将结果输出到指定文件
"""

import os
import sys
import argparse
import tempfile
from datetime import datetime
from PIL import ImageGrab
from doubao_ocr import DoubaoOCR

class ScreenshotOCR:
    def __init__(self, node_script_path):
        """
        初始化截图OCR工具
        :param node_script_path: Node.js脚本路径
        """
        self.ocr = DoubaoOCR(node_script_path)
    
    def capture_screen(self, output_path=None):
        """
        截取当前屏幕
        :param output_path: 截图保存路径，默认使用临时文件
        :return: 截图文件路径
        """
        print("正在截取屏幕...")
        
        # 截取屏幕
        screenshot = ImageGrab.grab()
        
        # 保存截图
        if not output_path:
            # 使用临时文件
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(temp_dir, f"screenshot_{timestamp}.png")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存图片
        screenshot.save(output_path)
        print(f"屏幕截图已保存到: {output_path}")
        
        return output_path
    
    def recognize_screen(self, output_file=None, question="图里有什么内容？"):
        """
        截取屏幕并识别内容
        :param output_file: 结果输出文件路径
        :param question: 向豆包提问的问题
        :return: 识别结果
        """
        # 1. 截取屏幕
        screenshot_path = self.capture_screen()
        
        try:
            # 2. 调用豆包OCR识别
            result = self.ocr.recognize_image(screenshot_path, question)
            
            if result and result.get("success"):
                response = result.get("response", "")
                print("\n=== 屏幕识别结果 ===")
                print(response)
                
                # 3. 将结果输出到文件
                if output_file:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(f"识别时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"问题: {question}\n\n")
                        f.write(f"识别结果:\n{response}\n")
                    print(f"\n识别结果已保存到: {output_file}")
                
                return result
            else:
                print("识别失败")
                return None
        finally:
            # 清理临时文件
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                print(f"临时截图已删除: {screenshot_path}")

def main():
    """
    主函数，用于命令行调用
    """
    parser = argparse.ArgumentParser(description="豆包屏幕截图OCR识别工具")
    parser.add_argument("--output", help="结果输出文件路径")
    parser.add_argument("--question", default="图里有什么内容？", help="向豆包提问的问题")
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_node_script = os.path.join(script_dir, "test_upload_image.js")
    parser.add_argument("--node_script", default=default_node_script, help="Node.js脚本路径")
    
    args = parser.parse_args()
    
    # 创建截图OCR实例
    screenshot_ocr = ScreenshotOCR(args.node_script)
    
    # 执行屏幕识别
    result = screenshot_ocr.recognize_screen(args.output, args.question)
    
    if result:
        print("\n识别成功！")
    else:
        print("\n识别失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()