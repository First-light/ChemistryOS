import sys
sys.path.append('src/chemistry_os/src')
from abc import ABC, abstractmethod
from enum import Enum, auto
from facilities.pkgcmd import PkgCmdParser

class FacilityState(Enum):
    IDLE = auto() # 空闲
    WAIT = auto() # 等待
    BUSY = auto() # 忙碌
    STOP = auto() # 停止
    ERROR = auto()  # 错误

class Facility(ABC):

    tuple_list = []

    def __init__(self,name:str,type:str):
        self.name = name
        self.type = type
        self.parser = PkgCmdParser(self.name)

        self._state = FacilityState.IDLE
        self.data = {"state":self.state}

        self.cmd_init()
        # 检查是否存在重复的 name 和 type 参数对
        if any(name == pair[0] for pair in Facility.tuple_list):
            raise ValueError(f"Duplicate name pair: {name}")
        # 存储 name 和 type 参数对
        Facility.tuple_list.append((name,type,self.parser.cmd,self.data))
        # self.facility_init()

    # def facility_init(self):

    def cmd_print(self,message):
        print(f"{self.name}: {message}")

    def cmd_print_head(self):
        print(f"{self.name}: ",end='')

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self,state):
        self._state = state

    @abstractmethod
    def cmd_init(self):
        pass
    

        





        





    
