import sys
sys.path.append('src/chemistry_os/src')
from utilities.utility_param import ParamUtils
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 
from facilities.facility_filter import Filter
import time



@staticmethod
def main_thread_func():
    filter = Filter("filter")
    print(filter.liquid_convert_dict)
    main_parser = CommandParser()
    main_parser.start()
        # 保持主线程运行
    ParamUtils.param_dict_update()
    print(ParamUtils.param_dict)
    # filter.set_pump_dir_name("water",0)
    # filter.pump_control_name("water",1)
    filter.pump_add_test_name("water",test= False)
    # time.sleep(20)
    # filter.pump_control_name("water",0)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main_sys = System("os")
    main_sys.main_thread_target = main_thread_func
    main_sys.start()
