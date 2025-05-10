import time
import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_fr5arm import Fr5Arm
from sdk import HN_SDK

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



fr5_A = Fr5Arm("fr5A","192.168.58.2")
# fr5_A.gripper_activate()
# fr5_A.Go_to_start_zone_0()
fr5_A.set_nowplace(1)
fr5_A.move_to_safe_catch(0)

