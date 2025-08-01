
import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
from facilities.facility_server import TCPServer
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_filter import Filter
import time
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
from facilities.facility_bath import Bath
from facilities.facility_sdk import HN_SDK


if __name__ == '__main__':
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

    add_Liquid=PumpGroup('add_Liquid')
    add_Solid=Add_Solid('add_Solid')
    fr5_C = Fr5Arm("fr5C","192.168.58.3")
    fr5_A = Fr5Arm("fr5A","192.168.58.2")
    bath = Bath('bath')
    filter = Filter("filter")
    
    main_sys = System("os")

    hn_sdk=HN_SDK()
    hn_sdk.HN_init()

    main_server = TCPServer(test=True)
    
    main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
    # main_server.register("facility_location",200, System.facility_location)
    

    main_server.start()

    main_parser = CommandParser()
    main_parser.start()
    # 机械臂初始化
    
    hn_sdk.fr5A_init()
    # hn_sdk.pot_wash()
    hn_sdk.name_catch("sanjinshaoping_support")
    hn_sdk.move_wash('sanjinshaoping_wash_1', 2)
    hn_sdk.name_put("sanjinshaoping_support")


        # 保持主线程运行
    try:
        
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()