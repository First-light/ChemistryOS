import time
import sys

sys.path.append('src/chemistry_os/src')
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_addLiquid import Add_Liquid
from facilities.facility_addSolid import Add_Solid
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_sdk import HN_SDK

# fr5_C = Fr5Arm("fr5C","192.168.60.2")
# time.sleep(3)
# fr5_C.catcher('open')
# exit()

# fr5_C = Fr5Arm("fr5C","192.168.60.2")
# fr5_C.catcher('open')
# exit()
# fr5_C.move_to_desc([330.0,-195.0,380.0,90.0,-45.0,90.0],vel=10)
# input('catch?')
# fr5_C.catcher('close')
# input('ok?')
# fr5_C.move_to_desc([330.0,-195.0,200.0,90.0,-45.0,90.0],vel=10)

# hn_sdk=HN_SDK()
# hn_sdk.add_Solid.turn_on()
# time.sleep(1)
# hn_sdk.add_Solid.tube_hor()
# exit()



fr5_C = Fr3Arm("fr3A","192.168.58.3")
fr5_C.put()
exit()
fr5_A = Fr5Arm("fr5A","192.168.58.2")
fr5_A.set_nowplace(2)
fr5_A.move_to_safe_catch(3)
hn_sdk=HN_SDK()
hn_sdk.add_liquid('HCl', 0, 0)
exit()
# add_Liquid=Add_Liquid('add_Liquid')
# add_Solid=Add_Solid('add_Solid')
# hn_sdk=HN_SDK()
# hn_sdk.fr5_init()
# hn_sdk.name_catch('beaker')
# hn_sdk.name_put('add_solid_place')

# hn_sdk.name_catch('test_tube')
# hn_sdk.name_put('test_tube')

# hn_sdk.name_catch('sanjinshaoping')
# hn_sdk.name_put('sanjinshaoping')



