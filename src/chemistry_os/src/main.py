from facilities.facility_filter import Filter
from facilities.facility_bath import Bath
from facilities.facility_system import System
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_temp import FacilityTemp
from parser import CommandParser
from server import TCPServer
from facility import Facility
import time
import sys

sys.path.append('src/chemistry_os/src')

if __name__ == '__main__':
    # filter = Filter("filter", "/dev/ttyUSB0")
    main_sys = System("os")
    # fr5 = Fr5Arm("fr5A","192.168.58.2")


    main_server = TCPServer()
    # main_server.register("example_unit", 5,fr5.data_dict, fr5.dict_update_angles)
    # main_server.register("example_unit", 5,fr5.data_dict, fr5.data_dict_update_angles)
    main_server.register("example_unit", 50,Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.start()
    main_parser = CommandParser()
    main_parser.start(input_mode="curses")
    # # main_parser.parse("os project name=pro1 file=double1.json")


    # 保持主线程运行
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()
