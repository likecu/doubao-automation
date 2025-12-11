#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包API调用工具集测试类
用于测试各个功能模块的正确性
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from doubao_ocr import DoubaoOCR
from screenshot_ocr import ScreenshotOCR
from doubao_text_chat import DoubaoTextChat
from doubao_yes_no import DoubaoYesNo

class TestDoubaoAPI(unittest.TestCase):
    """测试豆包API调用工具集"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image.png')
        # 创建一个临时测试图片文件
        if not os.path.exists(self.test_image_path):
            with open(self.test_image_path, 'w') as f:
                f.write('test image content')
        
        # 脚本路径，现在位于js目录下
        self.test_upload_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'js', 'test_upload_image.js')
        self.chat_bot_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'js', 'doubao_chat_bot.js')
        
    def tearDown(self):
        """清理测试环境"""
        # 不删除测试图片，以便后续测试使用
        pass
    
    def test_doubao_ocr_init(self):
        """测试DoubaoOCR类初始化"""
        # 测试正常初始化
        ocr = DoubaoOCR(self.test_upload_script)
        self.assertIsInstance(ocr, DoubaoOCR)
        
        # 测试无效脚本路径
        with self.assertRaises(FileNotFoundError):
            DoubaoOCR('invalid_script_path.js')
    
    def test_doubao_ocr_invalid_image(self):
        """测试DoubaoOCR识别不存在的图片"""
        ocr = DoubaoOCR(self.test_upload_script)
        with self.assertRaises(FileNotFoundError):
            ocr.recognize_image('invalid_image_path.png')
    
    @patch('subprocess.run')
    def test_doubao_ocr_recognize(self, mock_run):
        """测试DoubaoOCR识别图片"""
        # 模拟subprocess.run返回结果
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"success": true, "message": "图里有什么内容？", "response": "测试图片内容", "chatHistory": []}',
            stderr=''
        )
        
        ocr = DoubaoOCR(self.test_upload_script)
        result = ocr.recognize_image(self.test_image_path)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['response'], '测试图片内容')
    
    def test_doubao_text_chat_init(self):
        """测试DoubaoTextChat类初始化"""
        # 测试正常初始化
        chat = DoubaoTextChat(self.chat_bot_script)
        self.assertIsInstance(chat, DoubaoTextChat)
        
        # 测试无效脚本路径
        with self.assertRaises(FileNotFoundError):
            DoubaoTextChat('invalid_script_path.js')
    
    def test_doubao_text_chat_empty_message(self):
        """测试DoubaoTextChat发送空消息"""
        chat = DoubaoTextChat(self.chat_bot_script)
        with self.assertRaises(ValueError):
            chat.send_message('')
    
    @patch('subprocess.run')
    def test_doubao_text_chat_send(self, mock_run):
        """测试DoubaoTextChat发送消息"""
        # 模拟subprocess.run返回结果
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"success": true, "message": "你好", "response": "你好，有什么可以帮到你？", "chatHistory": []}',
            stderr=''
        )
        
        chat = DoubaoTextChat(self.chat_bot_script)
        result = chat.send_message('你好')
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['response'], '你好，有什么可以帮到你？')
    
    def test_doubao_yes_no_init(self):
        """测试DoubaoYesNo类初始化"""
        yes_no = DoubaoYesNo(self.chat_bot_script)
        self.assertIsInstance(yes_no, DoubaoYesNo)
    
    def test_doubao_yes_no_parse(self):
        """测试DoubaoYesNo解析是/否回答"""
        yes_no = DoubaoYesNo(self.chat_bot_script)
        
        # 测试肯定回答
        self.assertEqual(yes_no.parse_yes_no('是的，没错'), 'yes')
        self.assertEqual(yes_no.parse_yes_no('对的，正确'), 'yes')
        self.assertEqual(yes_no.parse_yes_no('Yes, absolutely'), 'yes')
        
        # 测试否定回答
        self.assertEqual(yes_no.parse_yes_no('不是的'), 'no')
        self.assertEqual(yes_no.parse_yes_no('不对，错误'), 'no')
        self.assertEqual(yes_no.parse_yes_no('No, definitely not'), 'no')
        
        # 测试无法判断的回答
        self.assertIsNone(yes_no.parse_yes_no('这个问题很难回答'))
        # "我不确定"包含"不确定"，应该返回'no'
        self.assertEqual(yes_no.parse_yes_no('我不确定'), 'no')
    
    def test_doubao_yes_no_file_read(self):
        """测试DoubaoYesNo读取文件内容"""
        yes_no = DoubaoYesNo(self.chat_bot_script)
        
        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write('测试文件内容')
            temp_file = f.name
        
        try:
            content = yes_no.read_file_content(temp_file)
            self.assertEqual(content, '测试文件内容')
            
            # 测试读取不存在的文件
            with self.assertRaises(FileNotFoundError):
                yes_no.read_file_content('invalid_file_path.txt')
        finally:
            # 清理临时文件
            os.unlink(temp_file)
    
    def test_screenshot_ocr_init(self):
        """测试ScreenshotOCR类初始化"""
        screenshot_ocr = ScreenshotOCR(self.test_upload_script)
        self.assertIsInstance(screenshot_ocr, ScreenshotOCR)
    
    @patch('PIL.ImageGrab.grab')
    def test_screenshot_ocr_capture(self, mock_grab):
        """测试ScreenshotOCR捕获屏幕"""
        # 模拟ImageGrab.grab返回结果
        mock_image = MagicMock()
        
        # 模拟save方法，实际创建一个空文件
        def mock_save(file_path):
            with open(file_path, 'w') as f:
                f.write('mock screenshot content')
        
        mock_image.save = mock_save
        mock_grab.return_value = mock_image
        
        screenshot_ocr = ScreenshotOCR(self.test_upload_script)
        temp_file = screenshot_ocr.capture_screen()
        
        # 验证结果
        self.assertIsInstance(temp_file, str)
        self.assertTrue(os.path.exists(temp_file))
        
        # 清理临时文件
        os.unlink(temp_file)

if __name__ == '__main__':
    # 运行所有测试
    unittest.main()
