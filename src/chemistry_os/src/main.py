import sys
sys.path.append('src/chemistry_os/src')
import threading
import time
from parser import CommandParser 
from facilities.facility_temp import FacilityTemp
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_system import System
from facilities.facility_bath import Bath
from facilities.facility_filter import Filter

if __name__ == '__main__':
    filter = Filter("filter","/dev/ttyUSB0")
    main_sys = System("os")

    time.sleep(5)
    main_parser = CommandParser()
    # main_parser.parse("os project name=pro1 file=double1.json")
    # main_parser.parse("os project name=pro2 file=double1.json")
    main_parser.parse("os check")
    main_parser.start()
    # 气泵测试
    main_parser.parse("filter valve state=1")
    time.sleep(1)
    main_parser.parse("filter airpump state=1")
    time.sleep(40)
    main_parser.parse("filter airpump state=0")
    time.sleep(1)
    main_parser.parse("filter pump state=0")

    
    # main_parser.parse("filter valve state=0")
    # time.sleep(1)
    # main_parser.parse("filter speed speed=600")
    # time.sleep(1)
    # main_parser.parse("filter dir direction=1")
    # time.sleep(1)
    # main_parser.parse("filter pump state=1")
    # time.sleep(40)
    # main_parser.parse("filter pump state=0")
    # main_parser.parse("filter query")
    # time.sleep(1)
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()



