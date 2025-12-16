#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包是/否判断工具
功能：
1. 支持纯文字问题的是/否判断
2. 支持文件内容的是/否判断
3. 支持图片内容的是/否判断
4. 解析豆包的回答，仅输出是或否
"""

import os
import sys
import argparse
from doubao_browser_client import DoubaoBrowserClient
from doubao_common import validate_file_path

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
        
        # 处理response为None的情况
        if response is None:
            return None
        
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
                
                # 获取原始响应
                response = result.get("response", "")
                
                # 处理response为null的情况，从chatHistory中提取回答
                chat_history = result.get("chatHistory", [])
                if response is None or response == "":
                    # 遍历chatHistory，找到包含实际回答的AI消息
                    for message in chat_history:
                        if message.get("type") == "ai" and message.get("content"):
                            content = message.get("content")
                            # 跳过无意义内容
                            if content in ["分享", "编辑分享"]:
                                continue
                            
                            # 检查是否是重复的问题
                            lower_content = content.lower()
                            lower_question = full_question.lower()
                            if lower_content.startswith(lower_question):
                                continue
                            
                            # 检查是否包含实际回答（yes/no）
                            if 'yes' in lower_content or 'no' in lower_content:
                                response = content
                                break
                    
                    # 如果没有找到包含yes/no的消息，尝试找到最长的AI回答
                    if response is None or response == "":
                        longest_ai_response = ""
                        for message in chat_history:
                            if message.get("type") == "ai" and message.get("content"):
                                content = message.get("content")
                                if content not in ["分享", "编辑分享"] and len(content) > len(longest_ai_response):
                                    longest_ai_response = content
                        
                        if longest_ai_response:
                            # 提取"分享"或"编辑分享"之前的内容
                            if "编辑分享" in longest_ai_response:
                                response = longest_ai_response.split("编辑分享")[0].strip()
                            elif "分享" in longest_ai_response:
                                response = longest_ai_response.split("分享")[0].strip()
                            else:
                                response = longest_ai_response
                
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
                
                # 获取原始响应
                response = result.get("response", "")
                
                # 处理response为null的情况，从chatHistory中提取回答
                chat_history = result.get("chatHistory", [])
                if response is None or response == "":
                    # 遍历chatHistory，找到包含实际回答的AI消息
                    for message in chat_history:
                        if message.get("type") == "ai" and message.get("content"):
                            content = message.get("content")
                            # 跳过无意义内容
                            if content in ["分享", "编辑分享"]:
                                continue
                            
                            # 检查是否是重复的问题
                            lower_content = content.lower()
                            lower_question = full_question.lower()
                            if lower_content.startswith(lower_question):
                                continue
                            
                            # 检查是否包含实际回答（yes/no）
                            if 'yes' in lower_content or 'no' in lower_content:
                                response = content
                                break
                    
                    # 如果没有找到包含yes/no的消息，尝试找到最长的AI回答
                    if response is None or response == "":
                        longest_ai_response = ""
                        for message in chat_history:
                            if message.get("type") == "ai" and message.get("content"):
                                content = message.get("content")
                                if content not in ["分享", "编辑分享"] and len(content) > len(longest_ai_response):
                                    longest_ai_response = content
                        
                        if longest_ai_response:
                            # 提取"分享"或"编辑分享"之前的内容
                            if "编辑分享" in longest_ai_response:
                                response = longest_ai_response.split("编辑分享")[0].strip()
                            elif "分享" in longest_ai_response:
                                response = longest_ai_response.split("分享")[0].strip()
                            else:
                                response = longest_ai_response
                
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
                
                # 获取原始响应
                response = result.get("response", "")
                
                # 处理response为null的情况，从chatHistory中提取回答
                chat_history = result.get("chatHistory", [])
                if response is None or response == "":
                    # 遍历chatHistory，找到包含实际回答的AI消息
                    for message in chat_history:
                        if message.get("type") == "ai" and message.get("content"):
                            content = message.get("content")
                            # 跳过无意义内容
                            if content in ["分享", "编辑分享"]:
                                continue
                            
                            # 检查是否是重复的问题
                            lower_content = content.lower()
                            lower_question = full_question.lower()
                            if lower_content.startswith(lower_question):
                                continue
                            
                            # 检查是否包含实际回答（yes/no）
                            if 'yes' in lower_content or 'no' in lower_content:
                                response = content
                                break
                    
                    # 如果没有找到包含yes/no的消息，尝试找到最长的AI回答
                    if response is None or response == "":
                        longest_ai_response = ""
                        for message in chat_history:
                            if message.get("type") == "ai" and message.get("content"):
                                content = message.get("content")
                                if content not in ["分享", "编辑分享"] and len(content) > len(longest_ai_response):
                                    longest_ai_response = content
                        
                        if longest_ai_response:
                            # 提取"分享"或"编辑分享"之前的内容
                            if "编辑分享" in longest_ai_response:
                                response = longest_ai_response.split("编辑分享")[0].strip()
                            elif "分享" in longest_ai_response:
                                response = longest_ai_response.split("分享")[0].strip()
                            else:
                                response = longest_ai_response
                
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

def main():
    """
    主函数，用于命令行调用
    """
    parser = argparse.ArgumentParser(description="豆包是/否判断工具")
    parser.add_argument("--question", required=True, help="判断的问题")
    parser.add_argument("--file", help="文件路径")
    parser.add_argument("--image", help="图片路径")
    parser.add_argument("--server", default="http://localhost:3000", help="浏览器服务器地址")
    parser.add_argument("--debug", action="store_true", help="输出调试信息")
    
    args = parser.parse_args()
    
    # 验证参数
    if args.file and args.image:
        print("错误: 文件和图片不能同时提供")
        sys.exit(1)
    
    try:
        # 创建是/否判断实例
        yes_no = DoubaoYesNo(args.server)
        
        # 执行判断
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