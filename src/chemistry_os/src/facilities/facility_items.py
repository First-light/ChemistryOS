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

    def cmd_error(self):
        print("error")

    def cmd_stop(self):
        print("stop")

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
