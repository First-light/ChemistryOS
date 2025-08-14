import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 
import time










@staticmethod
def main_thread_func():
    main_parser = CommandParser()
    main_parser.start()
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("主线程退出")

if __name__ == '__main__':
    main_sys = System("os")
    main_sys.main_thread_target = main_thread_func
    main_sys.start()