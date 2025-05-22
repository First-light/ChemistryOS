import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from structs import FacilityState
from time import sleep

class Item_Cup(Facility):
    type = "cup"
    data = {"param1": 0, "param2": 1}

    def __init__(self,name:str,):
        super().__init__(name,Item_Cup.type)
        

    def cmd_init(self):
        self.parser.register("data", self.show_data, {"param1": 0, "param2": 1}, "output test")

    def listen(self):
        while True:
            if self.state == FacilityState.ERROR:
                break
            if self.state == FacilityState.STOP:
                break
            sleep(0.005)


    def show_data(self):
        print("type:",Item_Cup.type)
        print("name:",self.name)
        print("data:",Item_Cup.data)
    
    def wait(self,time):
        print("wait ",time)
        sleep(time)

        

class Point(Facility):
    type = "point"
    def __init__(self,name:str,):
        super().__init__(name,Point.type)
        self.name = name
        self.destination = [0, 0, 0]
        self.catch_pre_offset = 0.0
        self.put_height = 0.0
        self.catch_direction = [0.0, 0.0, 0.0]
        self.safe_place_id = 0
        self.state = FacilityState.STOP # 设施状态初始化为stop，防止在未设置状态时就调用设施的命令

    def cmd_init(self):
        self.parser.register("data", self.show_data, {}, "output test")
        self.parser.register("enable", self.enable, {"x": 0, "y": 0, "z": 0}, "set destination")
        self.parser.register("disable", self.disable, {"offset": 0.0}, "set catch pre offset")

    def enable(self):
        self.state = FacilityState.IDLE
        self.log.info("enable")

    def disable(self):
        self.state = FacilityState.STOP
        self.log.info("disable")

    def show_data(self):
        print("type:",Point.type)
        print("name:",self.name)
        print("destination:",self.destination)
        print("catch_pre_offset:",self.catch_pre_offset)
        print("put_height:",self.put_height)
        print("catch_direction:",self.catch_direction)
        print("safe_place_id:",self.safe_place_id)
