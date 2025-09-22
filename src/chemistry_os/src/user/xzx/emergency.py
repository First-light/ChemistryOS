import sys


sys.path.append('src/chemistry_os/src')
from facilities.flowdisplay import Flowdisplay
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 
from facilities.facility_filter import Filter
from facilities.facility_server import TCPServer
from facilities.facility_project import Project
from facilities.facility_bath import Bath
from facilities.facility_sdk import HN_SDK
from facilities.facility_fr5arm import Fr5Arm
from facility import Facility
from utilities.utility_project import ProjectUtils
import time


@staticmethod
def main_thread_func():

    filter = Filter("filter")
    add_Liquid=PumpGroup('add_Liquid')
    add_Solid=Add_Solid('add_Solid')
    fr5_C = Fr5Arm("fr5C","192.168.58.3")
    fr5_A = Fr5Arm("fr5A","192.168.58.2")
    bath = Bath('bath')
    hn_sdk=HN_SDK()
    
    pro = Project(name="pro",file="fr5.json") 
   
    main_server = TCPServer(test=True)
    main_server.register_pkg("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.data_update)
    main_server.register_pkg("log", 10, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register_pkg("project_json", 200, pro.project_dict,enable=False)
    main_server.register_pkg("project_data_dict", 20, pro.data_dict,pro.data_dict_update)
    main_server.register_pkg("facility_location",200, System.facility_location_dict,enable=False)
    main_server.register_pkg("facility_state",10, System.facility_state_dict,System.facility_state_dict_update)
    main_server.register_pkg("fr5A_data", 5, fr5_A.data_dict, fr5_A.data_dict_update)
    main_server.register_pkg("fr5C_data", 5, fr5_C.data_dict, fr5_C.data_dict_update)
    # main_server.register("bath_data", 5, bath.data_dict, bath.data_dict_update)
    main_server.register_pkg("filter_data", 20, filter.data_dict, filter.data_dict_update)
    # main_server.register("add_Liquid_data", 5, add_Liquid.data_dict, add_Liquid.data_dict_update)
    # main_server.register("add_Solid_data", 5, add_Solid.data_dict, add_Solid.data_dict_update)
    # main_server.register("hn_sdk_data", 5, hn_sdk.data_dict, hn_sdk.data_dict_update)
    main_server.start()


    main_parser = CommandParser()
    main_parser.parse("os check")
    main_parser.start()
    main_parser.start(input="unity")

    # input("ok?")
    # fr5_A.Go_to_start_zone_0()

    # bath.power_ctr(1)
    # bath.mix_ctr(1)
    # bath.circle_ctr(1)# 允许circle
    # bath.hot_ctr(1)# 加热
    # bath.cold_ctr(1)# 允许制冷

    # filter.pump_control_name("acid",1)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("主线程退出")

if __name__ == '__main__':
    main_sys = System("os")
    main_sys.main_thread_target = main_thread_func
    main_sys.start()