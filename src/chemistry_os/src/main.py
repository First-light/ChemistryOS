import sys
sys.path.append('src/chemistry_os/src')
import threading
import time
from parser import CommandParser 
from facilities.class_template import facility_temp
from facilities.class_fr5arm import fr5robot

if __name__ == '__main__':
    
    # fr5_A = fr5robot("fr5A","192.168.58.6")
    # fr5_B = fr5robot("fr5A","192.168.59.6")

    fr5_A = facility_temp("fr5A",1,2)
    fr5_B = facility_temp("fr5B",30,40)

    main_parser = CommandParser()
    main_parser.start()

    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        main_parser.end()



