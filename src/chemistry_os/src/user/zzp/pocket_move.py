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


fr5_A = Fr5Arm("fr5A","192.168.58.2")
fr5_A.check_place_move()
fr5_A.move_to_safe_catch(3)
fr5_A.move_to_desc([-80.0, 260.0, 380.0, 90.0, 0.0, -90.0], type='MoveJ', vel=fr5_A.default_speed)

fr5_A.move_to_desc([100.0, 200.0, 400.0, 90.0, 0.0, 180.0], type='MoveJ', vel=fr5_A.default_speed)
fr5_A.check_place_move()
fr5_A.move_to_safe_catch(0)