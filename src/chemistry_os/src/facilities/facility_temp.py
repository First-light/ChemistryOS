import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from time import sleep


class FacilityTemp(Facility):
    type = "temp"
    public_param_1 = 0
    public_param_2 = 1

    def __init__(self,name:str,param1,param2):
        super().__init__(name,FacilityTemp.type)
        self.param1 = param1
        self.param2 = param2
        

    def output(self,param1,param2):
        print("output:",param1,param2)

    def cmd_init(self):
        self.parser.register("output", self.output, {"param1": 0, "param2": 1}, "output test")
        self.parser.register("message", self.message,{}, "output message")
        self.parser.register("wait", self.wait, {"time": 0}, "wait for time")
        self.parser.register("control", self.control, {}, "control")

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
