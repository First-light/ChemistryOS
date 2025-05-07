import sys
sys.path.append('src/chemistry_os/src')
from facilities.sdk import HN_SDK
from simple_client import TCPClient

if __name__ == '__main__':
    CompoundC_solid_add = 0.5 # 化合物C的添加量
    HCL_volume_add = 26.8*CompoundC_solid_add # 浓盐酸
    KMnO4_volume_add = 53.52*CompoundC_solid_add # 高锰酸钾添加量 
    H2O2_volume_add = 20.0*CompoundC_solid_add # 双氧水添加量
    HCL_L_volume_add = 80.0*CompoundC_solid_add
    CH3CN_volume_add = 20.0 # 乙腈添加量
    N2H4_volume_add = 0.4854 # 肼添加量
    exit()
    hn_sdk=HN_SDK()
    # 机械臂初始化
    hn_sdk.HN_init()
    # 抓取三颈烧瓶
    hn_sdk.name_catch('sanjinshaoping')
    hn_sdk.bath_put('bath_fr5')
    # 固液进料
    hn_sdk.add_solid('beaker', CompoundC_solid_add)
    hn_sdk.add_liquid('HCl', 100, HCL_volume_add)
    # 水浴
    hn_sdk.bath_init()
    hn_sdk.bath_writetmp(0)
    hn_sdk.add_liquid('KMnO4', 15, KMnO4_volume_add)
    hn_sdk.bath_writetmp(25)
    hn_sdk.interactable_countdown(7200)
    hn_sdk.bath_writetmp(0)
    hn_sdk.add_liquid('H2O2', 30, KMnO4_volume_add)
    hn_sdk.interactable_countdown(1200)

    hn_sdk.bath_writetmp(25)
    hn_sdk.add_liquid('CH3CN', 30, CH3CN_volume_add)
    hn_sdk.add_liquid('N2H4', 30, N2H4_volume_add)
    hn_sdk.interactable_countdown(14400)

    hn_sdk.bath_close()
    # 放置三颈烧瓶
    hn_sdk.bath_catch('bath_fr5')
    hn_sdk.name_put('sanjinshaoping')

