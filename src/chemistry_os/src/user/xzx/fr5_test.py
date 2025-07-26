import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_flowdisplay import Flowdisplay
from facilities.facility_filter import Filter
from facilities.facility_bath import Bath
from facilities.facility_system import System
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_fr5arm import Fr5Arm
from facility import Facility
from parser import CommandParser
from server import TCPServer
import time
import sys

sys.path.append('src/chemistry_os/src')

if __name__ == '__main__':
    main_sys = System("os")
    flowdisplay = Flowdisplay("flowdisplay")
    fr5 = Fr5Arm("fr5A","192.168.58.2")
    fr5.Go_to_start_zone_0()


    main_server = TCPServer()
    
    main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.update_process_display_dict)
    main_server.register("fr5A", 5, fr5.data_dict, fr5.data_dict_update_angles)

    main_server.start()
    main_parser = CommandParser()
    main_parser.parse("os project name=pro file=fr5.json")
    main_parser.parse("os check")
    main_parser.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()

