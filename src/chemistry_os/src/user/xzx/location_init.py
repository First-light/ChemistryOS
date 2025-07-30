import sys
import time
sys.path.append('src/chemistry_os/src')
from facility import Facility
from facilities.facility_server import TCPServer
from facilities.facility_filter import Filter
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 


if __name__ == '__main__':

    main_sys = System("os")
    # filter = Filter("filter")
    main_parser = CommandParser()
    main_parser.start()

    main_server = TCPServer(test=True)
    
    main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register("facility_location",200, System.facility_location)
    # main_server.register("flow", 50, Flowdisplay.process_display_dict, Flowdisplay.update_process_display_dict)
    

    main_server.start()


        # 保持主线程运行
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()