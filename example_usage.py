#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包线程管理器使用示例
功能：
1. 演示如何在Python程序中集成使用豆包线程管理器
2. 展示如何管理多个不同类型的豆包任务
3. 提供配置文件管理示例
"""

import os
import time
import json
from doubao_thread_manager import DoubaoThreadManager

# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_PATH = "/Volumes/600g/app1/okx-py/bin/python3"

def create_text_chat_command(message, debug=False):
    """
    创建纯文字聊天命令
    :param message: 聊天消息
    :param debug: 是否开启调试模式
    :return: 命令列表
    """
    text_script = os.path.join(SCRIPT_DIR, "doubao_text_chat.py")
    return [PYTHON_PATH, text_script, message, "--headless", str(not debug).lower()]

def create_ocr_command(image_path, question="图里有什么内容？", debug=False):
    """
    创建图片OCR命令
    :param image_path: 图片路径
    :param question: 提问内容
    :param debug: 是否开启调试模式
    :return: 命令列表
    """
    ocr_script = os.path.join(SCRIPT_DIR, "doubao_ocr.py")
    command = [PYTHON_PATH, ocr_script, image_path]
    if question:
        command.extend(["--question", question])
    command.extend(["--headless", str(not debug).lower()])
    return command

def create_yesno_command(question, file=None, image=None, debug=False):
    """
    创建是/否判断命令
    :param question: 提问内容
    :param file: 文件路径
    :param image: 图片路径
    :param debug: 是否开启调试模式
    :return: 命令列表
    """
    yesno_script = os.path.join(SCRIPT_DIR, "doubao_yes_no.py")
    command = [PYTHON_PATH, yesno_script, "--question", question]
    if file:
        command.extend(["--file", file])
    elif image:
        command.extend(["--image", image])
    if debug:
        command.append("--debug")
    return command

def load_tasks_from_config(config_file):
    """
    从配置文件加载任务
    :param config_file: 配置文件路径
    :return: 任务列表
    """
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("tasks", [])

def save_tasks_to_config(tasks, config_file):
    """
    将任务保存到配置文件
    :param tasks: 任务列表
    :param config_file: 配置文件路径
    """
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump({"tasks": tasks}, f, ensure_ascii=False, indent=2)

def example_basic_usage():
    """
    基本用法示例：创建多个不同类型的豆包任务
    """
    print("=== 基本用法示例 ===")
    
    # 创建线程管理器
    manager = DoubaoThreadManager()
    
    try:
        # 添加纯文字聊天任务 (每30秒执行一次)
        text_command = create_text_chat_command("你好，豆包")
        manager.add_worker("text", text_command, interval=30)
        
        # 添加是/否判断任务 (每2分钟执行一次)
        yesno_command = create_yesno_command("地球是圆的吗？")
        manager.add_worker("yesno", yesno_command, interval=120)
        
        # 添加图片OCR任务 (每5分钟执行一次)
        # ocr_command = create_ocr_command("/path/to/image.png", "图里有什么？")
        # manager.add_worker("ocr", ocr_command, interval=300)
        
        # 运行5分钟后停止
        print("线程管理器已启动，将运行5分钟后停止")
        for i in range(1, 6):
            time.sleep(60)
            print(f"已运行 {i} 分钟")
            
            # 获取并打印线程状态
            print("\n当前线程状态：")
            for status in manager.get_status():
                print(f"线程 {status['worker_id']} ({status['mode']}): 运行中={status['running']}, 成功次数={status['success_count']}")
                if status['last_result']:
                    print(f"  最后结果: {status['last_result'][:100]}...")
                if status['last_error']:
                    print(f"  最后错误: {status['last_error'][:100]}...")
    
    except KeyboardInterrupt:
        print("用户中断，停止线程管理器")
    
    finally:
        manager.stop_all()
        print("线程管理器已停止")

def example_config_file():
    """
    配置文件用法示例：从配置文件加载和管理任务
    """
    print("\n=== 配置文件用法示例 ===")
    
    # 示例配置文件
    config_file = os.path.join(SCRIPT_DIR, "doubao_tasks.json")
    
    # 创建示例任务配置
    example_tasks = [
        {
            "name": "定期问候",
            "mode": "text",
            "message": "你好，豆包",
            "interval": 60,
            "debug": False
        },
        {
            "name": "是/否判断",
            "mode": "yesno",
            "question": "地球是圆的吗？",
            "interval": 120,
            "debug": False
        },
        {
            "name": "图片内容识别",
            "mode": "ocr",
            "image": "/path/to/image.png",
            "question": "图里有什么？",
            "interval": 300,
            "debug": False
        }
    ]
    
    # 保存配置文件
    save_tasks_to_config(example_tasks, config_file)
    print(f"已创建示例配置文件: {config_file}")
    print("配置文件内容:")
    print(json.dumps({"tasks": example_tasks}, ensure_ascii=False, indent=2))
    
    # 从配置文件加载任务
    tasks = load_tasks_from_config(config_file)
    
    # 创建线程管理器
    manager = DoubaoThreadManager()
    
    try:
        # 根据配置添加任务
        for task in tasks:
            mode = task["mode"]
            interval = task.get("interval", 60)
            debug = task.get("debug", False)
            
            if mode == "text":
                command = create_text_chat_command(task["message"], debug)
            elif mode == "yesno":
                command = create_yesno_command(task["question"], None, None, debug)
            elif mode == "ocr":
                command = create_ocr_command(task["image"], task.get("question"), debug)
            else:
                print(f"未知模式: {mode}")
                continue
            
            manager.add_worker(mode, command, interval)
            print(f"已添加任务: {task['name']} ({mode}模式，间隔{interval}秒)")
        
        # 运行3分钟后停止
        print("\n线程管理器已启动，将运行3分钟后停止")
        time.sleep(180)
        
    except KeyboardInterrupt:
        print("用户中断，停止线程管理器")
    
    finally:
        manager.stop_all()
        print("线程管理器已停止")
        
        # 清理示例配置文件
        if os.path.exists(config_file):
            os.remove(config_file)
            print(f"已删除示例配置文件: {config_file}")

def example_dynamic_tasks():
    """
    动态任务管理示例：动态添加和移除任务
    """
    print("\n=== 动态任务管理示例 ===")
    
    # 创建线程管理器
    manager = DoubaoThreadManager()
    
    try:
        # 添加第一个任务
        task1_command = create_yesno_command("地球是圆的吗？")
        task1_id = manager.add_worker("yesno", task1_command, interval=60)
        print(f"已添加任务1，ID: {task1_id}")
        
        # 运行30秒后添加第二个任务
        time.sleep(30)
        task2_command = create_text_chat_command("今天天气怎么样？")
        task2_id = manager.add_worker("text", task2_command, interval=90)
        print(f"已添加任务2，ID: {task2_id}")
        
        # 运行60秒后移除第一个任务
        time.sleep(60)
        if manager.remove_worker(task1_id):
            print(f"已移除任务1，ID: {task1_id}")
        else:
            print(f"移除任务1失败，ID: {task1_id}")
        
        # 运行30秒后停止所有任务
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("用户中断，停止线程管理器")
    
    finally:
        manager.stop_all()
        print("线程管理器已停止")

if __name__ == "__main__":
    # 运行示例
    example_basic_usage()
    example_config_file()
    example_dynamic_tasks()