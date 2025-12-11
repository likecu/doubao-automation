#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包线程管理器
功能：
1. 使用多线程同时运行多个豆包工具实例
2. 支持动态配置线程数量、执行间隔和运行时长
3. 支持自定义豆包工具命令和参数
4. 提供线程状态监控和管理
5. 支持纯文字聊天、图片OCR和是/否判断三种模式
6. 保持豆包工具的活跃状态
"""

import threading
import subprocess
import time
import argparse
import sys
import os
import json
from datetime import datetime

class DoubaoWorker(threading.Thread):
    """
    豆包工作线程类，用于在单独的线程中运行豆包工具
    """
    def __init__(self, worker_id, mode, command, interval=60):
        """
        初始化豆包工作线程
        :param worker_id: 工作线程ID
        :param mode: 工作模式 (text/ocr/yesno)
        :param command: 要执行的豆包工具命令
        :param interval: 执行间隔（秒）
        """
        threading.Thread.__init__(self)
        self.worker_id = worker_id
        self.mode = mode
        self.command = command
        self.interval = interval
        self.running = False
        self.last_executed = None
        self.last_result = None
        self.last_error = None
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
    
    def run(self):
        """
        线程运行方法，定期执行豆包工具命令
        """
        self.running = True
        print(f"[{datetime.now()}] 工作线程 {self.worker_id} 启动 ({self.mode}模式)")
        print(f"[{datetime.now()}] 执行命令: {' '.join(self.command)}")
        
        while self.running:
            try:
                start_time = time.time()
                self.last_executed = datetime.now()
                
                # 执行豆包工具命令
                result = subprocess.run(
                    self.command,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                self.execution_count += 1
                
                if result.returncode == 0:
                    self.success_count += 1
                    self.last_result = result.stdout.strip()
                    self.last_error = None
                    print(f"[{datetime.now()}] 工作线程 {self.worker_id} 执行成功")
                    print(f"[{datetime.now()}] 结果: {self.last_result}")
                else:
                    self.error_count += 1
                    self.last_result = None
                    self.last_error = result.stderr.strip()
                    print(f"[{datetime.now()}] 工作线程 {self.worker_id} 执行失败，返回码: {result.returncode}")
                    print(f"[{datetime.now()}] 错误输出: {self.last_error}")
                    print(f"[{datetime.now()}] 标准输出: {result.stdout}")
                
                execution_time = time.time() - start_time
                print(f"[{datetime.now()}] 工作线程 {self.worker_id} 执行耗时: {execution_time:.2f}秒")
                
            except subprocess.TimeoutExpired:
                self.error_count += 1
                self.execution_count += 1
                self.last_result = None
                self.last_error = "执行超时"
                print(f"[{datetime.now()}] 工作线程 {self.worker_id} 执行超时")
            except Exception as e:
                self.error_count += 1
                self.execution_count += 1
                self.last_result = None
                self.last_error = str(e)
                print(f"[{datetime.now()}] 工作线程 {self.worker_id} 执行异常: {str(e)}")
            
            # 等待指定间隔后再次执行
            if self.running:
                time.sleep(self.interval)
    
    def stop(self):
        """
        停止线程运行
        """
        self.running = False
        print(f"[{datetime.now()}] 工作线程 {self.worker_id} 已停止")
    
    def get_status(self):
        """
        获取线程状态信息
        """
        return {
            'worker_id': self.worker_id,
            'mode': self.mode,
            'running': self.running,
            'last_executed': self.last_executed.strftime('%Y-%m-%d %H:%M:%S') if self.last_executed else None,
            'interval': self.interval,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'last_result': self.last_result,
            'last_error': self.last_error
        }

class DoubaoThreadManager:
    """
    豆包线程管理器类，用于管理多个豆包工作线程
    """
    def __init__(self):
        """
        初始化豆包线程管理器
        """
        self.workers = []
        self.worker_counter = 0
        self.manager_running = False
    
    def add_worker(self, mode, command, interval=60):
        """
        添加新的工作线程
        :param mode: 工作模式 (text/ocr/yesno)
        :param command: 要执行的豆包工具命令
        :param interval: 执行间隔（秒）
        :return: 工作线程ID
        """
        self.worker_counter += 1
        worker = DoubaoWorker(self.worker_counter, mode, command, interval)
        self.workers.append(worker)
        worker.start()
        return self.worker_counter
    
    def remove_worker(self, worker_id):
        """
        移除指定的工作线程
        :param worker_id: 工作线程ID
        :return: 是否成功移除
        """
        for worker in self.workers:
            if worker.worker_id == worker_id:
                worker.stop()
                worker.join()
                self.workers.remove(worker)
                return True
        return False
    
    def start_all(self):
        """
        启动所有工作线程
        """
        for worker in self.workers:
            if not worker.running:
                worker.start()
    
    def stop_all(self):
        """
        停止所有工作线程
        """
        for worker in self.workers:
            worker.stop()
        
        for worker in self.workers:
            worker.join()
        
        self.workers.clear()
        self.worker_counter = 0
    
    def get_status(self):
        """
        获取所有工作线程的状态信息
        :return: 工作线程状态列表
        """
        return [worker.get_status() for worker in self.workers]
    
    def monitor_status(self, interval=10):
        """
        监控并输出所有工作线程的状态信息
        :param interval: 监控间隔（秒）
        """
        self.manager_running = True
        while self.manager_running:
            print(f"\n[{datetime.now()}] === 豆包线程管理器状态 ===")
            print(f"[{datetime.now()}] 活跃线程数: {len(self.workers)}")
            
            for status in self.get_status():
                print(f"\n[{datetime.now()}] 线程ID: {status['worker_id']}")
                print(f"[{datetime.now()}] 模式: {status['mode']}")
                print(f"[{datetime.now()}] 运行状态: {'运行中' if status['running'] else '已停止'}")
                print(f"[{datetime.now()}] 最后执行时间: {status['last_executed']}")
                print(f"[{datetime.now()}] 执行间隔: {status['interval']}秒")
                print(f"[{datetime.now()}] 总执行次数: {status['execution_count']}")
                print(f"[{datetime.now()}] 成功次数: {status['success_count']}")
                print(f"[{datetime.now()}] 失败次数: {status['error_count']}")
                if status['last_result']:
                    print(f"[{datetime.now()}] 最后结果: {status['last_result'][:50]}{'...' if len(status['last_result']) > 50 else ''}")
                if status['last_error']:
                    print(f"[{datetime.now()}] 最后错误: {status['last_error'][:50]}{'...' if len(status['last_error']) > 50 else ''}")
            
            time.sleep(interval)
    
    def stop_monitor(self):
        """
        停止状态监控
        """
        self.manager_running = False

def build_command(mode, args, script_dir):
    """
    根据模式和参数构建豆包工具命令
    :param mode: 工作模式 (text/ocr/yesno)
    :param args: 命令行参数
    :param script_dir: 脚本目录路径
    :return: 构建好的命令列表
    """
    python_path = "/Volumes/600g/app1/okx-py/bin/python3"
    command = [python_path]
    
    if mode == "text":
        # 纯文字聊天模式
        text_script = os.path.join(script_dir, "doubao_text_chat.py")
        command.extend([text_script, args.message])
        command.extend(["--headless", str(not args.debug).lower()])
    elif mode == "ocr":
        # 图片OCR模式
        ocr_script = os.path.join(script_dir, "doubao_ocr.py")
        command.extend([ocr_script, args.image])
        if args.question:
            command.extend(["--question", args.question])
        command.extend(["--headless", str(not args.debug).lower()])
    elif mode == "yesno":
        # 是/否判断模式
        yesno_script = os.path.join(script_dir, "doubao_yes_no.py")
        command.extend([yesno_script, "--question", args.question])
        if args.file:
            command.extend(["--file", args.file])
        elif args.image:
            command.extend(["--image", args.image])
        if args.debug:
            command.append("--debug")
    
    return command

def main():
    """
    主函数，用于命令行调用
    """
    parser = argparse.ArgumentParser(description="豆包线程管理器")
    
    # 模式选择
    parser.add_argument("--mode", choices=["text", "ocr", "yesno"], default="yesno", help="工作模式")
    
    # 豆包工具参数
    parser.add_argument("--message", default="你好，豆包", help="纯文字聊天消息")
    parser.add_argument("--question", default="地球是圆的吗？", help="提问内容")
    parser.add_argument("--file", help="文件路径")
    parser.add_argument("--image", help="图片路径")
    parser.add_argument("--debug", action="store_true", help="输出调试信息并显示浏览器界面")
    
    # 多线程参数
    parser.add_argument("--threads", type=int, default=2, help="线程数量")
    parser.add_argument("--interval", type=int, default=60, help="执行间隔（秒）")
    parser.add_argument("--duration", type=int, help="运行时长（秒），不指定则一直运行")
    parser.add_argument("--monitor", action="store_true", help="启用线程状态监控")
    
    args = parser.parse_args()
    
    # 验证参数
    if args.mode == "ocr" and not args.image:
        print("错误: OCR模式必须提供图片路径")
        sys.exit(1)
    
    if args.mode == "yesno" and args.file and args.image:
        print("错误: 是/否判断模式中文件和图片不能同时提供")
        sys.exit(1)
    
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建豆包工具命令
    command = build_command(args.mode, args, script_dir)
    
    # 创建豆包线程管理器
    manager = DoubaoThreadManager()
    
    try:
        # 添加指定数量的工作线程
        for _ in range(args.threads):
            manager.add_worker(args.mode, command.copy(), args.interval)
        
        # 启动状态监控线程（如果启用）
        monitor_thread = None
        if args.monitor:
            monitor_thread = threading.Thread(target=manager.monitor_status)
            monitor_thread.daemon = True
            monitor_thread.start()
        
        # 如果指定了运行时长，则在时长结束后停止所有线程
        if args.duration:
            print(f"\n[{datetime.now()}] 豆包线程管理器将运行 {args.duration} 秒")
            time.sleep(args.duration)
        else:
            # 否则一直运行，直到用户中断
            print(f"\n[{datetime.now()}] 豆包线程管理器已启动，按 Ctrl+C 停止所有线程")
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] 用户中断，停止所有线程")
    
    finally:
        # 停止所有工作线程
        manager.stop_all()
        
        if monitor_thread:
            manager.stop_monitor()
            monitor_thread.join()
        
        print(f"\n[{datetime.now()}] 豆包线程管理器已停止")

if __name__ == "__main__":
    main()