import sys
sys.path.append('src/chemistry_os/src')
import threading
import time
from parser import CommandParser 
from facility import facility_temp
from facilities.facility_fr5arm import fr5robot
from facilities.facility_system import system


if __name__ == '__main__':
    
    # fr5_A = fr5robot("fr5A","192.168.58.6")
    # fr5_B = fr5robot("fr5A","192.168.59.6")
    # main_system = instantiator("sys")
    main_sys = system("sys")


    main_parser = CommandParser()
    main_parser.parse("sys project name=pro file=test")
    main_parser.start()

    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        main_parser.end()



