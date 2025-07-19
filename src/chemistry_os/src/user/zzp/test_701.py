import time
import sys

sys.path.append('src/chemistry_os/src')
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
import logging
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_sdk import HN_SDK
from facilities.facility_bath import Bath
from facilities.facility_flowdisplay import Flowdisplay
from facility import Facility
from server import TCPServer
from facilities.facility_filter import Filter
from parser import CommandParser

CompoundC_solid_add = 0.5 # 化合物C的添加量
HCL_volume_add = 26.8*CompoundC_solid_add # 浓盐酸
KMnO4_volume_add = 53.52*CompoundC_solid_add # 高锰酸钾添加量 
H2O2_volume_add = 20.0*CompoundC_solid_add # 双氧水添加量
HCL_L_volume_add = 80.0*CompoundC_solid_add
CH3CN_volume_add = 20.0 # 乙腈添加量
N2H4_volume_add = 0.4854 # 肼添加量
HCl_rpm = 100
KMnO4_rpm = 15
H2O2_rpm = 30
CH3CN_rpm = 30
N2H4_rpm = 30
tmp_0 = 0
tmp_25 = 25
reaction_time_1 = 7200
reaction_time_2 = 1200
reaction_time_3 = 14400

# controller = Add_Solid()
# with controller:
#     controller.tube_ver()
#     controller.clip_open()

# exit()


flowdisplay = Flowdisplay("flowdisplay")
add_Liquid=PumpGroup('add_Liquid')
add_Solid=Add_Solid('add_Solid')
fr5_C = Fr5Arm("fr5C","192.168.58.3")
fr5_A = Fr5Arm("fr5A","192.168.58.2")
bath = Bath('bath')
sub_addresses={               # 下级设备地址字典
    "empty": 0x00,           # 空地址
    "solvent": 0x03,          # 溶解溶剂地址
    "water": 0x02,            # 清水清洗液地址
    "acid": 0x04,              # 酸清洗液地址
    "pump": 0x01                # 抽滤地址
}

filter = Filter("filter", "/dev/ttyUSB1",sub_addresses = sub_addresses)
# print(filter)
hn_sdk=HN_SDK()

main_server = TCPServer(test = True)

main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
main_server.register("flow", 50, flowdisplay.process_display_dict, flowdisplay.data_update)
main_server.register("fr5A", 5, fr5_A.data_dict, fr5_A.data_dict_update_angles)
main_server.register("fr5C", 5,fr5_C.data_dict, fr5_C.data_dict_update_angles)

main_server.start()

hn_sdk.HN_init()
# 固体进料
hn_sdk.add_solid(CompoundC_solid_add, 'test_tube_support', 'beaker_support')
# 抓取三颈烧瓶
hn_sdk.move_shaoping_A2C()
hn_sdk.bath_open()
# 液体进料
hn_sdk.add_liquid_bath('HCl')
hn_sdk.bath_close()
# 放置三颈烧瓶
hn_sdk.move_shaoping_C2A()


# hn_sdk.HN_init()
# main_parser = CommandParser()
# main_parser.start()


# hn_sdk.move_shaoping_A2C()
# hn_sdk.bath_catch('bath_fr5_catch')
# # hn_sdk.name_catch('sanjinshaoping_support')
# hn_sdk.move_wash('sanjinshaoping_wash_1',0)
# hn_sdk.move_wash('sanjinshaoping_wash_2',1)
# hn_sdk.move_wash('sanjinshaoping_wash_1',2)
# hn_sdk.bath_put('bath_fr5_put')
# # hn_sdk.name_put('sanjinshaoping_support')
# hn_sdk.move_shaoping_C2A()


# # 保持主线程运行
# try:
    
#     while True:
#         time.sleep(0.1)
# except KeyboardInterrupt:
#     main_parser.end()
