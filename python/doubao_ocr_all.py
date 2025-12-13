#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包OCR整合工具
包含所有OCR相关功能：
1. 图片OCR识别
2. 屏幕截图OCR识别  
3. 是/否判断（支持纯文本、文件、图片）
"""

import os
import sys
import argparse
import tempfile
import json
import time
from datetime import datetime
from PIL import ImageGrab
import requests
from typing import Dict, Optional, List

# ========== 公共工具函数 ==========

def validate_file_path(file_path):
    """
    验证文件路径是否存在
    :param file_path: 文件路径
    :return: 绝对路径或抛出FileNotFoundError
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    return os.path.abspath(file_path)


def get_script_dir():
    """
    获取当前脚本所在目录
    :return: 脚本所在目录的绝对路径
    """
    return os.path.dirname(os.path.abspath(__file__))


# ========== 豆包浏览器客户端 ==========

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


# ========== 豆包OCR识别类 ==========

class DoubaoOCR:
    def __init__(self, server_url="http://localhost:3000"):
        """
        初始化豆包OCR识别类
        :param server_url: 浏览器服务器地址，默认为 http://localhost:3000
        """
        self.client = DoubaoBrowserClient(server_url)
    
    def recognize_image(self, image_path, question="图里有什么内容？"):
        """
        通过浏览器服务器识别图片内容
        :param image_path: 图片路径
        :param question: 向豆包提问的问题
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
    
    def get_ocr_result(self, image_path, question="图里有什么内容？"):
        """
        获取OCR识别结果
        :param image_path: 图片路径
        :param question: 向豆包提问的问题
        :return: 识别结果字符串
        """
        result = self.recognize_image(image_path, question)
        if result and result.get("success"):
            return result.get("response", "")
        return "识别失败"


# ========== 屏幕截图OCR类 ==========

class ScreenshotOCR:
    def __init__(self, server_url="http://localhost:3000"):
        """
        初始化截图OCR工具
        :param server_url: 浏览器服务器地址
        """
        self.ocr = DoubaoOCR(server_url)
    
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


# ========== 豆包是/否判断类 ==========

class DoubaoYesNo:
    def __init__(self, server_url="http://localhost:3000"):
        """
        初始化豆包是/否判断工具
        :param server_url: 浏览器服务器地址，默认为 http://localhost:3000
        """
        self.client = DoubaoBrowserClient(server_url)
        
    def read_file_content(self, file_path):
        """
        读取文件内容
        :param file_path: 文件路径
        :return: 文件内容字符串
        """
        file_path = validate_file_path(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    
    def parse_yes_no(self, response, debug=False):
        """
        解析回答为yes或no
        :param response: 豆包的回答
        :param debug: 是否输出调试信息
        :return: yes/no，无法判断返回None
        """
        if debug:
            print(f"原始回答: {response}")
        
        # 转换为小写进行匹配
        lower_response = response.lower()
        
        # 否定词列表，包含更长的词优先匹配
        no_words = ['不是', '不对', '不确定', '错误的', '不对的', '没有',
                    '否', '不', '错误', '否定', 'neither',
                    'no', 'nope', 'not', 'incorrect', 'wrong', 'negative']
        
        # 肯定词列表，包含更长的词优先匹配
        yes_words = ['是的', '没错', '没错的', '对的', '肯定', '确定',
                     '是', '对', '正确',
                     'yes', 'yeah', 'yep', 'correct', 'right', 'affirmative', 'sure', 'okay']
        
        # 检查回答是否包含否定词
        for word in no_words:
            if word in lower_response:
                return "no"
        
        # 检查回答是否包含肯定词
        for word in yes_words:
            if word in lower_response:
                return "yes"
        
        # 无法判断时返回None
        return None
    
    def judge_text(self, question, debug=False):
        """
        判断纯文字问题
        :param question: 问题
        :param debug: 是否输出调试信息
        :return: yes/no
        """
        # 构建完整问题，引导豆包仅回答yes或no
        full_question = f"{question} Please answer with only 'yes' or 'no'."
        
        if debug:
            print(f"向豆包提问: {full_question}")
        
        try:
            # 创建新页面
            page_id = self.client.create_page()
            if not page_id:
                if debug:
                    print("创建页面失败")
                return None
            
            try:
                # 执行纯文本聊天
                result = self.client.text_chat(page_id, full_question)
                
                if not result or not result.get("success"):
                    if debug:
                        print("获取回答失败")
                    return None
                
                response = result.get("response", "")
                
                # 解析回答为yes或no
                return self.parse_yes_no(response, debug)
            finally:
                # 关闭页面
                self.client.close_page(page_id)
                
        except Exception as e:
            if debug:
                print(f"判断失败: {str(e)}")
            return None
    
    def judge_file(self, question, file_path, debug=False):
        """
        判断文件内容相关问题
        :param question: 问题
        :param file_path: 文件路径
        :param debug: 是否输出调试信息
        :return: yes/no
        """
        # 读取文件内容
        file_content = self.read_file_content(file_path)
        
        if debug:
            print(f"文件内容: {file_content[:100]}...")
        
        # 构建完整问题，引导豆包仅回答yes或no
        full_question = f"{question} 文件内容如下：\n{file_content}\nPlease answer with only 'yes' or 'no'."
        
        if debug:
            print(f"向豆包提问: {full_question}")
        
        try:
            # 创建新页面
            page_id = self.client.create_page()
            if not page_id:
                if debug:
                    print("创建页面失败")
                return None
            
            try:
                # 执行纯文本聊天
                result = self.client.text_chat(page_id, full_question)
                
                if not result or not result.get("success"):
                    if debug:
                        print("获取回答失败")
                    return None
                
                response = result.get("response", "")
                
                # 解析回答为yes或no
                return self.parse_yes_no(response, debug)
            finally:
                # 关闭页面
                self.client.close_page(page_id)
                
        except Exception as e:
            if debug:
                print(f"判断失败: {str(e)}")
            return None
    
    def judge_image(self, question, image_path, debug=False):
        """
        判断图片内容相关问题
        :param question: 问题
        :param image_path: 图片路径
        :param debug: 是否输出调试信息
        :return: yes/no
        """
        # 构建完整问题，引导豆包仅回答yes或no
        full_question = f"{question} Please answer with only 'yes' or 'no'."
        
        if debug:
            print(f"向豆包提问: {full_question}")
        
        try:
            # 验证并获取绝对路径
            image_path = validate_file_path(image_path)
            
            # 创建新页面
            page_id = self.client.create_page()
            if not page_id:
                if debug:
                    print("创建页面失败")
                return None
            
            try:
                # 执行OCR识别
                result = self.client.ocr(page_id, image_path, full_question)
                
                if not result or not result.get("success"):
                    if debug:
                        print("获取回答失败")
                    return None
                
                response = result.get("response", "")
                
                # 解析回答为yes或no
                return self.parse_yes_no(response, debug)
            finally:
                # 关闭页面
                self.client.close_page(page_id)
                
        except Exception as e:
            if debug:
                print(f"判断失败: {str(e)}")
            return None
    
    def judge(self, question=None, file_path=None, image_path=None, debug=False):
        """
        统一的判断方法
        :param question: 问题
        :param file_path: 文件路径
        :param image_path: 图片路径
        :param debug: 是否输出调试信息
        :return: yes/no
        """
        # 参数验证
        if not question:
            raise ValueError("问题不能为空")
        
        if file_path and image_path:
            raise ValueError("文件和图片不能同时提供")
        
        # 检查服务器状态
        if not self.client.is_server_running():
            print("浏览器服务器未运行，请先启动服务器")
            print("启动命令: node browser_server.js")
            return None
        
        if file_path:
            # 文件判断
            return self.judge_file(question, file_path, debug)
        elif image_path:
            # 图片判断
            return self.judge_image(question, image_path, debug)
        else:
            # 纯文字判断
            return self.judge_text(question, debug)


# ========== 命令行入口 ==========

def main():
    """
    主函数，统一的命令行入口
    """
    parser = argparse.ArgumentParser(description="豆包OCR整合工具")
    
    # 子命令配置
    subparsers = parser.add_subparsers(dest="command", required=True, help="可用命令")
    
    # 1. 图片OCR命令
    ocr_parser = subparsers.add_parser("ocr", help="图片OCR识别")
    ocr_parser.add_argument("image_path", help="图片路径")
    ocr_parser.add_argument("--question", default="图里有什么内容？", help="向豆包提问的问题")
    ocr_parser.add_argument("--server", default="http://localhost:3000", help="浏览器服务器地址")
    
    # 2. 屏幕截图OCR命令
    screenshot_parser = subparsers.add_parser("screenshot", help="屏幕截图OCR识别")
    screenshot_parser.add_argument("--output", help="结果输出文件路径")
    screenshot_parser.add_argument("--question", default="图里有什么内容？", help="向豆包提问的问题")
    screenshot_parser.add_argument("--server", default="http://localhost:3000", help="浏览器服务器地址")
    
    # 3. 是/否判断命令
    yes_no_parser = subparsers.add_parser("yesno", help="是/否判断")
    yes_no_parser.add_argument("--question", required=True, help="判断的问题")
    yes_no_parser.add_argument("--file", help="文件路径")
    yes_no_parser.add_argument("--image", help="图片路径")
    yes_no_parser.add_argument("--server", default="http://localhost:3000", help="浏览器服务器地址")
    yes_no_parser.add_argument("--debug", action="store_true", help="输出调试信息")
    
    args = parser.parse_args()
    
    # 根据命令执行不同功能
    if args.command == "ocr":
        # 图片OCR识别
        ocr = DoubaoOCR(args.server)
        result = ocr.recognize_image(args.image_path, args.question)
        
        if result:
            print("\n=== 识别结果 ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 提取关键信息
            if result.get("success"):
                print("\n=== 关键信息 ===")
                print(f"提问: {result.get('message', '')}")
                print(f"回复: {result.get('response', '')}")
    
    elif args.command == "screenshot":
        # 屏幕截图OCR识别
        screenshot_ocr = ScreenshotOCR(args.server)
        screenshot_ocr.recognize_screen(args.output, args.question)
    
    elif args.command == "yesno":
        # 是/否判断
        yes_no = DoubaoYesNo(args.server)
        
        # 验证参数
        if args.file and args.image:
            print("错误: 文件和图片不能同时提供")
            sys.exit(1)
        
        try:
            result = yes_no.judge(
                question=args.question,
                file_path=args.file,
                image_path=args.image,
                debug=args.debug
            )
            
            # 输出结果
            if result:
                print(result)
            else:
                print("无法判断")
        except Exception as e:
            print(f"错误: {str(e)}")
            if args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()