import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
from facilities.facility_fr5arm import Fr5Arm
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
    fr3_C = Fr3Arm("fr3C","192.168.58.3")
    fr5_A = Fr5Arm("fr5A","192.168.58.2")
    bath = Bath('bath')
    hn_sdk=HN_SDK()
    # 机械臂初始化
    hn_sdk.HN_init()
    # 抓取三颈烧瓶
    hn_sdk.name_catch('sanjinshaoping')
    hn_sdk.bath_put('bath_fr5')

    # 固液进料
    hn_sdk.add_solid(CompoundC_solid_add, 'test_tube', 'add_solid_place')
    hn_sdk.add_liquid('HCl', HCl_rpm, HCL_volume_add)
    # 水浴
    hn_sdk.bath_open()
    hn_sdk.bath_writetmp(tmp_0)
    hn_sdk.add_liquid('KMnO4', KMnO4_rpm, KMnO4_volume_add)
    hn_sdk.bath_writetmp(tmp_25)
    hn_sdk.interactable_countdown(reaction_time_1)
    hn_sdk.bath_writetmp(tmp_0)
    hn_sdk.add_liquid('H2O2', H2O2_rpm, H2O2_volume_add)
    hn_sdk.interactable_countdown(reaction_time_2)

    hn_sdk.bath_writetmp(tmp_25)
    hn_sdk.add_liquid('CH3CN', CH3CN_rpm, CH3CN_volume_add)
    hn_sdk.add_liquid('N2H4', N2H4_rpm, N2H4_volume_add)
    hn_sdk.interactable_countdown(reaction_time_3)

    hn_sdk.bath_close()
    # 放置三颈烧瓶
    hn_sdk.bath_catch('bath_fr5')
    hn_sdk.name_put('sanjinshaoping')

