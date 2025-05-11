import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_project import Project
from prettytable import PrettyTable
from facilities.facility_temp import FacilityTemp
from structs import FacilityState

class System(Facility):
    type = "system"

    def __init__(self,name:str = "os"):
        super().__init__(name, System.type)
        self.objects = []  # 用于存储创建的实例

    def cmd_init(self):
        self.parser.register("fr5arm", self.create_fr5robot, {"name":'', "ip":''}, "create fr5robot")
        self.parser.register("temp", self.create_temp, {"name":'', "param1":'', "param2":''}, "create temp")
        self.parser.register("project", self.create_project, {"name":'', "file":''}, "create project")
        self.parser.register("delete", self.destroy, {"name":''}, "delete object")
        self.parser.register("check", self.list,{}, "list all objects")
        self.parser.register("!", self.stop_all,{}, "list all objects")

    def stop_all(self):
        self.log.info("stop all objects:")
        for i, tuple_t in enumerate(Facility.tuple_list):
            name = tuple_t[0]
            type = tuple_t[1]
            state_data_p = tuple_t[3].state
            if name != self.name:
                state_data_p[0] = FacilityState.STOP
                self.log.info(f"object {name} stopped.")

    def list(self):
        self.log.info("check all objects:")
        table = PrettyTable()
        table.field_names = ["Index", "Object Name", "Object Type", "Object State"]

        for i, tuple_t in enumerate(Facility.tuple_list):
            name = tuple_t[0]
            type = tuple_t[1]
            state_data_p = tuple_t[3].state
            table.add_row([i+1, name, type,state_data_p[0]])

        print(table)

    def destroy(self, name: str):
        if name == '':
            self.log.info("failed to delete object:",name)
            return

        for i, tuple_t in enumerate(Facility.tuple_list):
            objectname = tuple_t[0]
            obj = tuple_t[2]
            if name == objectname:
                # 删除对象 robot
                del obj
                # 删除元组
                del Facility.tuple_list[i]
                self.log.info(f"object {name} destroyed successfully.")
                return
        self.log.info(f"No matching object found for name: {name}")
        

# 以下为创建实例的函数
        

    def create_temp(self,name:str,param1,param2):
        if name != '' or param1 != '' or param2 != '':
            self.log.info("create temp:",name,param1,param2)
            new_temp = FacilityTemp(name, param1, param2)
            self.objects.append(new_temp)
        else:
            self.log.info("failed to create temp:",name,param1,param2)

    def create_fr5robot(self,name:str,ip:str):
        if name != '' or ip != '':
            self.log.info("create fr5robot:",name,ip)
            new_robot = Fr5Arm(name, ip)
            self.objects.append(new_robot)
        else:
            self.log.info("failed to create fr5robot:",name,ip)

    def create_project(self,name:str,file:str):
        if name != '' or file != '':
            self.log.info("create project:",name,file)
            new_project = Project(name, file)
            self.objects.append(new_project)
        else:
            self.log.info("failed to create project:",name,file)
        

