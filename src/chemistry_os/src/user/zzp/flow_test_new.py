import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_filter import Filter
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_bath import Bath
from facilities.facility_sdk import HN_SDK
from facilities.flowdisplay import Flowdisplay
from facilities.facility_system import System
from facilities.facility_server import TCPServer
from facility import Facility

if __name__ == '__main__':
    CompoundC_solid_add = 0.5 # 化合物C的添加量

    main_sys = System("os")
    add_Liquid=PumpGroup('add_Liquid')
    add_Solid=Add_Solid('add_Solid')
    fr5_C = Fr5Arm("fr5C","192.168.58.3")
    fr5_A = Fr5Arm("fr5A","192.168.58.2")
    bath = Bath('bath')
    filter = Filter("filter")
    hn_sdk=HN_SDK()

    main_server= TCPServer(test=True)
    main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.data_update)
    main_server.register("fr5A", 5, fr5_A.data_dict, fr5_A.data_dict_update)
    main_server.register("fr5C", 5, fr5_C.data_dict, fr5_C.data_dict_update)
    main_server.register("addsolid", 25, add_Solid.data_dict)
    main_server.start()

    # 机械臂初始化
    hn_sdk.HN_init()
    # 固体进料
    hn_sdk.add_solid(CompoundC_solid_add, 'test_tube_support', 'beaker_support')
    # 抓取三颈烧瓶
    hn_sdk.move_shaoping_A2C()
    # 液体进料
    hn_sdk.bath_open()
    hn_sdk.add_liquid_bath('HCl')
    hn_sdk.add_liquid_bath('KMnO4')
    hn_sdk.add_liquid_bath('H2O2')
    hn_sdk.bath_close()

    hn_sdk.bath_wash()

    hn_sdk.bath_open()
    hn_sdk.add_liquid_bath('N2H4')
    hn_sdk.bath_close()
    # 放置三颈烧瓶
    hn_sdk.move_shaoping_C2A()

