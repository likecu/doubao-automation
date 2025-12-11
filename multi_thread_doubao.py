#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包多线程调用脚本
功能：
1. 使用多线程同时运行多个豆包工具实例
2. 支持配置线程数量
3. 支持自定义豆包工具命令和参数
4. 保持豆包工具的活跃状态
"""

import threading
import subprocess
import time
import argparse
import sys
import os

class DoubaoThread(threading.Thread):
    """
    豆包线程类，用于在单独的线程中运行豆包工具
    """
    def __init__(self, thread_id, command, interval=60):
        """
        初始化豆包线程
        :param thread_id: 线程ID
        :param command: 要执行的豆包工具命令
        :param interval: 执行间隔（秒）
        """
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.command = command
        self.interval = interval
        self.running = True
    
    def run(self):
        """
        线程运行方法，定期执行豆包工具命令
        """
        print(f"线程 {self.thread_id} 启动，执行命令: {' '.join(self.command)}")
        while self.running:
            try:
                # 执行豆包工具命令
                result = subprocess.run(
                    self.command,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                # 输出执行结果
                if result.returncode == 0:
                    print(f"线程 {self.thread_id} 执行成功: {result.stdout.strip()}")
                else:
                    print(f"线程 {self.thread_id} 执行失败，返回码: {result.returncode}")
                    print(f"错误输出: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"线程 {self.thread_id} 执行超时")
            except Exception as e:
                print(f"线程 {self.thread_id} 执行异常: {str(e)}")
            
            # 等待指定间隔后再次执行
            if self.running:
                time.sleep(self.interval)
    
    def stop(self):
        """
        停止线程运行
        """
        self.running = False
        print(f"线程 {self.thread_id} 已停止")

def main():
    """
    主函数，用于命令行调用
    """
    parser = argparse.ArgumentParser(description="豆包多线程调用脚本")
    
    # 豆包工具参数
    parser.add_argument("--question", default="地球是圆的吗？", help="判断的问题")
    parser.add_argument("--file", help="文件路径")
    parser.add_argument("--image", help="图片路径")
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_node_script = os.path.join(script_dir, "doubao_chat_bot.js")
    parser.add_argument("--node_script", default=default_node_script, help="Node.js脚本路径")
    parser.add_argument("--debug", action="store_true", help="输出调试信息")
    
    # 多线程参数
    parser.add_argument("--threads", type=int, default=2, help="线程数量")
    parser.add_argument("--interval", type=int, default=60, help="执行间隔（秒）")
    parser.add_argument("--duration", type=int, help="运行时长（秒），不指定则一直运行")
    
    args = parser.parse_args()
    
    # 验证参数
    if args.file and args.image:
        print("错误: 文件和图片不能同时提供")
        sys.exit(1)
    
    # 构建豆包工具命令
    python_path = "/Volumes/600g/app1/okx-py/bin/python3"
    yes_no_script = os.path.join(script_dir, "doubao_yes_no.py")
    
    command = [python_path, yes_no_script, "--question", args.question]
    
    if args.file:
        command.extend(["--file", args.file])
    elif args.image:
        command.extend(["--image", args.image])
    
    command.extend(["--node_script", args.node_script])
    
    if args.debug:
        command.append("--debug")
    
    # 创建并启动线程
    threads = []
    for i in range(args.threads):
        thread = DoubaoThread(i+1, command, args.interval)
        threads.append(thread)
        thread.start()
        # 线程启动间隔，避免同时发起多个请求
        time.sleep(5)
    
    try:
        # 如果指定了运行时长，则在时长结束后停止所有线程
        if args.duration:
            print(f"将在 {args.duration} 秒后停止所有线程")
            time.sleep(args.duration)
            for thread in threads:
                thread.stop()
        else:
            # 否则一直运行，直到用户中断
            print("按 Ctrl+C 停止所有线程")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断，停止所有线程")
        for thread in threads:
            thread.stop()
    
    # 等待所有线程结束
    for thread in threads:
        thread.join()
    
    print("所有线程已停止")

if __name__ == "__main__":
    main()