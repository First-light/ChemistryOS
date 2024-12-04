import sys
sys.path.append('src/chemistry_os/src')
import time
import Robot # type: ignore # 根目录在src下
import math
import numpy
from abc import ABC, abstractmethod
from enum import Enum, auto

class facility_state(Enum):
    IDLE = auto() # 空闲
    INIT = auto() # 初始化
    WAIT = auto() # 等待
    BUSY = auto() # 忙碌
    STOP = auto() # 停止
    ERROR = auto()  # 错误

class facility(ABC):
    def __init__(self,name:str,type:str):
        self.name = name
        self.type = type
        self.state = facility_state.INIT

    @abstractmethod
    def cmd(self,command:str):
        pass

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



    
