import sys
import logging  # 添加日志模块
import os
from datetime import datetime  # 用于生成时间戳

sys.path.append('src/chemistry_os/src')
from abc import ABC, abstractmethod
from facilities.pkgcmd import PkgCmdParser
from structs import FacilityState
from structs import ServerMod
import time


class Facility(ABC):
    tuple_list = []
    log_cache = []  # 公用日志缓存区
    log_cache_dict = {
        "data": None,
        "server_mod": int(ServerMod.SKIP.value),
    }  # 公用日志缓存区字典

    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type
        self.state = [0]
        self.state[0] = FacilityState.IDLE
        

        # self.object_init_list = ["flowdisplay"]  # 用于存储对象初始化列表

        # if type not in self.object_init_list:
        #     for facility in Facility.tuple_list:
        #         if facility[0] == name and isinstance(facility[3], expected_type):
        #             return facility[3]  # 返回实例化的对象引用


        # 初始化日志记录器
        self.log_init()
        self.parser = PkgCmdParser(self.name, self.state,self.log)

        # 注册父类的命令
        self.cmd_public_init()
        # 注册子类的命令
        self.cmd_init()
        
        # 检查是否存在重复的 name 和 type 参数对
        if any(name == pair[0] for pair in Facility.tuple_list):
            self.log.warning(f"重复设备名称：{name}")
        # 存储 name 和 type 参数对
        else:
            Facility.tuple_list.append((name, type, self.parser.cmd, self))
            self.log.info(f"成功实例化对象：{self}")
        
    def delay(self, sec):
        print("delay ", sec)
        time.sleep(sec)

    # 公共命令初始化的函数
    def cmd_public_init(self):
        self.parser.register("delay", self.delay,{"sec": 0},"Delay for a specified time")

    # 命令初始化的函数
    @abstractmethod
    def cmd_init(self):
        pass

    def cmd_error(self):
        self.log.error("error")

    def cmd_stop(self):
        self.log.info("stop")
        
    def find_object_by_name(name: str, if_log: bool = False):
        """
        根据名称从 Facility.tuple_list 中找到对应的对象实例。
        
        :param name: 要查找的对象名称
        :param log_output: 是否输出日志信息，默认为 False
        :return: 对应的对象实例，如果未找到则返回 None
        """
        for i, tuple_t in enumerate(Facility.tuple_list):
            obj_name = tuple_t[0]  # 对象名称
            obj_instance = tuple_t[3]  # 对应的对象实例
            if obj_name == name:
                if if_log:
                    logging.info(f"找到对象: {obj_name}")
                return obj_instance
        if if_log:
            logging.warning(f"未找到名称为 {name} 的对象")
        return None

    def show_logs(self):
        """
        显示当前日志缓存区中的所有日志信息
        """
        if not Facility.log_cache:
            print("=PRINT=")
            print("日志缓存区为空")
        else:
            print("当前日志缓存区内容:")
            for log in Facility.log_cache:
                print(log)
            print("=PRINT-END=")
    
    def log_init(self):
        """
        初始化日志记录器，支持控制台和文件输出，并确保日志目录和文件存在
        """
        # 创建日志记录器
        self.log = logging.getLogger(self.name)  # 使用实例的 name 作为日志记录器名称
        self.log.setLevel(logging.INFO)  # 设置日志级别为 INFO
        # 创建文件日志格式（包含时间戳）
        file_formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M'
        )
        # 创建控制台日志格式（不包含时间戳）
        console_formatter = logging.Formatter(
            fmt='[%(name)s] [%(levelname)s]: %(message)s'
        )
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        # 动态获取日志目录路径，基于 sys.path[0]
        base_dir = sys.path[0]  # 获取当前项目的根目录
        self.log_dir = os.path.join(base_dir, 'log')  # 将日志目录设置为项目根目录下的 log 文件夹
        # 确保日志目录存在
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)  # 如果目录不存在，则创建
        # 确保日志文件存在
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')  # 格式化当前时间
        log_file = os.path.join(self.log_dir, f'facilities_{timestamp}.log')  # 日志文件路径

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        # 将处理器添加到日志记录器
        self.log.addHandler(console_handler)
        self.log.addHandler(file_handler)
        # 避免重复添加处理器
        self.log.propagate = False

        # 添加日志到缓存区
        self.log.addHandler(self.cache_handler())

    def cache_handler(self):
        """
        创建一个处理器，用于将日志信息存储到公用缓存区
        """
        class CacheHandler(logging.Handler):
            def emit(self, record):
                log_entry = self.format(record)
                Facility.log_cache.append(log_entry)  # 将日志信息存储到公用缓存区

        cache_handler = CacheHandler()
        cache_handler.setFormatter(logging.Formatter(
            fmt='[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s',
            datefmt='%Y-%m-%d %H:%M'
        ))
        return cache_handler

    @staticmethod
    def read_log_cache():
        """
        只读缓存区里的日志信息
        :return: 缓存区中的所有日志信息
        """
        return Facility.log_cache

    @staticmethod
    def extract_log_cache():
        """
        抽取缓存区的所有日志信息，并清空缓存区
        :return: 缓存区中的所有日志信息
        """
        logs = Facility.log_cache[:]
        Facility.log_cache.clear()
        return logs
    
    def log_cache_dict_update():
        """
        更新日志缓存字典中的数据
        """

        extracted_logs = Facility.extract_log_cache()
        if extracted_logs:# 如果没有日志数据，则设置 server_mod 为 SKIP
            Facility.log_cache_dict["data"] = extracted_logs
            Facility.log_cache_dict["server_mod"] = int(ServerMod.ADJUST.value)
