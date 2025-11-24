import time
import sys

sys.path.append('src/chemistry_os/src')
from facilities.facility_thermometer import Thermometer
from utilities.events import event_countdown
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
import logging
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_sdk import HN_SDK
from facilities.facility_bath import Bath
from facilities.flowdisplay import Flowdisplay
from facility import Facility
from facilities.facility_server import TCPServer
from facilities.facility_filter import Filter
from facilities.facility_parser import CommandParser
from facilities.facility_system import System

main_sys = System("os")  # 必须放最前
main_parser = CommandParser()
main_parser.start(input="shell")

# add_Liquid = PumpGroup('add_Liquid')
# add_Solid = Add_Solid()
fr5_C = Fr5Arm("fr5C", "192.168.58.3")
fr5_A = Fr5Arm("fr5A", "192.168.58.2")
# bath = Bath('bath')
# filter = Filter("filter")
# thermometer = Thermometer("thermometer")

# main_server= TCPServer(test = True)
# main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
# main_server.register("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.data_update)
# main_server.register("fr5A", 5, fr5_A.data_dict, fr5_A.data_dict_update)
# main_server.register("fr5C", 5, fr5_C.data_dict, fr5_C.data_dict_update)
# main_server.register("addsolid", 25, add_Solid.data_dict)
# main_server.start()

# hn_sdk = HN_SDK()
# hn_sdk.HN_init()

# 假设这是你从 fr5_A.get_pose('tool') 获取的数据
pose = fr5_C.get_pose('tool')  # 示例：[123.456, -78.912, 34.567, 190.0, -200.0, 720.5]

# 四舍五入到小数点后一位
rounded_pose = [round(x, 1) for x in pose]

# 定义角度归一化函数到 (-180, 180]
def normalize_angle(angle):
    while angle <= -180.0:
        angle += 360.0
    while angle > 180.0:
        angle -= 360.0
    return round(angle, 1)  # 再次确保保留一位小数

# 处理后三个姿态角
for i in range(3, 6):
    rounded_pose[i] = normalize_angle(rounded_pose[i])

# 输出最终结果
print(rounded_pose)
input("Press Enter to exit...")
fr5_C.move_to_desc([200.0, -300.0, 250, 90.0, -45.0, 0.0])
exit(0)

add_solid_catch = [-619.0, -318.0, 150.0, 90.0, -0.0, -90.0]
beaker_A = [-506, -118, 106, 90, 0, -90]
beaker_B = [-506, 31, 106, 90, 0, -90]
add_liquid = [-221.1, -422.3, 71.9, 90.0, -0.0, -45.0]
tube_A = [-47.0, -533.0, 150.0, 90.0, -0.0, -0.0]
tube_B = [15.1, -533.0, 150.0, 90.0, -0.0, -0.0]
tube_2_add_solid = [-666.0, -453.9, 284.7, 90.0, -0.0, -45.0]
safe_pos_tube = [-25.0, -320.0, 335.0, 90.0, 0.0, 0.0]
safe_pos_beaker = [-320.0, 25.0, 335.0, 90.0, -0.0, -90.0]
safe_pos_react = [-220.1, 125.0, 335.0, 90.0, -0.0, 180.0]

safe_pos_mix = [400.0, -100.0, 200.0, 90.0, 0.0, -0.0]
beaker_mix = [318.0, -255.0, 100.0, 90.0, -0.0, 0.0]
beaker_pour = [-250.0, 235.0, 305.0, 90.0, -45.0, -90.0]