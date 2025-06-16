import time
import sys

sys.path.append('src/chemistry_os/src')
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
import logging
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_sdk import HN_SDK
from facilities.facility_bath import Bath

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

# controller = Add_Solid()
# controller.initialize_serial()
# # controller.turn_on()
# # controller.clip_close()
# controller.clip_open()
# # controller.add_solid_series(0.5)
# # controller.turn_off()
# controller.release_serial()
# exit(0)


add_Liquid=PumpGroup('add_Liquid')
add_Solid=Add_Solid('add_Solid')
fr3_C = Fr3Arm("fr3C","192.168.58.3")
fr5_A = Fr5Arm("fr5A","192.168.58.2")
bath = Bath('bath')
hn_sdk=HN_SDK()

# hn_sdk.bath_close()
add_Solid.initialize_serial()
# add_Solid.clip_open()
# time.sleep(1)
# print(add_Solid.ser.read_all())
for _ in range(10):
    print(add_Solid._read_raw_frame())

print(add_Solid._read_needed_frame())
add_Solid.release_serial()

# add_Solid.initialize_serial()
# add_Solid.clip_close()
# add_Solid.release_serial()

add_Solid.initialize_serial()
# # add_Solid.turn_on()
# # add_Solid.add_solid_series(0.5)
add_Solid.turn_off()
add_Solid.release_serial()

# add_Solid.initialize_serial()
# add_Solid.clip_open()
# add_Solid.release_serial()

# add_Liquid.add_liquid('HCl', 150, HCL_volume_add)

# hn_sdk.bath_open()
# hn_sdk.bath_writetmp(tmp_0)

# add_Liquid.add_liquid("KMnO4", 150, KMnO4_volume_add)

hn_sdk.bath_writetmp(tmp_25)
hn_sdk.bath_close()

# hn_sdk.fr3_check_place()
# hn_sdk.fr5_init()

# hn_sdk.name_catch('sanjinshaoping')
# hn_sdk.bath_put('bath_fr5')
# hn_sdk.name_catch('sanjinshaoping')
# hn_sdk.bath_put('bath_fr5')
# hn_sdk.name_catch_and_put('beaker', 'beaker_add_space')
# fr3_C.move_to_safe_catch(2)
# hn_sdk.name_catch('beaker')
# hn_sdk.name_pour('solid_pour_place')
# hn_sdk.bath_catch('bath_fr5')
# hn_sdk.name_put('sanjinshaoping')

# hn_sdk.add_liquid('HCl', HCl_rpm, HCL_volume_add)

# hn_sdk.fr3_init()
# hn_sdk.fr5_init()

# hn_sdk.name_pour('solid_pour_place')

# hn_sdk.add_solid(0, 'test_tube', 'beaker')

# add_Liquid.add_liquid('H2O2',150 ,10)
# hn_sdk.fr5_init()
# hn_sdk.fr3_init()

# hn_sdk.name_catch('beaker')
# hn_sdk.name_catch('test_tube')
# hn_sdk.name_put('test_tube_add_place', test_tube_add=True)
# fr3_C.move_to_catch()

# hn_sdk.name_catch_and_put('beaker', 'add_solid_place')
# hn_sdk.add_Solid.initialize_serial()
# hn_sdk.add_Solid.turn_on()
# hn_sdk.add_Solid.add_solid_series(0.5)
# hn_sdk.add_Solid.turn_off()
# hn_sdk.add_Solid.release_serial()
# hn_sdk.name_catch('test_tube_add_place', test_tube_add=True)
# hn_sdk.name_put('test_tube')

# hn_sdk.name_catch('test_tube')
# hn_sdk.name_put('test_tube')

# hn_sdk.name_catch('sanjinshaoping')
# hn_sdk.bath_put('bath_fr5')
# hn_sdk.fr3_move_to_bath()
# hn_sdk.fr3_move_to_catch()
# hn_sdk.bath_catch('bath_fr5')
# hn_sdk.name_put('sanjinshaoping')



