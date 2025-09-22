import sys


sys.path.append('src/chemistry_os/src')
from facilities.facility_thermometer import Thermometer
from utilities.utility_param import ParamTuple, ParamUtils
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
ParamTuple.CompoundC_solid_add = 1 # 化合物C的添加量
ParamTuple.HCl_volume_add = 26.8*ParamTuple.CompoundC_solid_add # 浓盐酸
ParamTuple.KMnO4_volume_add = 53.52*ParamTuple.CompoundC_solid_add # 高锰酸钾添加量 
ParamTuple.H2O2_volume_add = 20.0*ParamTuple.CompoundC_solid_add # 双氧水添加量
ParamTuple.N2H4_volume_add = 1.14*ParamTuple.CompoundC_solid_add # 肼添加量

ParamTuple.CH3CN_volume_add = 22.73*ParamTuple.CompoundC_solid_add  # 乙腈添加量
ParamTuple.HCl_volume_wash = 20.0*ParamTuple.CompoundC_solid_add
ParamTuple.water_volume_wash = 20.0*ParamTuple.CompoundC_solid_add

ParamTuple.liquid_volume_pump = 200 # ml
ParamTuple.liquid_2_volume_pump = ParamTuple.HCl_volume_wash + ParamTuple.water_volume_wash 

ParamTuple.HCl_temp = 0
ParamTuple.KMnO4_temp = 25
ParamTuple.H2O2_temp = 0
ParamTuple.N2H4_temp = 25

ParamTuple.reaction_time_1 = 7200
ParamTuple.reaction_time_2 = 1200
ParamTuple.reaction_time_3 = 14400
ParamTuple.project_name  = "flow_project"
ParamTuple.init_name = "flow_init"

main_sys = System("os")
main_parser = CommandParser()
main_server = TCPServer(test=True)
filter = Filter("filter")
add_Liquid=PumpGroup('add_Liquid')
add_Solid=Add_Solid('add_Solid')
fr5_C = Fr5Arm("fr5C","192.168.58.3")
fr5_A = Fr5Arm("fr5A","192.168.58.2")
bath = Bath('bath')
thermometer = Thermometer("thermometer")
hn_sdk=HN_SDK()

def reset_make_func():
    pass
    # # 仅用于故障重启
    # ProjectUtils.register_object("filter")
    # ProjectUtils.register_object("add_Liquid")
    # ProjectUtils.register_object("add_Solid")
    # ProjectUtils.register_object("fr5C")
    # ProjectUtils.register_object("fr5A")
    # ProjectUtils.register_object('bath')
    # # ProjectUtils.register_object('thermometer')
    # ProjectUtils.register_object(hn_sdk.name)

    # ProjectUtils.register_process(hn_sdk.name,"add_liquid_init")
    # ProjectUtils.register_process(hn_sdk.name,"add_solid_init")

# json项目
def project_make_func():
    # 在这里实现您的自定义逻辑
    ProjectUtils.register_object("filter")
    ProjectUtils.register_object("add_Liquid")
    ProjectUtils.register_object("add_Solid")
    ProjectUtils.register_object("fr5C")
    ProjectUtils.register_object("fr5A")
    ProjectUtils.register_object('bath')
    ProjectUtils.register_object('thermometer')
    ProjectUtils.register_object(hn_sdk.name)

    ProjectUtils.register_process(main_server.name,"open_log")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_config_init")
    ProjectUtils.register_process(hn_sdk.name,"temp_start")
    ProjectUtils.register_process(hn_sdk.name,"HN_init")
    ProjectUtils.register_process(hn_sdk.name,"move_shaoping_A2C")
    ProjectUtils.register_process(hn_sdk.name,"bath_open")
    ProjectUtils.register_sub_process("实验开始")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['HCl'])
    ProjectUtils.register_sub_process("浓盐酸滴加1")
    ProjectUtils.register_process(hn_sdk.name,"add_solid",[ParamTuple.CompoundC_solid_add, 'test_tube_support', 'beaker_support'])
    ProjectUtils.register_sub_process("化合物C称量和混合")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['HCl_wash'])
    ProjectUtils.register_sub_process("浓盐酸滴加2")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['KMnO4'])
    ProjectUtils.register_sub_process("高锰酸钾的滴加")
    ProjectUtils.register_process(hn_sdk.name,"interactable_countdown",[ParamTuple.reaction_time_1])
    ProjectUtils.register_sub_process("持续反应过程1")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['H2O2'])
    ProjectUtils.register_sub_process("双氧水滴加")
    ProjectUtils.register_process(hn_sdk.name,"interactable_countdown",[ParamTuple.reaction_time_2])
    ProjectUtils.register_sub_process("持续反应过程2")
    ProjectUtils.register_process(hn_sdk.name,"bath_over")
    ProjectUtils.register_process(hn_sdk.name,"bath_update")
    ProjectUtils.register_process(hn_sdk.name,"bath_catch",['bath_fr5_catch'])
    # ProjectUtils.register_process(hn_sdk.name,"move_wash",['sanjinshaoping_wash_1', 0])
    ProjectUtils.register_process(hn_sdk.name,"move_wash",['sanjinshaoping_wash_2', 1])
    ProjectUtils.register_process(hn_sdk.name,"move_wash",['sanjinshaoping_wash_3', 2])
    # ProjectUtils.register_process(hn_sdk.name,"move_wash",['sanjinshaoping_wash_1', 3])
    ProjectUtils.register_process(hn_sdk.name,"bath_put",['bath_fr5_put'])
    ProjectUtils.register_sub_process("中间产物抽滤和乙腈滴加")
    ProjectUtils.register_process(hn_sdk.name,"bath_open")
    ProjectUtils.register_process(hn_sdk.name,"add_liquid_bath",['N2H4'])
    ProjectUtils.register_sub_process("水合肼滴加")
    ProjectUtils.register_process(hn_sdk.name,"interactable_countdown",[ParamTuple.reaction_time_3])
    ProjectUtils.register_sub_process("持续反应过程3")
    ProjectUtils.register_process(hn_sdk.name,"bath_over")
    ProjectUtils.register_process(hn_sdk.name,"fr5_C_pour")
    ProjectUtils.register_process(hn_sdk.name,"move_shaoping_C2A")
    ProjectUtils.register_process(hn_sdk.name,"temp_over")
    ProjectUtils.register_process(main_server.name,"close_log")
    ProjectUtils.register_sub_process("实验结束")
    # 添加您需要的功能
    pass


def main_thread_func():
    # ProjectUtils.register_function(ParamTuple.init_name, reset_make_func)
    ProjectUtils.register_function(ParamTuple.project_name, project_make_func)
    # System.redefine_and_make(ParamTuple.init_name)
    System.redefine_and_make(ParamTuple.project_name)

    pro = Project(name="pro",file=ParamTuple.project_name + ".json") 
    # pro_reset = Project(name="pro_reset",file=ParamTuple.init_name + ".json") 
    
    main_parser.parse("os check")
    main_parser.start()
    main_parser.start(input="unity")

    main_server.register_pkg("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.data_update)
    main_server.register_pkg("log", 10, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register_pkg("project_json", 200, pro.project_dict,enable=False)
    main_server.register_pkg("project_data_dict", 20, pro.data_dict,pro.data_dict_update)
    # main_server.register("reset_data_dict", 20, pro_reset.data_dict,pro_reset.data_dict_update)
    main_server.register_pkg("facility_location",200, System.facility_location_dict,enable=False)
    main_server.register_pkg("facility_state",10, System.facility_state_dict,System.facility_state_dict_update)
    main_server.register_pkg("fr5A_data", 5, fr5_A.data_dict, fr5_A.data_dict_update)
    main_server.register_pkg("fr5C_data", 5, fr5_C.data_dict, fr5_C.data_dict_update)
    main_server.register_pkg("bath_data", 20, bath.data_dict)
    main_server.register_pkg("filter_data", 20, filter.data_dict, filter.data_dict_update)
    main_server.register_pkg("add_Liquid_data", 20, add_Liquid.data_dict)
    main_server.register_pkg("add_Solid_data", 20, add_Solid.data_dict)
    main_server.register_pkg("params", 50, ParamUtils.param_dict,ParamUtils.param_dict_update)
    main_server.register_pkg("liquid_config",100, hn_sdk.liquid_config)
    main_server.register_pkg("thermometer_config",500, thermometer.data_dict)
    main_server.start()

    # main_parser.parse("pro run") # 运行流程

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main_sys.main_thread_target = main_thread_func
    main_sys.start()

