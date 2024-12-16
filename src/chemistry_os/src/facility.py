import sys
sys.path.append('src/chemistry_os/src')
from abc import ABC, abstractmethod
from enum import Enum, auto
from facilities.pkgcmd import PkgCmdParser

class FacilityState(Enum):
    IDLE = auto() # 空闲
    INIT = auto() # 初始化
    WAIT = auto() # 等待
    BUSY = auto() # 忙碌
    STOP = auto() # 停止
    ERROR = auto()  # 错误

class Facility(ABC):
    tuple_list = []
    def __init__(self,name:str):
        self.name = name
        self.state = FacilityState.INIT
        self.parser = PkgCmdParser(self.name)
        self.cmd_init()
        # 检查是否存在重复的 name 和 type 参数对
        if any(name == pair[0] for pair in Facility.tuple_list):
            raise ValueError(f"Duplicate name pair: {name}")
        # 存储 name 和 type 参数对
        Facility.tuple_list.append((name,self.parser.cmd,self))
        # self.facility_init()

    # def facility_init(self):

    def cmd_print(self,message):
        print(f"{self.name}: {message}")

    def cmd_print_head(self):
        print(f"{self.name}: ",end='')

    @abstractmethod
    def cmd_init(self):
        pass
    

class FacilityTemp(Facility):
    public_param_1 = 0
    public_param_2 = 1

    def __init__(self,name:str,param1,param2):
        super().__init__(name)
        self.param1 = param1
        self.param2 = param2
        

    def output(self,param1,param2):
        print("output:",param1,param2)

    def cmd_init(self):
        self.parser.register("output", self.output, {"param1": 0, "param2": 1}, "output test")
        self.parser.register("message", self.message,{}, "output message")

    def message(self):
        print("This is a temp facility")
        print("name:",self.name)
        print("new_param_1:",self.param1)
        print("new_param_2:",self.param2)

        





        





    
