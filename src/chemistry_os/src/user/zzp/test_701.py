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
fr3_C.fr3_init()
# fr5_A = Fr5Arm("fr5A","192.168.58.2")
# fr5_A.fr5_init()
# fr5_A.move_to_safe_catch(3)
# bath = Bath('bath')
# hn_sdk=HN_SDK()

# hn_sdk.fr5_init()
# hn_sdk.add_solid(0, 'test_tube', 'beaker')

# add_Liquid.add_liquid('H2O2',150 ,10)
hn_sdk.fr5_init()
hn_sdk.fr3_init()

hn_sdk.name_catch('beaker')
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



