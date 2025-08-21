import time
import sys

sys.path.append('src/chemistry_os/src')
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

add_Solid=Add_Solid('add_Solid')
print(add_Solid.data_dict)
with add_Solid:
    pass
print(add_Solid.data_dict)
exit()
# with add_Solid:
#     # add_Solid.add_solid_series(0.5)
#     # add_Solid.tube_ver()
#     add_Solid.clip_open()
#     # add_Solid.clip_close()
#     # add_Solid.tube_hor()
#     # add_Solid.set_pid(1.2,1.75,2.1)


CompoundC_solid_add = 0.5 # 化合物C的添加量

main_sys = System("os") # 必须放最前
main_parser = CommandParser()  
main_parser.start(input="shell")


add_Liquid=PumpGroup('add_Liquid')
add_Liquid.add_liquid('HCl', 30, 180)
exit()


add_Liquid=PumpGroup('add_Liquid')
add_Solid=Add_Solid('add_Solid')
fr5_C = Fr5Arm("fr5C","192.168.58.3")
fr5_A = Fr5Arm("fr5A","192.168.58.2")
bath = Bath('bath')
filter = Filter("filter")

# main_server= TCPServer(test = True)
# main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
# main_server.register("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.data_update)
# main_server.register("fr5A", 5, fr5_A.data_dict, fr5_A.data_dict_update)
# main_server.register("fr5C", 5, fr5_C.data_dict, fr5_C.data_dict_update)
# main_server.register("addsolid", 25, add_Solid.data_dict)
# main_server.start()

hn_sdk=HN_SDK()
# event_countdown(10)
# exit()
hn_sdk.HN_init()
hn_sdk.add_liquid_bath('HCl')
# hn_sdk.add_solid(1.0, 'test_tube_support', 'beaker_support')
# hn_sdk.fr5A_init()
# fr5_C.check_place_move()
# hn_sdk.name_catch('beaker_add_place')
# # fr5_A.catch()
# hn_sdk.name_pour('bath_pour_place')
# hn_sdk.name_put('beaker_support')
# exit()
# hn_sdk.HN_init()
# hn_sdk.move_shaoping_support2C()
# hn_sdk.bath_catch('bath_fr5_catch')
# hn_sdk.move_wash('sanjinshaoping_wash_1', 3)
# hn_sdk.move_wash('sanjinshaoping_wash_2', 3)
# hn_sdk.bath_put('bath_fr5_put')
# hn_sdk.move_shaoping_C2support()

# hn_sdk.name_catch_and_put('beaker_support', 'beaker_add_place')
# hn_sdk.name_catch('beaker_add_place')
# hn_sdk.name_pour('bath_pour_place')
# hn_sdk.name_put('beaker_support')
# hn_sdk.add_liquid_bath('HCl')
# hn_sdk.name_catch('sanjinshaoping_support')
# hn_sdk.name_put('sanjinshaoping_support')


exit()


# hn_sdk.HN_init()
# main_parser = CommandParser()
# main_parser.start()


# 保持主线程运行
# try:
    
#     while True:
#         time.sleep(0.1)
# except KeyboardInterrupt:
#     main_parser.end()
