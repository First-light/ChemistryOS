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
from facilities.flowdisplay import Flowdisplay
from facility import Facility
from facilities.facility_server import TCPServer
from facilities.facility_filter import Filter
from facilities.facility_parser import CommandParser

CompoundC_solid_add = 0.5 # 化合物C的添加量

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

filter = Filter("filter", "/dev/ttyUSB0",sub_addresses = sub_addresses)
exit()
# print(filter)
hn_sdk=HN_SDK()

# main_server = TCPServer(test = True)

# main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
# main_server.register("flow", 50, flowdisplay.process_display_dict, flowdisplay.data_update)
# main_server.register("fr5A", 5, fr5_A.data_dict, fr5_A.data_dict_update_angles)
# main_server.register("fr5C", 5,fr5_C.data_dict, fr5_C.data_dict_update_angles)

# main_server.start()

hn_sdk.HN_init()
# 固体进料
hn_sdk.name_catch_and_put('beaker_support', 'beaker_add_place')
hn_sdk.name_catch('beaker_add_place')
hn_sdk.name_pour('solid_pour_place')
hn_sdk.name_put('beaker_support')
# # 抓取三颈烧瓶
# hn_sdk.move_shaoping_A2C()
# hn_sdk.bath_open()
# # 液体进料
# hn_sdk.add_liquid_bath('HCl')
# hn_sdk.bath_close()
# # 放置三颈烧瓶
# hn_sdk.move_shaoping_C2A()


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
