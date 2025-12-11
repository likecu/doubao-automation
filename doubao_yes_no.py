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
from doubao_ocr import DoubaoOCR
from doubao_text_chat import DoubaoTextChat

class DoubaoYesNo:
    def __init__(self, node_script_path):
        """
        初始化豆包是/否判断工具
        :param node_script_path: Node.js脚本路径
        """
        self.node_script_path = node_script_path
        self.ocr = None  # 延迟初始化
        self.text_chat = None  # 延迟初始化
        
    def read_file_content(self, file_path):
        """
        读取文件内容
        :param file_path: 文件路径
        :return: 文件内容字符串
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
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
        
        # 延迟初始化text_chat实例
        if self.text_chat is None:
            self.text_chat = DoubaoTextChat(self.node_script_path)
        # 调用纯文字聊天获取回答，debug模式下显示浏览器界面
        response = self.text_chat.get_response(full_question, headless=not debug)
        
        if not response:
            if debug:
                print("获取回答失败")
            return None
        
        # 解析回答为yes或no
        return self.parse_yes_no(response, debug)
    
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
        
        # 调用纯文字聊天获取回答，debug模式下显示浏览器界面
        response = self.text_chat.get_response(full_question, headless=not debug)
        
        if not response:
            if debug:
                print("获取回答失败")
            return None
        
        # 解析回答为是或否
        return self.parse_yes_no(response, debug)
    
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
        
        # 图片识别需要使用专门的test_upload_image.js脚本
        # 获取脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        test_upload_script = os.path.join(script_dir, "test_upload_image.js")
        # 创建专门用于图片识别的OCR实例
        from doubao_ocr import DoubaoOCR
        ocr = DoubaoOCR(test_upload_script)
        # 调用OCR获取回答，debug模式下显示浏览器界面
        result = ocr.recognize_image(image_path, full_question, headless=not debug)
        
        if not result or not result.get("success"):
            if debug:
                print("获取回答失败")
            return None
        
        response = result.get("response", "")
        
        # 解析回答为是或否
        return self.parse_yes_no(response, debug)
    
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
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_node_script = os.path.join(script_dir, "doubao_chat_bot.js")
    parser.add_argument("--node_script", default=default_node_script, help="Node.js脚本路径")
    parser.add_argument("--debug", action="store_true", help="输出调试信息")
    
    args = parser.parse_args()
    
    # 验证参数
    if args.file and args.image:
        print("错误: 文件和图片不能同时提供")
        sys.exit(1)
    
    try:
        # 创建是/否判断实例
        yes_no = DoubaoYesNo(args.node_script)
        
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