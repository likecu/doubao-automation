#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 图片OCR识别Python调用脚本
用于调用Google Gemini API进行图片OCR识别，返回识别结果
"""

import os
import argparse
import json
import datetime
import random
import google.genai as genai
from gemini_config import GEMINI_API_KEYS

class GeminiOCR:
    def __init__(self):
        """
        初始化Gemini OCR识别类
        """
        # 随机选择一个API密钥
        self.current_key_index = random.randint(0, len(GEMINI_API_KEYS) - 1)
        self.api_key = GEMINI_API_KEYS[self.current_key_index]
        
        # 创建客户端实例
        self.client = genai.Client(api_key=self.api_key)
        
        # 本地使用量存储文件路径
        self.usage_file = os.path.join(os.path.dirname(__file__), "gemini_usage.json")
        
        # 模型速率限制数据
        self.rate_limits = {
            # Gemini 2.5 模型
            "gemini-2.5-flash": {"rpm_limit": 5, "tpm_limit": 250000, "rpd_limit": 20},
            "gemini-2.5-flash-lite": {"rpm_limit": 10, "tpm_limit": 100000, "rpd_limit": 40},
            "gemini-2.5-flash-native-audio-dialog": {"rpm_limit": float('inf'), "tpm_limit": float('inf'), "rpd_limit": float('inf')},
            "gemini-2.5-pro": {"rpm_limit": 3, "tpm_limit": 100000, "rpd_limit": 10},
            
            # Gemma 3 模型
            "gemma-3-12b-it": {"rpm_limit": 10, "tpm_limit": 50000, "rpd_limit": 20},
            "gemma-3-2b-it": {"rpm_limit": 20, "tpm_limit": 100000, "rpd_limit": 40},
            "gemma-3-9b-it": {"rpm_limit": 15, "tpm_limit": 75000, "rpd_limit": 30},
            
            # Gemma 2 模型
            "gemma-2-27b-it": {"rpm_limit": 10, "tpm_limit": 50000, "rpd_limit": 20},
            "gemma-2-9b-it": {"rpm_limit": 20, "tpm_limit": 100000, "rpd_limit": 40},
            "gemma-2-2b-it": {"rpm_limit": 50, "tpm_limit": 200000, "rpd_limit": 100},
            
            # Gemma 1.1 模型
            "gemma-1.1-7b-it": {"rpm_limit": 20, "tpm_limit": 100000, "rpd_limit": 40},
            "gemma-1.1-2b-it": {"rpm_limit": 50, "tpm_limit": 200000, "rpd_limit": 100},
            
            # Gemma 1 模型
            "gemma-1-7b-it": {"rpm_limit": 20, "tpm_limit": 100000, "rpd_limit": 40},
            "gemma-1-2b-it": {"rpm_limit": 50, "tpm_limit": 200000, "rpd_limit": 100},
            
            # Gemini 1.5 模型
            "gemini-1.5-pro": {"rpm_limit": 5, "tpm_limit": 10000, "rpd_limit": 10},
            "gemini-1.5-flash": {"rpm_limit": 5, "tpm_limit": 250000, "rpd_limit": 20},
            
            # 其他模型
            "gemini-ultra": {"rpm_limit": 5, "tpm_limit": 10000, "rpd_limit": 10},
            "gemini-nano": {"rpm_limit": 50, "tpm_limit": 200000, "rpd_limit": 100},
            "gemini-experimental": {"rpm_limit": 2, "tpm_limit": 5000, "rpd_limit": 5}
        }
        
        # 模型优先级列表（优先使用高限额且高性能模型）
        self.model_priority = [
            "gemini-2.5-flash-lite",  # 高限额标准模型
            "gemini-2.5-flash",  # 主要使用模型
            "gemini-1.5-flash",
            "gemma-3-2b-it",  # 中限额模型
            "gemma-3-9b-it",
            "gemma-2-9b-it",
            "gemma-1.1-7b-it",
            "gemma-1-7b-it",
            "gemma-2-2b-it",  # 高限额轻量级模型
            "gemma-1.1-2b-it",
            "gemma-1-2b-it",
            "gemini-nano",
            "gemma-3-12b-it",  # 低限额模型
            "gemma-2-27b-it",
            "gemini-2.5-pro",  # 专业模型
            "gemini-1.5-pro",
            "gemini-ultra",
            "gemini-experimental"
        ]
        
        # 选择合适的模型
        self.model_name = self.select_best_model()
        print(f"使用模型: {self.model_name}")
    
    def ask_question(self, question):
        """
        直接向Gemini提问
        :param question: 提问内容
        :return: 提问结果对象
        """
        print(f"开始提问: {question}")
        print(f"当前使用模型: {self.model_name}")
        
        # 尝试提问，支持模型切换
        max_attempts = 3
        current_attempt = 0
        
        while current_attempt < max_attempts:
            try:
                # 直接使用文本内容
                contents = [question]
                
                # 调用Gemini API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents
                )
                
                # 估算使用的令牌数（简单估算）
                tokens_used = len(response.text) * 1.5  # 粗略估算：每个汉字约1.5个令牌
                
                # 更新本地使用量记录
                self.update_usage(self.model_name, int(tokens_used))
                
                print(f"使用量更新: {self.model_name} - RPM: +1, TPM: +{int(tokens_used)}")
                
                # 返回结果对象
                return {
                    "success": True,
                    "response": response.text,
                    "model": self.model_name,
                    "tokens_used": int(tokens_used),
                    "chatHistory": [
                        {"type": "user", "content": question},
                        {"type": "ai", "content": response.text}
                    ]
                }
                
            except Exception as e:
                error_msg = str(e)
                print(f"调用Gemini API时发生错误: {error_msg}")
                
                # 检查是否是配额超限错误
                if "quota exceeded" in error_msg.lower() or "429" in error_msg:
                    print(f"模型 {self.model_name} 配额已用完，尝试切换模型或API密钥...")
                    current_attempt += 1
                    
                    # 尝试切换API密钥
                    if len(GEMINI_API_KEYS) > 1:
                        self.current_key_index = (self.current_key_index + 1) % len(GEMINI_API_KEYS)
                        self.api_key = GEMINI_API_KEYS[self.current_key_index]
                        self.client = genai.Client(api_key=self.api_key)
                        print(f"已切换到新API密钥: {self.api_key[:10]}...")
                    
                    # 从优先级列表中移除当前模型
                    if self.model_name in self.model_priority:
                        self.model_priority.remove(self.model_name)
                    
                    # 选择新的模型
                    new_model = self.select_best_model()
                    if new_model != self.model_name:
                        self.model_name = new_model
                        print(f"已切换到新模型: {self.model_name}")
                    else:
                        print("没有可用的替代模型")
                        break
                else:
                    # 其他错误，直接返回
                    return None
        
        print(f"尝试了 {current_attempt} 次后仍无法完成提问")
        return None
    
    def recognize_image(self, image_path, question="图里有什么内容？"):
        """
        通过Gemini API识别图片内容
        :param image_path: 图片路径
        :param question: 向Gemini提问的问题
        :return: 识别结果字符串
        """
        # 验证并获取绝对路径
        image_path = os.path.abspath(image_path)
        
        if not os.path.exists(image_path):
            print(f"图片文件不存在: {image_path}")
            return None
        
        print(f"开始识别图片: {image_path}")
        print(f"提问内容: {question}")
        print(f"当前使用模型: {self.model_name}")
        
        # 尝试识别图片，支持模型切换
        max_attempts = 3
        current_attempt = 0
        
        while current_attempt < max_attempts:
            try:
                # 使用内嵌方式传递图片数据
                from google.genai import types
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
                
                # 构建消息内容
                contents = [
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/jpeg' if image_path.endswith('.jpg') or image_path.endswith('.jpeg') else 'image/png'
                    ),
                    question
                ]
                
                # 调用Gemini API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents
                )
                
                # 估算使用的令牌数（简单估算）
                tokens_used = len(response.text) * 1.5  # 粗略估算：每个汉字约1.5个令牌
                
                # 更新本地使用量记录
                self.update_usage(self.model_name, int(tokens_used))
                
                print(f"使用量更新: {self.model_name} - RPM: +1, TPM: +{int(tokens_used)}")
                
                # 返回结果对象
                return {
                    "success": True,
                    "response": response.text,
                    "model": self.model_name,
                    "tokens_used": int(tokens_used),
                    "chatHistory": [
                        {"type": "user", "content": question},
                        {"type": "ai", "content": response.text}
                    ]
                }
                
            except Exception as e:
                error_msg = str(e)
                print(f"调用Gemini API时发生错误: {error_msg}")
                
                # 检查是否是配额超限错误
                if "quota exceeded" in error_msg.lower() or "429" in error_msg:
                    print(f"模型 {self.model_name} 配额已用完，尝试切换模型或API密钥...")
                    current_attempt += 1
                    
                    # 尝试切换API密钥
                    if len(GEMINI_API_KEYS) > 1:
                        self.current_key_index = (self.current_key_index + 1) % len(GEMINI_API_KEYS)
                        self.api_key = GEMINI_API_KEYS[self.current_key_index]
                        self.client = genai.Client(api_key=self.api_key)
                        print(f"已切换到新API密钥: {self.api_key[:10]}...")
                    
                    # 从优先级列表中移除当前模型
                    if self.model_name in self.model_priority:
                        self.model_priority.remove(self.model_name)
                    
                    # 选择新的模型
                    new_model = self.select_best_model()
                    if new_model != self.model_name:
                        self.model_name = new_model
                        print(f"已切换到新模型: {self.model_name}")
                    else:
                        print("没有可用的替代模型")
                        break
                else:
                    # 其他错误，直接返回
                    return None
        
        print(f"尝试了 {current_attempt} 次后仍无法完成识别")
        return None
    
    def process_document(self, document_path, question="文档内容是什么？"):
        """
        通过Gemini API处理文档内容（PDF等）
        :param document_path: 文档路径
        :param question: 向Gemini提问的问题
        :return: 处理结果字符串
        """
        # 验证并获取绝对路径
        document_path = os.path.abspath(document_path)
        
        if not os.path.exists(document_path):
            print(f"文档文件不存在: {document_path}")
            return None
        
        print(f"开始处理文档: {document_path}")
        print(f"提问内容: {question}")
        print(f"当前使用模型: {self.model_name}")
        
        # 尝试处理文档，支持模型切换
        max_attempts = 3
        current_attempt = 0
        
        while current_attempt < max_attempts:
            try:
                # 使用内嵌方式传递文档数据
                from google.genai import types
                with open(document_path, 'rb') as f:
                    doc_bytes = f.read()
                
                # 构建消息内容
                contents = [
                    types.Part.from_bytes(
                        data=doc_bytes,
                        mime_type='application/pdf'
                    ),
                    question
                ]
                
                # 调用Gemini API
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents
                )
                
                # 估算使用的令牌数（简单估算）
                tokens_used = len(response.text) * 1.5  # 粗略估算：每个汉字约1.5个令牌
                
                # 更新本地使用量记录
                self.update_usage(self.model_name, int(tokens_used))
                
                print(f"使用量更新: {self.model_name} - RPM: +1, TPM: +{int(tokens_used)}")
                
                # 返回结果对象
                return {
                    "success": True,
                    "response": response.text,
                    "model": self.model_name,
                    "tokens_used": int(tokens_used),
                    "chatHistory": [
                        {"type": "user", "content": question},
                        {"type": "ai", "content": response.text}
                    ]
                }
                
            except Exception as e:
                error_msg = str(e)
                print(f"调用Gemini API时发生错误: {error_msg}")
                
                # 检查是否是配额超限错误
                if "quota exceeded" in error_msg.lower() or "429" in error_msg:
                    print(f"模型 {self.model_name} 配额已用完，尝试切换模型或API密钥...")
                    current_attempt += 1
                    
                    # 尝试切换API密钥
                    if len(GEMINI_API_KEYS) > 1:
                        self.current_key_index = (self.current_key_index + 1) % len(GEMINI_API_KEYS)
                        self.api_key = GEMINI_API_KEYS[self.current_key_index]
                        self.client = genai.Client(api_key=self.api_key)
                        print(f"已切换到新API密钥: {self.api_key[:10]}...")
                    
                    # 从优先级列表中移除当前模型
                    if self.model_name in self.model_priority:
                        self.model_priority.remove(self.model_name)
                    
                    # 选择新的模型
                    new_model = self.select_best_model()
                    if new_model != self.model_name:
                        self.model_name = new_model
                        print(f"已切换到新模型: {self.model_name}")
                    else:
                        print("没有可用的替代模型")
                        break
                else:
                    # 其他错误，直接返回
                    return None
        
        print(f"尝试了 {current_attempt} 次后仍无法完成文档处理")
        return None
    
    def get_ocr_result(self, result, question="图里有什么内容？"):
        """
        从识别结果中提取OCR识别文本
        :param result: 识别结果对象
        :param question: 向Gemini提问的问题
        :return: 识别结果字符串
        """
        if result and result.get("success"):
            return result.get("response", "识别失败")
        return "识别失败"
    
    def load_usage_data(self):
        """
        加载本地使用量数据
        :return: 使用量数据字典
        """
        if not os.path.exists(self.usage_file):
            return {}
        
        try:
            with open(self.usage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"警告: {self.usage_file} 文件格式错误，将重新创建")
            return {}
    
    def save_usage_data(self, usage_data):
        """
        保存本地使用量数据
        :param usage_data: 使用量数据字典
        """
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(usage_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"警告: 无法保存使用量数据到 {self.usage_file}: {e}")
    
    def update_usage(self, model_name, tokens_used=100):
        """
        更新本地使用量记录
        :param model_name: 模型名称
        :param tokens_used: 使用的令牌数
        """
        today = datetime.date.today().isoformat()
        usage_data = self.load_usage_data()
        
        # 初始化今天的数据
        if today not in usage_data:
            usage_data[today] = {}
        
        # 初始化模型数据
        if model_name not in usage_data[today]:
            usage_data[today][model_name] = {
                "rpm_used": 0,
                "tpm_used": 0,
                "rpd_used": 0
            }
        
        # 更新使用量
        usage_data[today][model_name]["rpm_used"] += 1  # 每次调用增加一个请求
        usage_data[today][model_name]["tpm_used"] += tokens_used
        usage_data[today][model_name]["rpd_used"] += 1  # 每次调用增加一个请求
        
        # 保存数据
        self.save_usage_data(usage_data)
    
    def get_today_usage(self, model_name):
        """
        获取今天的使用量
        :param model_name: 模型名称
        :return: 使用量字典 {"rpm_used": 0, "tpm_used": 0, "rpd_used": 0}
        """
        today = datetime.date.today().isoformat()
        usage_data = self.load_usage_data()
        
        if today in usage_data and model_name in usage_data[today]:
            return usage_data[today][model_name]
        return {"rpm_used": 0, "tpm_used": 0, "rpd_used": 0}
    
    def is_model_available(self, model_name):
        """
        检查模型是否可用（本地使用量未达限额）
        :param model_name: 模型名称
        :return: 是否可用
        """
        if model_name not in self.rate_limits:
            return False
        
        usage = self.get_today_usage(model_name)
        limits = self.rate_limits[model_name]
        
        # 检查RPM（每分钟请求数）
        if usage["rpm_used"] >= limits["rpm_limit"]:
            return False
        
        # 检查TPM（每分钟令牌数）
        if usage["tpm_used"] >= limits["tpm_limit"]:
            return False
        
        # 检查RPD（每天请求数）
        if usage["rpd_used"] >= limits["rpd_limit"]:
            return False
        
        return True
    
    def select_best_model(self):
        """
        选择最优模型（优先使用无限制且未达本地限额的模型）
        :return: 最优模型名称
        """
        for model_name in self.model_priority:
            if self.is_model_available(model_name):
                return model_name
        
        # 如果所有模型都不可用，返回默认模型
        return "gemini-2.5-flash"
    
    def check_quota(self, show_details=False):
        """
        检查Gemini API限额
        通过发送一个小的请求并分析响应或错误信息来获取限额信息
        :param show_details: 是否显示详细的速率限制信息
        """
        print("正在检查Gemini API限额...")
        
        try:
            # 发送一个简单的文本请求来检查限额
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=["检查限额"]
            )
            print("✓ API请求成功，当前有可用限额")
            
            # 显示详细的速率限制信息
            if show_details:
                print("\n=== Gemini 模型速率限制详情 ===")
                print("\n模型名称\t\t\t\t\t类别\t\tRPM\t\tTPM\t\tRPD")
                print("-" * 120)
                
                # 模型速率限制数据
                rate_limits = [
                    ("gemini-2.5-flash", "文本输出模型", "2 / 5", "268 / 250K", "6 / 20"),
                    ("gemini-2.5-flash-lite", "轻量级模型", "3 / 10", "60 / 100K", "10 / 40"),
                    ("gemini-2.5-flash-native-audio-dialog", "无限制模型", "无限制", "无限制", "无限制"),
                    ("gemini-2.5-pro", "专业模型", "2 / 3", "200 / 100K", "4 / 10"),
                    ("gemma-3-12b-it", "文本模型", "4 / 10", "500 / 50K", "8 / 20"),
                    ("gemma-3-2b-it", "轻量级文本模型", "5 / 20", "1K / 100K", "10 / 40"),
                    ("gemma-3-9b-it", "文本模型", "6 / 15", "750 / 75K", "12 / 30"),
                    ("gemma-2-27b-it", "文本模型", "4 / 10", "500 / 50K", "8 / 20"),
                    ("gemma-2-9b-it", "文本模型", "5 / 20", "1K / 100K", "10 / 40"),
                    ("gemma-2-2b-it", "轻量级文本模型", "10 / 50", "2K / 200K", "20 / 100"),
                    ("gemma-1.1-7b-it", "文本模型", "5 / 20", "1K / 100K", "10 / 40"),
                    ("gemma-1.1-2b-it", "轻量级文本模型", "10 / 50", "2K / 200K", "20 / 100"),
                    ("gemma-1-7b-it", "文本模型", "5 / 20", "1K / 100K", "10 / 40"),
                    ("gemma-1-2b-it", "轻量级文本模型", "10 / 50", "2K / 200K", "20 / 100"),
                    ("gemini-1.5-pro", "高级模型", "1 / 5", "100 / 10K", "2 / 10"),
                    ("gemini-1.5-flash", "文本输出模型", "2 / 5", "268 / 250K", "6 / 20"),
                    ("gemini-ultra", "高级模型", "1 / 5", "100 / 10K", "2 / 10"),
                    ("gemini-nano", "移动端模型", "10 / 50", "2K / 200K", "20 / 100"),
                    ("gemini-experimental", "实验模型", "1 / 2", "50 / 5K", "2 / 5"),
                ]
                
                # 打印所有模型的速率限制
                for model, category, rpm, tpm, rpd in rate_limits:
                    print(f"{model:<40} {category:<15} {rpm:<10} {tpm:<12} {rpd:<10}")
            else:
                print("\n注意：Gemini API的Python SDK没有直接提供查询具体限额数字的方法。")
                print("使用 --quota-details 参数查看详细的速率限制信息")
                print("要查看详细的限额信息，请访问：https://ai.dev/usage?tab=rate-limit")
            
        except Exception as e:
            error_msg = str(e)
            print(f"✗ API请求失败: {error_msg}")
            
            if "quota exceeded" in error_msg.lower() or "429" in error_msg:
                print("\n原因：API限额已用完")
                print("建议：")
                print("1. 等待限额重置（通常为分钟或天级）")
                print("2. 升级到付费计划以获得更多限额")
                print("3. 检查详细限额信息：https://ai.dev/usage?tab=rate-limit")
            elif "403" in error_msg or "permission denied" in error_msg.lower():
                print("\n原因：权限错误")
                print("建议：检查API密钥是否有效且已正确配置")
            elif "404" in error_msg:
                print("\n原因：模型不存在或不可用")
                print("建议：检查模型名称是否正确")
            else:
                print("\n原因：其他API错误")
                print("建议：检查网络连接或稍后重试")
            
            return False
        
        return True


def main():
    """
    主函数，用于命令行调用
    """
    import json
    
    parser = argparse.ArgumentParser(description="Gemini图片OCR识别、文档处理和直接提问工具")
    parser.add_argument("file_path", help="文件路径（可选，不提供则直接提问），支持图片和PDF文档", nargs='?')
    parser.add_argument("--question", default="图里有什么内容？", help="提问内容（图片识别时默认为'图里有什么内容？'，文档处理时默认为'文档内容是什么？'，直接提问时为必填）")
    # 保留server参数以保持兼容性，但实际上Gemini不使用服务器
    parser.add_argument("--server", default="", help="(Gemini不使用)服务器地址")
    # 保留headless参数以保持兼容性
    parser.add_argument("--headless", type=lambda x: x.lower() in ['true', 'yes', '1'], default=True, help="(Gemini不使用)是否使用无头模式")
    parser.add_argument("--verbose", action="store_true", help="显示详细日志")
    parser.add_argument("--check-quota", action="store_true", help="检查Gemini API限额")
    parser.add_argument("--quota-details", action="store_true", help="显示详细的速率限制信息")
    parser.add_argument("--type", choices=['image', 'document', 'auto'], default='auto', help="文件类型，默认为自动检测")
    
    args = parser.parse_args()
    
    # 创建OCR实例
    ocr = GeminiOCR()
    
    # 检查限额
    if args.check_quota:
        ocr.check_quota(args.quota_details)
        return
    
    # 检查参数：直接提问时必须提供question
    if not args.file_path and args.question == "图里有什么内容？":
        parser.error("直接提问时必须使用--question参数提供问题内容")
    
    # 执行识别、文档处理或提问
    result = None
    if args.file_path:
        # 根据文件类型或自动检测选择处理方式
        file_type = args.type
        if file_type == 'auto':
            # 自动检测文件类型
            ext = os.path.splitext(args.file_path)[1].lower()
            if ext in ['.pdf']:
                file_type = 'document'
            else:
                file_type = 'image'
        
        if file_type == 'document':
            # 处理文档
            result = ocr.process_document(args.file_path, args.question)
        else:
            # 处理图片
            result = ocr.recognize_image(args.file_path, args.question)
    else:
        # 直接提问
        result = ocr.ask_question(args.question)
    
    if result:
        if args.verbose:
            # 详细模式：显示完整API响应和聊天记录
            print("\n=== 完整API响应 ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 提取关键信息
        if result.get("success"):
            # 使用get_ocr_result从result中提取回答
            actual_response = ocr.get_ocr_result(result, args.question)
            print("\n=== 处理结果 ===")
            print(f"提问: {args.question}")
            print(f"回答: {actual_response}")
            
            if args.verbose:
                # 详细模式：显示聊天记录
                chat_history = result.get('chatHistory', [])
                print(f"\n聊天记录数量: {len(chat_history)}")
                
                # 打印每条聊天记录
                for i, msg in enumerate(chat_history):
                    print(f"\n消息 {i+1}:")
                    print(f"  类型: {msg.get('type', '')}")
                    print(f"  内容: {msg.get('content', '')}")
    else:
        print("处理失败")


if __name__ == "__main__":
    main()
