#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包API调用工具集 - 公共模块
包含各个模块共用的方法和功能
"""

import subprocess
import json
import os
import sys

def execute_node_script(script_path, args, timeout=60):
    """
    执行Node.js脚本并获取输出
    
    :param script_path: Node.js脚本路径
    :param args: 传递给脚本的参数列表
    :param timeout: 超时时间（秒）
    :return: subprocess.run的返回结果
    """
    cmd = ["node", script_path] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"脚本执行超时，超时时间: {timeout}秒")
        return None
    except Exception as e:
        print(f"执行脚本时发生错误: {e}")
        return None

def parse_json_output(output):
    """
    从输出中提取并解析JSON数据
    
    :param output: 脚本输出
    :return: 解析后的JSON数据或None
    """
    if not output:
        return None
    
    try:
        # 找到JSON的起始位置（第一个{）
        json_start = output.find('{')
        if json_start == -1:
            print("未找到JSON数据")
            return None
        
        # 找到JSON的结束位置（最后一个}）
        json_end = output.rfind('}') + 1
        if json_end <= json_start:
            print("未找到完整的JSON数据")
            return None
        
        # 提取JSON部分
        json_str = output[json_start:json_end]
        print(f"提取的JSON字符串: {json_str}")
        
        # 解析JSON
        output_data = json.loads(json_str)
        return output_data
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"原始输出: {output}")
        return None
    except Exception as e:
        print(f"解析JSON时发生错误: {e}")
        return None

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

def get_default_node_script(script_name):
    """
    获取默认的Node.js脚本路径
    
    :param script_name: 脚本名称
    :return: 脚本的绝对路径
    """
    script_dir = get_script_dir()
    # Node.js脚本现在位于js目录下
    return os.path.join(os.path.dirname(script_dir), "js", script_name)

def format_headless_param(headless):
    """
    格式化无头模式参数
    
    :param headless: 布尔值，表示是否使用无头模式
    :return: 字符串形式的无头模式参数
    """
    return str(headless).lower()

def ensure_dir_exists(dir_path):
    """
    确保目录存在
    
    :param dir_path: 目录路径
    """
    os.makedirs(dir_path, exist_ok=True)

def handle_script_result(result):
    """
    处理脚本执行结果
    
    :param result: subprocess.run的返回结果
    :return: 脚本输出或None
    """
    if result is None:
        return None
    
    if result.returncode != 0:
        print(f"Node.js脚本执行失败，返回码: {result.returncode}")
        print(f"错误输出: {result.stderr}")
        print(f"标准输出: {result.stdout}")
        return None
    
    return result.stdout
