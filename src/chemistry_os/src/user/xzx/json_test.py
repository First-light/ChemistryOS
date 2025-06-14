import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_bath import Bath
from facilities.facility_sdk import HN_SDK
from facilities.facility_system import System
from parser import CommandParser
from server import TCPServer
import time

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
    fr5_C = Fr3Arm("fr3C","192.168.58.3")
    fr5_A = Fr5Arm("fr5A","192.168.58.2")
    bath = Bath('bath')
    hn_sdk=HN_SDK()
    # 机械臂初始化
    hn_sdk.HN_init()
    # 抓取三颈烧瓶

    main_sys = System("os")

    main_server = TCPServer()
    main_server.register("example_unit", 5,fr5_A.data_dict)
    main_server.start()

    main_parser = CommandParser()
    main_parser.parse("os project name=pro file=json_test.json")
    main_parser.parse("os check")
    # main_parser.parse("pro run")
    main_parser.start()


    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()


