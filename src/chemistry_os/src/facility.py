import sys
sys.path.append('src/chemistry_os/src')
from abc import ABC, abstractmethod
from facilities.pkgcmd import PkgCmdParser
from structs import FacilityState

class Facility(ABC):

    tuple_list = []

    def __init__(self,name:str,type:str):
        self.name = name
        self.type = type
        self.state = [0]
        self.state[0] = FacilityState.IDLE
        self.parser = PkgCmdParser(self.name,self.state)

        self.cmd_init()
        # 检查是否存在重复的 name 和 type 参数对
        if any(name == pair[0] for pair in Facility.tuple_list):
            raise ValueError(f"Duplicate name pair: {name}")
        # 存储 name 和 type 参数对
        Facility.tuple_list.append((name,type,self.parser.cmd,self))
        # self.facility_init()

    # def facility_init(self):

    def cmd_print(self,message):
        print(f"{self.name}: {message}")

    def cmd_print_head(self):
        print(f"{self.name}: ",end='')

    def message_start(self):
        print("\n<",self.name,">:")

    def message_head(self):
        print("<",self.name,">: ",end="")

    def message_end(self):
        print("\n")


    # 命令初始化的函数
    @abstractmethod
    def cmd_init(self):
        pass
    
    # 处理错误的函数
    @abstractmethod
    def cmd_error(self):
        pass

    # 处理流程停止的函数
    @abstractmethod
    def cmd_stop(self):
        pass

        





        





    
