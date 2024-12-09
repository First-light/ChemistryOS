import sys
sys.path.append('src/chemistry_os/src')
from facility import facility
from facilities.class_fr5arm import fr5robot
from prettytable import PrettyTable


class system(facility):

    def __init__(self,name:str = "os"):
        super().__init__(name)
        self.objects = []  # 用于存储创建的 fr5robot 实例

    def cmd_init(self):
        self.parser.register("create-fr5", self.create_fr5robot, {"name":'', "ip":''}, "create fr5robot")
        self.parser.register("delete", self.destroy, {"name":''}, "delete fr5robot")
        self.parser.register("list", self.list,{}, "list all facility")

    def list(self):
        print("list all facility:")
        table = PrettyTable()
        table.field_names = ["Index", "Object Name", "Robot"]

        for i, tuple_t in enumerate(facility.TupleList):
            objectname = tuple_t[0]
            obj = tuple_t[2]
            table.add_row([i+1, objectname, obj])

        print(table)

    def create_fr5robot(self,name:str,ip:str):
        if name != '' or ip != '':
            print("create fr5robot:",name,ip)
            new_robot = fr5robot(name, ip)
            self.objects.append(new_robot)
        else:
            print("failed to create fr5robot:",name,ip)
        

    def destroy(self, name: str):
        if name == '':
            print("failed to delete facility:",name)
            return

        for i, tuple_t in enumerate(facility.TupleList):
            objectname = tuple_t[0]
            obj = tuple_t[2]
            if name == objectname:
                # 删除对象 robot
                del obj
                # 删除元组
                del facility.TupleList[i]
                print(f"object {name} destroyed successfully.")
                return
        print(f"No matching object found for name: {name}")