import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 
from facilities.facility_filter import Filter
import time

if __name__ == '__main__':
    main_sys = System("os")
    sub_addresses={               # 下级设备地址字典
        "empty": 0x00,           # 空地址
        "solvent": 0x04,          # 溶解溶剂地址
        "water": 0x02,            # 清水清洗液地址
        "acid": 0x03,              # 酸清洗液地址
        "pump": 0x01                # 抽滤地址
    }
    filter = Filter("filter", "/dev/ttyUSB0",sub_addresses = sub_addresses)
    filter.pump_init()  # 初始化蠕动泵

    main_parser = CommandParser()
    main_parser.start()
        # 保持主线程运行


    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        main_parser.end()