import sys
import os
from datetime import datetime
from typing import Literal

class FileUtils:
    log_file_stack:str=""
    def __init__(self):
        pass

    @staticmethod
    def get_log_file_path(
        log_prefix: str = "facilities",
        numbering_mode: Literal["timestamp", "sequential"] = "timestamp",
        log_dir: str = None
    ) -> str:
        """
        获取日志文件路径
        
        :param log_prefix: 日志文件前缀名
        :param numbering_mode: 编号模式 - "timestamp" 或 "sequential"
        :param log_dir: 自定义日志目录，如果为 None 则使用默认的项目根目录/log
        :return: 完整的日志文件路径
        """
        # 动态获取日志目录路径，基于 sys.path[0]
        if FileUtils.log_file_stack == "":
            if log_dir is None:
                base_dir = sys.path[0]  # 获取当前项目的根目录
                log_dir = os.path.join(base_dir, 'log')  # 将日志目录设置为项目根目录下的 log 文件夹
            
            # 确保日志目录存在
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)  # 如果目录不存在，则创建
            
            if numbering_mode == "timestamp":
                # 时间戳模式
                timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                log_file = os.path.join(log_dir, f'{log_prefix}_{timestamp}.log')
            else:
                # 自然编号模式
                log_file = FileUtils._get_sequential_log_file(log_dir, log_prefix)
            FileUtils.log_file_stack = log_file
        else:
            log_file = FileUtils.log_file_stack
            
        return log_file
    
    @staticmethod
    def _get_sequential_log_file(log_dir: str, log_prefix: str) -> str:
        """
        获取按序号编号的日志文件路径，自动找到可用的序号
        
        :param log_dir: 日志目录
        :param log_prefix: 日志文件前缀
        :return: 完整的日志文件路径
        """
        # 扫描现有文件，找到最大序号
        existing_numbers = []
        
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.startswith(f'{log_prefix}_') and filename.endswith('.log'):
                    # 提取序号部分
                    try:
                        number_part = filename[len(f'{log_prefix}_'):-4]  # 去掉前缀和 .log
                        if number_part.isdigit():
                            existing_numbers.append(int(number_part))
                    except (ValueError, IndexError):
                        continue
        
        # 找到最小的可用序号（从1开始）
        next_number = 1
        while next_number in existing_numbers:
            next_number += 1
        
        log_file = os.path.join(log_dir, f'{log_prefix}_{next_number}.log')
        return log_file

