import sys
sys.path.append('src/chemistry_os/src')
import time
import Robot # type: ignore # 根目录在src下
import math
import numpy
from abc import ABC, abstractmethod
from enum import Enum, auto
from cmd_parser import PkgCmdParser

class facility_state(Enum):
    IDLE = auto() # 空闲
    INIT = auto() # 初始化
    WAIT = auto() # 等待
    BUSY = auto() # 忙碌
    STOP = auto() # 停止
    ERROR = auto()  # 错误

class facility(ABC):
    namelist = []
    def __init__(self,name:str,type:str):
        self.name = name
        self.type = type
        self.state = facility_state.INIT
        # 检查是否存在重复的 name 和 type 参数对
        if name in facility.namelist:
            raise ValueError(f"Duplicate name pair: {name}")
        # 存储 name 和 type 参数对
        facility.namelist.append(name)
        self.parser = PkgCmdParser(self.type)

    @abstractmethod
    def cmd_init(self):
        pass
    


class facility_temp(facility):
    public_param_1 = 0
    public_param_2 = 1
    type = "temp3"

    def __init__(self,name:str,new_param_1,new_param_2):
        super().__init__(name, facility_temp.type)
        self.cmd_init()
        self.new_param_1 = new_param_1
        self.new_param_2 = new_param_2

    def output(self,param1,param2):
        print("output:",param1,param2)

    def cmd_init(self):
        self.parser.register("output", self.output, {"param1": 0, "param2": 1}, "output test")
        self.parser.register("message", self.message,{}, "output message")

    def message(self):
        print("This is a temp facility")
        print("name:",self.name)
        print("type:",facility_temp.type)
        print("new_param_1:",self.new_param_1)
        print("new_param_2:",self.new_param_2)
"""
设备类模版
class facility_temp:

    public_param_1 = 0
    public_param_2 = 0

    def __init__(self,name:str,type:str,new_param_1,new_param_2 ......):
        super().__init__(name,type)
        ......

    def func_1(self):
    
    def func_2(self):

"""



    
