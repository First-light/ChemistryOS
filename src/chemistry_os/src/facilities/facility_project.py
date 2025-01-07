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
    PAUSE = 3    # 暂停
    QUIT = 4     # 退出
    ERROR = 5    # 错误

class Project(Facility):
    type = "project"

    def __init__(self, name: str, file: str):
        super().__init__(name, Project.type)
        self.step = 1
        self.project_state = ProjectState.NO_FILE
        self.cmd_load(file)
        self.sub_parser = CommandParser()
        self.executor_thread = threading.Thread(target=self.executor)
        self.executor_thread.daemon = True
        self.executor_thread.start()

    def __del__(self):
        # 停止线程
        self.executor_thread.join()


    def executor(self):
        while True:
            if self.project_state == ProjectState.READY:
                # 等待命令
                time.sleep(0.1)

            elif self.project_state == ProjectState.RUNNING:
                # 执行任务
                sequence = self.dict['configs']['sequence']
                self.executor_run_step(self.step,sequence)
                self.step += 1
                if self.step > len(sequence):
                    self.project_state = ProjectState.QUIT
                time.sleep(0.1)

            elif self.project_state == ProjectState.PAUSE:
                time.sleep(0.1)

            elif self.project_state == ProjectState.QUIT:
                print("quit")
                self.project_state = ProjectState.READY
                self.step = self.dict['configs']['startStep']

            elif self.project_state == ProjectState.NO_FILE:
                time.sleep(0.1)


            time.sleep(0.02)


    def executor_check_all(self):
        self.executor_check_objects()
        self.executor_check_step()


    def executor_check_objects(self):
        print("Self check for all objects...")
        obj_name_list = []

        for tuple_t in Facility.tuple_list:
            name = tuple_t[0]
            obj_name_list.append(name)

        for file_obj_name in self.dict['objects']:
            if any(obj_name == file_obj_name for obj_name in obj_name_list):
                print(f"Object {file_obj_name} exists in the system.")
            else:
                print(f"Object {file_obj_name} does not exist in the system.")


    def executor_check_step(self):
        print("Self check for all step...")
        sequence_steps = self.dict['configs']['sequence']
        process_steps = self.dict['process'].keys()
        for step in sequence_steps:
            if step in process_steps:
                print(f"Step {step} exists in the process.")
            else:
                print(f"Step {step} does not exist in the process.")


    def executor_run_step(self, step_num: int,sequence):    
        # 获取sequence中的步骤名称
        step_name = sequence[step_num - 1]
        # 在process中查找对应的步骤
        step_info = self.dict['process'][step_name]
        
        if 'sequence' in step_info:
            sub_sequence = step_info['sequence']
            for sub_step_num in range(len(sub_sequence)):
                self.executor_run_step(sub_step_num+1,sub_sequence)
            return

        # 获取步骤的object, command, parameters
        obj = step_info['object']
        command = step_info['command']
        parameters = step_info['parameters']
        # 将parameters转换为字符串
        parameters_str = " ".join([f"{key}={value}" for key, value in parameters.items()])
        # 将object, command, parameters串成字符串
        result_str = f"{obj} {command} {parameters_str}"
        ret = self.sub_parser.parse(result_str)
        if ret == 2:
            self.project_state = ProjectState.PAUSE
            print(f"Failed to execute step {step_num} {step_name}.")



    def cmd_init(self):
        self.parser.register("load", self.cmd_load, {"file": ''}, "load file")
        self.parser.register("supple", self.cmd_objects_supple, {}, "check objects and supple missing objects")
        self.parser.register("run", self.cmd_project_run, {}, "run project")
        self.parser.register("stop", self.cmd_project_run, {}, "stop project")
        self.parser.register("exit", self.cmd_project_run, {}, "exit project")


    def cmd_objects_supple(self):
        if self.dict is None:
            print("No file loaded")
            return
        
        print("Supple missing objects")
        obj_name_list = []

        for tuple_t in Facility.tuple_list:
            name = tuple_t[0]
            obj_name_list.append(name)

        for file_obj_name in self.dict['objects']:
            if any(obj_name == file_obj_name for obj_name in obj_name_list):
                print(f"Object {file_obj_name} exists in the system.")
            else:
                # 读取self.data['objects'][file_obj_name]['type']的信息,调用sub_parser的parse方法，输入“os {type} 键1=键的值 ......”
                print(f"Create object {file_obj_name} in the system.")
                # 读取 self.data['objects'][file_obj_name]['type'] 的信息
                obj_type = self.dict['objects'][file_obj_name]['type']
                obj_params = self.dict['objects'][file_obj_name]
                # 构建参数字符串
                obj_params_str = " ".join([f"{key}={value}" for key, value in obj_params.items() if key != 'type'])
                # 构建最终的命令字符串
                result_str = f"os {obj_type} name={file_obj_name} {obj_params_str}"
                # 调用 sub_parser 的 parse 方法
                ret = self.sub_parser.parse(result_str)
                if ret != 0:
                    print(f"Failed to create object {file_obj_name} in the system.")
                    break
                

    def cmd_project_run(self):
        if self.dict is None:
            print("No file loaded")
            return
        print("running")
        self.project_state = ProjectState.RUNNING

    def cmd_project_stop(self):
        print("stop")
        self.project_state = ProjectState.PAUSE

    def cmd_project_exit(self):
        print("exit")
        self.project_state = ProjectState.QUIT

    def cmd_load(self, file: str):
        if file == '':
            print("Please input the file name.")
            return

        json_file_path = os.path.join(os.path.dirname(__file__), 'json/', file + ".json")
        print("path: ", json_file_path)

        if not os.path.isfile(json_file_path):
            print(f"File {file}.json does not exist.")
        else:
            self.cmd_load_avaliable(json_file_path)

    def cmd_load_avaliable(self, json_file_path: str):
        self.file = json_file_path
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # print("JSON file content: ", data)
                # 你可以在这里对解析后的 JSON 数据进行进一步处理
                self.dict = data
                # 创建并启动线程
                self.executor_check_all()
                self.step = self.dict['configs']['startStep']
                self.project_state = ProjectState.READY
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON file: {e}")
