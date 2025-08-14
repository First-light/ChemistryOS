import ctypes
from inspect import ismethod
import json
from logging import Logger
import os
import sys
import threading
import time
from types import MethodType
sys.path.append('src/chemistry_os/src')
from utilities.utility_emergency import EmergencyUtils
from utilities.utility_log import LogUtils
from facility import Facility
from facilities.facility_fr5arm import Fr5Arm
from facilities.facility_project import Project
from prettytable import PrettyTable
from facilities.flowdisplay import Flowdisplay
from facilities.facility_temp import FacilityTemp
from structs import FacilityState
from utilities.utility_param import ParamUtils


class System(Facility):
    type = "system"
    facility_location = {}
    

    # 类级别的默认豁免类型白名单
    default_except_types = [
        "system",      # 系统对象
        "parser",      # 
        "project",     # 
        "tcp_server"       #
    ]
    
    

    def __init__(self, name: str = "os",error_detect:bool = True):
        super().__init__(name, System.type)
        LogUtils.log = self.log
        self.main_thread_target:MethodType= None
        self.main_thread = None
        self.main_thread_paused = True

        self.error_detect = error_detect
        self.error_detect_thread = None
        
        
        self.objects = []  # 用于存储创建的实例


    def cmd_init(self):
        self.parser.register("fr5arm", self.create_fr5robot, {"name": '', "ip": ''}, "创建 FR5 机械臂")
        self.parser.register("temp", self.create_temp, {"name": '', "param1": '', "param2": ''}, "创建温控设备")
        self.parser.register("project", self.create_project, {"name": '', "file": ''}, "创建项目")
        self.parser.register("delete", self.destroy, {"name": ''}, "删除对象")
        self.parser.register("check", self.system_check, {}, "列出所有对象")
        self.parser.register("check_dict",self.check_all_init_dict,{},"检查所有对象初始化参数")
        self.parser.register("!", self.stop_all, {}, "停止所有对象")
        self.parser.register("thread_pause", self.pause_main_thread, {}, "暂停主线程")
        self.parser.register("thread_resume", self.resume_main_thread, {}, "恢复主线程")
        self.parser.register("thread_stop", self.stop_main_thread, {}, "停止主线程")


    def start(self):
        if self.main_thread_target is None:
            self.log.error("主线程目标函数未设置，无法启动主线程。请设置 System.main_thread_target。")
            return False
        else:
            self.load_data()  # 加载设施位置数据
            self.init_dict = ParamUtils.get_init_params(self)
            self.start_error_detect_thread()  # 启动error检测线程
            self.start_main_thread()

            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("程序退出")


            return True
        
    def load_data(self):
        try:
            self.fac_location_file_path = "src/chemistry_os/src/facilities/location/fac_location.json"
            with open(self.fac_location_file_path, 'r') as file:
                System.facility_location = json.load(file)
        except FileNotFoundError:
            self.log.error(f"无法找到设施位置文件: {self.fac_location_file_path}")
            System.facility_location = {}

    def start_main_thread(self):
        try:
            self.main_thread = threading.Thread(target=self.main_thread_target)
            self.main_thread.daemon = True
            self.main_thread.start()
            self.main_thread_paused = False
        except Exception as e:
            self.log.error(f"主线程启动失败: {e}")

    

    def error_detect_func(self):
    #检测机械臂急停标志位，检测到后将机械臂软件标签位设置为ERROR
        while self.error_detect:
            if EmergencyUtils.if_emergency == False:
                for i, tuple_t in enumerate(Facility.tuple_list):
                    if tuple_t.facility.state == FacilityState.ERROR:
                        name = tuple_t.name
                        self.log.warning(f"检测到对象 {name} 标签ERROR,执行急停进程。")
                        
                        self.stop_all()
                        EmergencyUtils.if_emergency = True
                    
            time.sleep(0.002)


    def start_error_detect_thread(self):
        if self.error_detect and self.error_detect_thread is None:
            try:
                self.error_detect_thread = threading.Thread(target=self.error_detect_func)
                self.error_detect_thread.daemon = True
                self.error_detect_thread.start()
            except Exception as e:
                self.log.error(f"安全检测线程启动失败: {e}")
                self.error_detect = False


    def pause_main_thread(self):
        if self.main_thread and self.main_thread.is_alive() and not self.main_thread_paused:
            # 尝试暂停线程（Linux系统）
            try:
                thread_id = self.main_thread.ident
                self.main_thread_paused = True
                # 发送SIGSTOP信号给线程
                os.system(f"kill -STOP {thread_id}")
                self.log.info("主线程已暂停")
            except Exception as e:
                self.log.error(f"线程暂停失败: {e}")
            


    def resume_main_thread(self):
        """恢复主线程"""
        if self.main_thread and self.main_thread.is_alive() and self.main_thread_paused:
            try:
                thread_id = self.main_thread.ident
                self.main_thread_paused = False
                self.log.info("正在恢复主线程...")
                # 恢复线程
                os.system(f"kill -CONT {thread_id}")
                self.log.info("主线程已恢复")
            except Exception as e:
                self.log.error(f"线程恢复失败: {e}")

    def stop_main_thread(self):
        """停止主线程"""
        self.main_thread_paused = False  # 确保不被暂停阻塞
        
        if self.main_thread and self.main_thread.is_alive():
            # 强制终止线程（不推荐，但可用于紧急情况）
            try:
                thread_id = self.main_thread.ident
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(thread_id), 
                    ctypes.py_object(SystemExit)
                )
                if res > 1:
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                    self.log.error("线程终止失败")
                else:
                    self.log.info("主线程已强制停止")
            except Exception as e:
                self.log.error(f"停止主线程失败: {e}")

    def cmd_error_handing(self):
        pass

    def cmd_stop_handing(self):
        pass

    def cmd_reset(self):#从error/stop恢复idle的状态
        pass

    def error_check_thread():
        pass

    def stop_all(self):
        self.pause_main_thread()
        for tuple_t in Facility.tuple_list:
            name = tuple_t.name
            object_type = tuple_t.type
            object = tuple_t.facility
            
            # 检查是否在白名单中
            if object_type not in System.default_except_types:
                if object.state != FacilityState.ERROR:
                    object.state = FacilityState.STOP
                    self.log.info(f"对象 {name} (类型: {object_type}) 标记停止。")
                
        for i, tuple_t in enumerate(Facility.tuple_list):
            name = tuple_t.name
            object = tuple_t.facility
            object_type = tuple_t.type
            if object_type not in System.default_except_types:
                if object.state == FacilityState.ERROR or object.state == FacilityState.STOP:
                    # 执行急停进程
                    object.cmd_stop_handing()
                    self.log.info(f"对象 {name} 执行急停进程。")
    
    def check_all_init_dict(self):
        self.log.info("检查所有对象初始化参数:")
        for i, tuple_t in enumerate(Facility.tuple_list):
            if hasattr(tuple_t.facility, 'init_dict') and tuple_t.facility.init_dict:
                self.log.info(f"对象 {tuple_t.name} 的初始化参数: {tuple_t.facility.init_dict}")

    def system_check(self):
        
        table = PrettyTable()
        table.field_names = ["序号", "对象名称", "对象类型", "对象状态"]

        for i, tuple_t in enumerate(Facility.tuple_list):
            name = tuple_t.name
            type = tuple_t.type
            state = tuple_t.facility.state
            table.add_row([i + 1, name, type, state])

        self.log.info(f"检查所有对象:\n{table}")

    def destroy(self, name: str):
        if name == '':
            self.log.warning("删除对象失败: 未提供名称")
            return

        for i, tuple_t in enumerate(Facility.tuple_list):
            objectname = tuple_t.name
            obj = tuple_t.facility
            if name == objectname:
                # 删除对象
                del obj
                # 删除元组
                del Facility.tuple_list[i]
                self.log.info(f"对象 {name} 已成功删除。")
                return
        self.log.warning(f"未找到名称为 {name} 的对象。")

    # 以下为创建实例的函数

    def create_temp(self, name: str, param1, param2):
        if name != '' or param1 != '' or param2 != '':
            self.log.info(f"创建温控设备: 名称={name}, 参数1={param1}, 参数2={param2}")
            new_temp = FacilityTemp(name, param1, param2)
            self.objects.append(new_temp)
        else:
            self.log.warning(f"创建温控设备失败: 名称={name}, 参数1={param1}, 参数2={param2}")

    def create_fr5robot(self, name: str, ip: str):
        if name != '' or ip != '':
            self.log.info(f"创建 FR5 机械臂: 名称={name}, IP={ip}")
            new_robot = Fr5Arm(name, ip)
            self.objects.append(new_robot)
        else:
            self.log.warning(f"创建 FR5 机械臂失败: 名称={name}, IP={ip}")

    def create_project(self, name: str, file: str):
        if name != '' or file != '':
            self.log.info(f"创建项目: 名称={name}, 文件={file}")
            new_project = Project(name, file)
            self.objects.append(new_project)
        else:
            self.log.warning(f"创建项目失败: 名称={name}, 文件={file}")
