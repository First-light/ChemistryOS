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

# 宏定义
CompoundC_solid_add = 0.5 # 化合物C的添加量


@staticmethod
def main_thread_func():

    filter = Filter("filter")
    add_Liquid=PumpGroup('add_Liquid')
    add_Solid=Add_Solid('add_Solid')
    fr5_C = Fr5Arm("fr5C","192.168.58.3")
    fr5_A = Fr5Arm("fr5A","192.168.58.2")
    bath = Bath('bath')
    hn_sdk=HN_SDK()

    ProjectUtils.register_object("filter")
    ProjectUtils.register_object("add_Liquid")
    ProjectUtils.register_object("add_Solid")
    ProjectUtils.register_object("fr5C")
    ProjectUtils.register_object("fr5A")
    ProjectUtils.register_object('bath')
    ProjectUtils.register_object(hn_sdk.name)

    ProjectUtils.register_process(hn_sdk.name,"HN_init")
    ProjectUtils.register_sub_process("用户初始化")
    ProjectUtils.register_process(hn_sdk.name,"move_shaoping_A2C")
    ProjectUtils.register_process(hn_sdk.name,"bath_open")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['HCl'])
    ProjectUtils.register_sub_process("浓HCL的滴加")
    ProjectUtils.register_process(hn_sdk.name,"add_solid",[CompoundC_solid_add, 'test_tube_support', 'beaker_support'])
    ProjectUtils.register_sub_process("化合物C的称量和混合")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['HCl_wash'])
    ProjectUtils.register_sub_process("固液混合，反应过程")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['KMnO4'])
    ProjectUtils.register_sub_process("高锰酸钾的滴加")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['H2O2'])
    ProjectUtils.register_sub_process("双氧水的滴加")
    ProjectUtils.register_process(hn_sdk.name,"bath_over")
    ProjectUtils.register_process(hn_sdk.name,"bath_wash")
    ProjectUtils.register_sub_process("抽滤")
    ProjectUtils.register_process(hn_sdk.name,"bath_open")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['N2H4'])
    ProjectUtils.register_sub_process("滴加水合肼")
    ProjectUtils.register_process(hn_sdk.name,"bath_over")
    ProjectUtils.register_process(hn_sdk.name,"move_shaoping_C2A")
    ProjectUtils.register_sub_process("E产物转移")
    ProjectUtils.make()

    pro = Project(name="pro",file="flow_tcp.json") 

    main_parser = CommandParser()
    main_parser.parse("os check")
    main_parser.start()
    main_parser.start(input="unity")

    main_server = TCPServer(test=True)
    main_server.register("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.data_update)
    main_server.register("log", 10, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register("project_json", 200, pro.project_dict,enable=False)
    main_server.register("project_data_dict", 20, pro.data_dict,pro.data_dict_update)
    main_server.register("facility_location",200, System.facility_location_dict,enable=False)
    main_server.register("facility_state",10, System.facility_state_dict,System.facility_state_dict_update)
    main_server.register("fr5A_data", 5, fr5_A.data_dict, fr5_A.data_dict_update)
    main_server.register("fr5C_data", 5, fr5_C.data_dict, fr5_C.data_dict_update)
    # main_server.register("bath_data", 5, bath.data_dict, bath.data_dict_update)
    main_server.register("filter_data", 20, filter.data_dict, filter.data_dict_update)
    # main_server.register("add_Liquid_data", 5, add_Liquid.data_dict, add_Liquid.data_dict_update)
    # main_server.register("add_Solid_data", 5, add_Solid.data_dict, add_Solid.data_dict_update)
    # main_server.register("hn_sdk_data", 5, hn_sdk.data_dict, hn_sdk.data_dict_update)

    main_server.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main_sys = System("os")
    main_sys.main_thread_target = main_thread_func
    main_sys.start()
