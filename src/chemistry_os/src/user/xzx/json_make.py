import sys
sys.path.append('src/chemistry_os/src')
from facilities.facility_system import System
from facilities.facility_parser import CommandParser 
from facilities.facility_filter import Filter
from facilities.facility_server import TCPServer
from facilities.facility_project import Project
from facility import Facility
from utilities.utility_project import ProjectUtils
import time

# 创建别名


@staticmethod
def main_thread_func():
    filter = Filter("filter")
    
        # 保持主线程运行
    ProjectUtils.register_object("filter")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_sub_process()
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_sub_process_start()
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_process("filter", "test")
    ProjectUtils.register_sub_process()
    # ProjectUtils.show_registered_data()
    ProjectUtils.make()

    pro = Project(name="pro",file="json_make.json") 

    main_parser = CommandParser()
    main_parser.parse("os check")
    main_parser.start()

    main_server = TCPServer(test=True)
    main_server.register("log", 50, Facility.log_cache_dict, Facility.log_cache_dict_update)
    main_server.register("project_json", 200, pro.dict)
    main_server.register("facility_location",200, System.facility_location)
    main_server.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main_sys = System("os")
    main_sys.main_thread_target = main_thread_func
    main_sys.start()
