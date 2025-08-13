import sys
import time
sys.path.append('src/chemistry_os/src')
from facilities.facility_filter import Filter
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 


if __name__ == '__main__':

    main_sys = System("os")
    # filter = Filter("filter")
    main_parser = CommandParser()
    main_parser.start()
    num:float = 2.0/3.0

    main_sys.log.info(f"系统初始化{num:.3f}完成")
    
        # 保持主线程运行
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()