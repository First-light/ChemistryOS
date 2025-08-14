import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 
from facilities.facility_filter import Filter
from facilities.facility_server import TCPServer
from facility import Facility
from utilities.utility_project import ProjectUtils
import time

# 创建别名


@staticmethod
def main_thread_func():
    filter = Filter("filter")

    main_parser = CommandParser()
    main_parser.start()
        # 保持主线程运行
    ProjectUtils.register_object("filter")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.show_registered_data()
    ProjectUtils.make



    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main_sys = System("os")
    main_sys.main_thread_target = main_thread_func
    main_sys.start()
