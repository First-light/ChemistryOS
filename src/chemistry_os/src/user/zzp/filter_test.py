import threading
import time
import sys

sys.path.append('src/chemistry_os/src')
from facilities.facility_thermometer import Thermometer
from facilities.facility_pumps import PumpGroup
from facilities.facility_addSolid import Add_Solid
import logging
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_sdk import HN_SDK
from facilities.facility_bath import Bath
from facilities.flowdisplay import Flowdisplay
from facility import Facility
from facilities.facility_server import TCPServer
from facilities.facility_filter import Filter
from facilities.facility_parser import CommandParser
from facilities.facility_system import System


main_sys = System("os") # 必须放最前
main_parser = CommandParser()
main_parser.start(input="shell")
add_Liquid=PumpGroup('add_Liquid')
add_Solid=Add_Solid('add_Solid')
fr5_C = Fr5Arm("fr5C","192.168.58.3")
fr5_A = Fr5Arm("fr5A","192.168.58.2")
bath = Bath('bath')
filter = Filter("filter")
thermometer = Thermometer("thermometer")

hn_sdk=HN_SDK()
hn_sdk.HN_init()
hn_sdk.move_shaoping_support2C()
hn_sdk.bath_catch('bath_fr5_catch')
hn_sdk.move_wash('sanjinshaoping_wash_1', 0)
# hn_sdk.move_wash('sanjinshaoping_wash_3', 2)
# hn_sdk.bath_mix()
# hn_sdk.move_wash('sanjinshaoping_wash_1', 0)
# hn_sdk.move_wash('sanjinshaoping_wash_3', 2)
# hn_sdk.bath_mix()
# hn_sdk.move_wash('sanjinshaoping_wash_1', 0)
# hn_sdk.move_wash('sanjinshaoping_wash_2', 1)
hn_sdk.name_put('sanjinshaoping_support_put')
exit()