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

    def __init__(self, name: str = "os"):
        super().__init__(name, System.type)
        self.objects = []  # 用于存储创建的实例

    def cmd_init(self):
        self.parser.register("fr5arm", self.create_fr5robot, {"name": '', "ip": ''}, "创建 FR5 机械臂")
        self.parser.register("temp", self.create_temp, {"name": '', "param1": '', "param2": ''}, "创建温控设备")
        self.parser.register("project", self.create_project, {"name": '', "file": ''}, "创建项目")
        self.parser.register("delete", self.destroy, {"name": ''}, "删除对象")
        self.parser.register("check", self.list, {}, "列出所有对象")
        self.parser.register("!", self.stop_all, {}, "停止所有对象")

    def stop_all(self):
        self.log.info("停止所有对象:")
        for i, tuple_t in enumerate(Facility.tuple_list):
            name = tuple_t[0]
            type = tuple_t[1]
            state_data_p = tuple_t[3].state
            if name != self.name:
                state_data_p[0] = FacilityState.STOP
                self.log.info(f"对象 {name} 已停止。")

    def list(self):
        self.log.info("检查所有对象:")
        table = PrettyTable()
        table.field_names = ["序号", "对象名称", "对象类型", "对象状态"]

        for i, tuple_t in enumerate(Facility.tuple_list):
            name = tuple_t[0]
            type = tuple_t[1]
            state_data_p = tuple_t[3].state
            table.add_row([i + 1, name, type, state_data_p[0]])

        print(table)

    def destroy(self, name: str):
        if name == '':
            self.log.info("删除对象失败: 未提供名称")
            return

        for i, tuple_t in enumerate(Facility.tuple_list):
            objectname = tuple_t[0]
            obj = tuple_t[2]
            if name == objectname:
                # 删除对象
                del obj
                # 删除元组
                del Facility.tuple_list[i]
                self.log.info(f"对象 {name} 已成功删除。")
                return
        self.log.info(f"未找到名称为 {name} 的对象。")

    # 以下为创建实例的函数

    def create_temp(self, name: str, param1, param2):
        if name != '' or param1 != '' or param2 != '':
            self.log.info(f"创建温控设备: 名称={name}, 参数1={param1}, 参数2={param2}")
            new_temp = FacilityTemp(name, param1, param2)
            self.objects.append(new_temp)
        else:
            self.log.info(f"创建温控设备失败: 名称={name}, 参数1={param1}, 参数2={param2}")

    def create_fr5robot(self, name: str, ip: str):
        if name != '' or ip != '':
            self.log.info(f"创建 FR5 机械臂: 名称={name}, IP={ip}")
            new_robot = Fr5Arm(name, ip)
            self.objects.append(new_robot)
        else:
            self.log.info(f"创建 FR5 机械臂失败: 名称={name}, IP={ip}")

    def create_project(self, name: str, file: str):
        if name != '' or file != '':
            self.log.info(f"创建项目: 名称={name}, 文件={file}")
            new_project = Project(name, file)
            self.objects.append(new_project)
        else:
            self.log.info(f"创建项目失败: 名称={name}, 文件={file}")
