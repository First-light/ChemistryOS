import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
import os
import json
import threading
import time
from enum import Enum, auto
from parser import CommandParser

class ProjectState(Enum):
    NO_FILE = 0  # 无文件
    READY = 1    # 准备
    RUNNING = 2  # 运行中
    PAUSE = 3   # 暂停
    QUIT  = 4    # 退出
    ERROR = 5    # 错误



class Project(Facility):
    def __init__(self, name: str, file: str):
        super().__init__(name)
        self.state = ProjectState.NO_FILE
        self.cmd_load(file)
        self.sub_parser = CommandParser()



    def __del__(self):
        # 停止线程
        self.executor_thread.join()

    def executor(self):
        self.executor_check_all()
        step = self.data['configs']['startStep']
        while True:

            if self.state == ProjectState.READY:
                # 等待命令
                time.sleep(0.1)
            elif self.state == ProjectState.RUNNING:
                # 执行任务
                self.executor_run_step(step)
                step += 1
                if step > len(self.data['configs']['sequence']):
                    self.state = ProjectState.QUIT
                time.sleep(0.1)
            elif self.state == ProjectState.PAUSE:
                self.cmd_print_head
                print("pause")
                time.sleep(0.1)
            elif self.state == ProjectState.QUIT:
                self.cmd_print_head
                print("quit")
                break
            time.sleep(0.01)
        
        
    def executor_check_all(self):
        self.executor_check_objects()
        self.executor_check_step()


    def executor_check_objects(self):
        self.cmd_print_head
        print("Self check for all objects...")
        obj_name_list = []

        for tuple_t in Facility.tuple_list:
            name = tuple_t[0]
            obj_name_list.append(name)

        for file_obj_name in self.data['objects']:
            if any(obj_name == file_obj_name for obj_name in obj_name_list):
                print(f"Object {file_obj_name} exists in the system.")
            else:
                print(f"Object {file_obj_name} does not exist in the system.")


    def executor_check_step(self):
        self.cmd_print_head
        print("Self check for all step...")
        sequence_steps = self.data['configs']['sequence']
        process_steps = self.data['process'].keys()
        for step in sequence_steps:
            if step in process_steps:
                print(f"Step {step} exists in the process.")
            else:
                print(f"Step {step} does not exist in the process.")



    def executor_run_step(self,step_num: int):
        # 获取sequence中的步骤名称
        step_name = self.data['configs']['sequence'][step_num - 1]
        # 在process中查找对应的步骤
        step_info = self.data['process'][step_name]
        # 获取步骤的object, command, parameters
        obj = step_info['object']
        command = step_info['command']
        parameters = step_info['parameters']
        # 将parameters转换为字符串
        parameters_str = " ".join([f"{key}={value}" for key, value in parameters.items()])
        # 将object, command, parameters串成字符串
        result_str = f"{obj} {command} {parameters_str}"
        self.sub_parser.parse(result_str)



    def cmd_init(self):
        self.parser.register("load", self.cmd_load, {"file": ''}, "load file")
        self.parser.register("run", self.cmd_project_run, {}, "run project")
        self.parser.register("stop", self.cmd_project_run, {}, "run project")
        self.parser.register("exit", self.cmd_project_run, {}, "run project")


    def cmd_project_run(self):
        self.cmd_print_head
        print("running")
        self.state = ProjectState.RUNNING

    def cmd_project_stop(self):
        self.cmd_print_head
        print("stop")
        self.state = ProjectState.PAUSE

    def cmd_project_exit(self):
        self.cmd_print_head
        print("exit")
        self.state = ProjectState.QUIT


    def cmd_load(self, file: str):
        if file == '':
            self.cmd_print_head
            print("Please input the file name.")
            return
        
        json_file_path = os.path.join(os.path.dirname(__file__), 'json/', file + ".json")
        self.cmd_print_head
        print("path: ", json_file_path)

        if not os.path.isfile(json_file_path):
            self.cmd_print_head
            print(f"File {file}.json does not exist.")
        else:
            self.cmd_load_avaliable(json_file_path)



    def cmd_load_avaliable(self, json_file_path: str):
        self.file = json_file_path
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cmd_print_head
                print("JSON file content: ", data)
                # 你可以在这里对解析后的 JSON 数据进行进一步处理
                self.data = data
                # 创建并启动线程
                self.executor_thread = threading.Thread(target=self.executor)
                self.executor_thread.daemon = True
                self.executor_thread.start()
                self.state = ProjectState.READY
        except json.JSONDecodeError as e:
            self.cmd_print_head
            print(f"Error decoding JSON file: {e}")



        

