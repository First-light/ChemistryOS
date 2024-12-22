import sys
sys.path.append('src/chemistry_os/src')
import threading
import time
from parser import CommandParser 
from facilities.facility_temp import FacilityTemp
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_system import System

if __name__ == '__main__':
    
    # fr5_A = Fr5Arm("fr5A","192.168.58.2")
    # fr5_B = Fr5Arm("fr5A","192.168.59.6")
    fr5_A = FacilityTemp("fr5A",0,1)
    fr5_B = FacilityTemp("fr5B",2,3)
    fr5_C = FacilityTemp("fr5C",4,5)
    main_sys = System("os")


    main_parser = CommandParser()
    main_parser.parse("os check")
    main_parser.parse("os project name=pro file=arm")
    main_parser.start()

    # 保持主线程运行
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()



