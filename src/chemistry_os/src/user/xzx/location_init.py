import sys
import time
sys.path.append('src/chemistry_os/src')
from facility import Facility
from facilities.facility_server import TCPServer
from facilities.facility_filter import Filter
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 

@staticmethod
def main_thread_func():
    # filter = Filter("filter")
    main_parser = CommandParser()
    main_parser.start()

    main_server = TCPServer(test=True)
    
    main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register("facility_location",200, System.facility_location)
    main_server.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("主线程退出")

if __name__ == '__main__':
    main_sys = System("os")
    main_sys.main_thread_target = main_thread_func
    main_sys.start()