import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_project import Project
from prettytable import PrettyTable
from facility import FacilityTemp

class System(Facility):

    def __init__(self,name:str = "os"):
        super().__init__(name)
        self.objects = []  # 用于存储创建的实例

    def cmd_init(self):
        self.parser.register("fr5arm", self.create_fr5robot, {"name":'', "ip":''}, "create fr5robot")
        self.parser.register("temp", self.create_temp, {"name":'', "param1":'', "param2":''}, "create temp")
        self.parser.register("project", self.create_project, {"name":'', "file":''}, "create project")
        self.parser.register("delete", self.destroy, {"name":''}, "delete object")
        self.parser.register("check", self.list,{}, "list all objects")

    def list(self):
        self.cmd_print("check all objects:")
        table = PrettyTable()
        table.field_names = ["Index", "Object Name", "Robot"]

        for i, tuple_t in enumerate(Facility.tupleList):
            objectname = tuple_t[0]
            obj = tuple_t[2]
            table.add_row([i+1, objectname, obj])

        print(table)

    def destroy(self, name: str):
        if name == '':
            self.cmd_print_head
            print("failed to delete object:",name)
            return

        for i, tuple_t in enumerate(Facility.tupleList):
            objectname = tuple_t[0]
            obj = tuple_t[2]
            if name == objectname:
                # 删除对象 robot
                del obj
                # 删除元组
                del Facility.tupleList[i]
                self.cmd_print_head
                print(f"object {name} destroyed successfully.")
                return
        self.cmd_print_head
        print(f"No matching object found for name: {name}")


# 以下为创建实例的函数
        

    def create_temp(self,name:str,param1,param2):
        if name != '' or param1 != '' or param2 != '':
            self.cmd_print_head
            print("create temp:",name,param1,param2)
            new_temp = FacilityTemp(name, param1, param2)
            self.objects.append(new_temp)
        else:
            self.cmd_print_head
            print("failed to create temp:",name,param1,param2)

    def create_fr5robot(self,name:str,ip:str):
        if name != '' or ip != '':
            self.cmd_print_head
            print("create fr5robot:",name,ip)
            new_robot = Fr5Arm(name, ip)
            self.objects.append(new_robot)
        else:
            self.cmd_print_head
            print("failed to create fr5robot:",name,ip)

    def create_project(self,name:str,file:str):
        if name != '' or file != '':
            self.cmd_print_head
            print("create project:",name,file)
            new_project = Project(name, file)
            self.objects.append(new_project)
        else:
            self.cmd_print_head
            print("failed to create project:",name,file)
        

