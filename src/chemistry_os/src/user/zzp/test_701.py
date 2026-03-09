import threading
import time
import sys

sys.path.append('src/chemistry_os/src')
from facilities.facility_thermometer import Thermometer
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

# CompoundC_solid_add = 0.5 # 化合物C的添加量

main_sys = System("os") # 必须放最前
main_parser = CommandParser()
main_parser.start(input="shell")
add_Liquid=PumpGroup('add_Liquid')
# add_Liquid.add_liquid('CH3CH', 150, 3)
# exit()
add_Solid=Add_Solid('add_Solid')

# with add_Solid:
#     # add_Solid.set_pid(1.2, 1.75, 2.25)
#     add_Solid.clip_close()
#     add_Solid.add_solid_series(0.5)
#     # print(add_Solid.data_dict['weight_now'])
#     add_Solid.tube_ver()
#     add_Solid.clip_open()
#     # add_Solid.clip_close()
#     # add_Solid.tube_hor()
#     # add_Solid.tube_ver()
# exit()

fr5_C = Fr5Arm("fr5C","192.168.58.3")
fr5_A = Fr5Arm("fr5A","192.168.58.2")
bath = Bath('bath')
filter = Filter("filter")
thermometer = Thermometer("thermometer")

# main_server= TCPServer(test = True)
# main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
# main_server.register("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.data_update)
# main_server.register("fr5A", 5, fr5_A.data_dict, fr5_A.data_dict_update)
# main_server.register("fr5C", 5, fr5_C.data_dict, fr5_C.data_dict_update)
# main_server.register("addsolid", 25, add_Solid.data_dict)
# main_server.start()

hn_sdk=HN_SDK()
# exit()
hn_sdk.HN_init()
# fr5_C.move_to_safe_catch(4)
# fr5_C.move_by(0,0,0,0,-40.0,0)
# fr5_C.move_by(0,0,0,0,-5.0,0)

hn_sdk.move_shaoping_support2C()
hn_sdk.fr5_C_pour()
# hn_sdk.temp_on()
# hn_sdk.temp_off()
hn_sdk.move_shaoping_C2support()

# hn_sdk.add_liquid('H2O2', 100, 30, wash=True)
# exit()