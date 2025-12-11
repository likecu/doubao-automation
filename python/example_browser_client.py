#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包浏览器客户端使用示例
演示如何使用浏览器复用功能同时运行多个Python文件
"""

from doubao_ocr import DoubaoOCR
from doubao_text_chat import DoubaoTextChat
from doubao_yes_no import DoubaoYesNo


def example_ocr():
    """
    示例1: 使用浏览器客户端进行OCR识别
    """
    print("\n=== 示例1: OCR识别 ===")
    
    try:
        # 创建OCR实例，使用默认的浏览器服务器地址
        ocr = DoubaoOCR()
        
        # 识别图片内容
        # 注意：请将下面的图片路径替换为实际存在的图片路径
        # result = ocr.recognize_image(
        #     "/path/to/image.png", 
        #     question="图里有什么内容？"
        # )
        # 
        # if result and result.get("success"):
        #     print(f"识别结果: {result.get('response')}")
        # else:
        #     print("识别失败")
        
        print("OCR示例已准备好，需要替换为实际图片路径才能运行")
        
    except Exception as e:
        print(f"OCR示例出错: {e}")


def example_text_chat():
    """
    示例2: 使用浏览器客户端进行纯文本聊天
    """
    print("\n=== 示例2: 纯文本聊天 ===")
    
    try:
        # 创建纯文本聊天实例
        chat = DoubaoTextChat()
        
        # 发送消息
        result = chat.send_message("你好，豆包")
        
        if result and result.get("success"):
            print(f"豆包回复: {result.get('response')}")
        else:
            print("聊天失败")
            
    except Exception as e:
        print(f"纯文本聊天示例出错: {e}")


def example_yes_no():
    """
    示例3: 使用浏览器客户端进行是/否判断
    """
    print("\n=== 示例3: 是/否判断 ===")
    
    try:
        # 创建是/否判断实例
        yes_no = DoubaoYesNo()
        
        # 执行是/否判断
        result = yes_no.judge(question="地球是圆的吗？")
        
        print(f"判断结果: {result}")
        
    except Exception as e:
        print(f"是/否判断示例出错: {e}")


def example_multiple_instances():
    """
    示例4: 同时运行多个浏览器客户端实例
    演示如何在不同的Python文件中同时使用浏览器复用功能
    """
    print("\n=== 示例4: 同时运行多个客户端实例 ===")
    
    try:
        # 创建多个不同类型的客户端实例
        # 这些实例将共享同一个浏览器服务器
        ocr = DoubaoOCR()
        chat = DoubaoTextChat()
        yes_no = DoubaoYesNo()
        
        print("已成功创建多个客户端实例")
        print("它们将共享同一个浏览器服务器，每个实例会创建独立的页面")
        print("\n可以在不同的Python文件中创建这些实例，它们都将复用同一个浏览器")
        
    except Exception as e:
        print(f"多个实例示例出错: {e}")


def main():
    """
    主函数，运行所有示例
    """
    print("豆包浏览器客户端使用示例")
    print("=" * 50)
    print("使用说明：")
    print("1. 首先启动浏览器服务器：")
    print("   ./start_browser_server.sh 或 node js/browser_server.js")
    print("2. 然后运行此示例文件：")
    print("   python3 example_browser_client.py")
    print("3. 浏览器服务器将保持运行，所有Python文件共享同一个浏览器")
    print("=" * 50)
    
    # 运行各个示例
    example_ocr()
    example_text_chat()
    example_yes_no()
    example_multiple_instances()
    
    print("\n" + "=" * 50)
    print("示例运行完成")
    print("浏览器服务器仍在后台运行，可通过 Ctrl+C 停止")
    print("或使用 kill 命令停止进程")


if __name__ == "__main__":
    main()
