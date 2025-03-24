import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from structs import FacilityState
from time import sleep

class FacilityCup(Facility):
    type = "cup"

    def __init__(self,name:str):
        super().__init__(name,FacilityCup.type)
        

    def cmd_init(self):
        self.parser.register("output", self.output, {"param1": 0, "param2": 1}, "output test")
        self.parser.register("message", self.message,{}, "output message")
        self.parser.register("wait", self.wait, {"time": 0}, "wait for time")
        self.parser.register("control", self.control, {}, "control")

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


    def message(self):
        print("This is a temp facility")
        print("name:",self.name)
        print("new_param_1:",self.param1)
        print("new_param_2:",self.param2)
    
    def wait(self,time):
        print("wait ",time)
        sleep(time)

    def control(self):
        print("control")
        user_input = input("Please enter any character: ")
        print("You entered:", user_input)
