<<<<<<< HEAD
import sys
sys.path.append('src/chemistry_os/src')
import threading
import time
from parser import CommandParser 
from facilities.facility_temp import FacilityTemp
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_system import System

if __name__ == '__main__':

    # fr3 = Fr3Arm("fr3","192.168.60.2")
    
    # fr5_A = Fr5Arm("fr5A","192.168.58.2")
    # # # fr5_B = Fr5Arm("fr5A","192.168.59.6")
    # # fr5_A = FacilityTemp("fr5A",0,1)
    # # fr5_B = FacilityTemp("fr5B",2,3)
    # # fr5_C = FacilityTemp("fr5C",4,5)
    # main_sys = System("os")

    # main_parser = CommandParser()
    # main_parser.parse("os check")
    # main_parser.parse("os project name=pro1 file=test2.json")
    # main_parser.start()
    # main_sys.objects
    # # main_parser.parse("fr5A out")
    # # main_parser.parse("fr3 reset")
    # main_parser.parse("fr5A reset")
    
    

    #脱机测试
    fr5_A = FacilityTemp("fr5A",0,1)
    fr5_B = FacilityTemp("fr5B",2,3)
    fr5_C = FacilityTemp("fr5C",4,5)
    main_sys = System("os")


    main_parser = CommandParser()
    main_parser.parse("os project name=pro1 file=double1.json")
    main_parser.parse("os project name=pro2 file=double1.json")
    main_parser.parse("os check")
    main_parser.start()
    
=======
from facilities.facility_filter import Filter
from facilities.facility_bath import Bath
from facilities.facility_system import System
from facilities.facility_fr3arm import Fr3Arm
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_temp import FacilityTemp
from parser import CommandParser
import time
import sys

sys.path.append('src/chemistry_os/src')

if __name__ == '__main__':
    filter = Filter("filter", "/dev/ttyUSB0",sub_address = 0x01)
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
    time.sleep(20)
    main_parser.parse("filter airpump state=1")


    time.sleep(1)
    # main_parser.parse("filter valve state=0")
    # time.sleep(1)
    # main_parser.parse("filter speed speed=600")
    # time.sleep(1)
    # main_parser.parse("filter dir direction=1")
    # time.sleep(1)
    # main_parser.parse("filter pump state=1")
    # time.sleep(10)
    # main_parser.parse("filter pump state=0")
    # main_parser.parse("filter query")
    # time.sleep(1)

>>>>>>> ac2d50baef95bef4de4d4d959dd5323c9dd2ea66
    # 保持主线程运行
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()
<<<<<<< HEAD



=======
>>>>>>> ac2d50baef95bef4de4d4d959dd5323c9dd2ea66
