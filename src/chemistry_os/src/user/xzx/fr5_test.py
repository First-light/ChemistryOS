import sys
sys.path.append('src/chemistry_os/src')
from facilities.flowdisplay import Flowdisplay
from facilities.facility_filter import Filter
from facilities.facility_bath import Bath
from facilities.facility_system import System
from facilities.facility_fr5arm import Fr5Arm
from facility import Facility
from facilities.facility_parser import CommandParser
from facilities.facility_server import TCPServer
import time
import sys

sys.path.append('src/chemistry_os/src')


@staticmethod
def main_thread_func():
    fr5 = Fr5Arm("fr5A","192.168.58.2")
    fr5.fr5_init_and_pose()


    main_server = TCPServer()
    
    main_server.register_pkg("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register_pkg("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.update_process_display_dict)
    main_server.register_pkg("fr5A", 5, fr5.data_dict, fr5.data_dict_update)

    main_server.start()
    main_parser = CommandParser()
    main_parser.parse("os project name=pro file=fr5.json")
    main_parser.parse("os check")
    main_parser.start()

    # fr5.move_to_desc([100,200,400,90,0,180], vel=20)
    # fr5.move_to_desc([100,300,400,90,0,180], vel=20)
    # # print(1)
    # fr5.move_by(0, 0, -30, vel=20)

    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("主线程退出")

if __name__ == '__main__':
    main_sys = System("os")
    main_sys.main_thread_target = main_thread_func
    main_sys.start()
