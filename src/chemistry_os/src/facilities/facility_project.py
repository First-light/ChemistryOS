import sys
sys.path.append('src/chemistry_os/src')
from facility import Facility
import os
import json
import threading
import time
from parser import CommandParser
from structs import ProjectState
from structs import FacilityState


class Project(Facility):
    type = "project"

    def __init__(self, name: str, file: str):
        super().__init__(name, Project.type)
        self.step = 1
        self.project_state = ProjectState.INIT
        self.data_type = ""
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
                self.executor_running()    
                time.sleep(0.1)

            elif self.project_state == ProjectState.PAUSE:
                time.sleep(0.1)

            elif self.project_state == ProjectState.QUIT:
                print("quit")
                self.project_state = ProjectState.INIT
                self.step = self.dict['configs']['startStep']

            elif self.project_state == ProjectState.INIT:
                time.sleep(0.1)

            time.sleep(0.02)


    def executor_check_all(self):
        if self.data_type == "json":
            objects_ok = self.json_check_objects()
            steps_ok = self.json_check_step()
            start_step_ok = self.json_check_start_step()

            if objects_ok and steps_ok and start_step_ok:
                self.log.info("自检通过。项目状态设置为 READY。")
                self.project_state = ProjectState.READY
            else:
                self.log.warning("自检失败。项目状态未设置为 READY。")
        else:
            self.log.warning(f"未加载数据或数据类型:[{self.data_type}] 不支持。")


    def json_check_objects(self):
        self.log.info("开始检查所有对象...")
        all_objects_exist = True

        # 遍历 self.dict['objects'] 中的对象
        for obj_name in self.dict['objects'].items():
            # 在 Facility.tuple_list 中查找对应的对象
            matching_tuple = next((tuple_t for tuple_t in Facility.tuple_list if tuple_t[0] == obj_name), None)

            if matching_tuple:
                obj_state_p = matching_tuple[3].state
                # 检查对象状态是否为 IDLE
                if obj_state_p[0] != FacilityState.IDLE:
                    self.log.warning(f"对象 {obj_name} 当前状态不是空闲 (当前状态: {obj_state_p[0]})。")
                    all_objects_exist = False
            else:
                self.log.warning(f"对象 {obj_name} 不存在于系统中。")
                all_objects_exist = False

        return all_objects_exist

    def json_check_step(self):
        self.log.info("开始检查所有步骤...")
        sequence_steps = self.dict['configs']['sequence']
        process_steps = self.dict['process'].keys()

        all_steps_exist = True
        for step in sequence_steps:
            if step in process_steps:
                print(f"步骤 {step} 存在在流程库中.")
            else:
                print(f"！步骤 {step} 不在流程库中.")
                all_steps_exist = False

        return all_steps_exist

    def count_total_steps(self,sequence):
        total_steps = 0
        for step_name in sequence:
            if step_name in self.dict['process'] and 'sequence' in self.dict['process'][step_name]:
                sub_sequence = self.dict['process'][step_name]['sequence']
                total_steps += self.count_total_steps(sub_sequence)
            else:
                total_steps += 1
        return total_steps
    
    def json_check_start_step(self):
        start_step = self.step
        total_steps = self.count_total_steps(self.dict['configs']['sequence'])
        
        if start_step < 1 or start_step > total_steps:
            self.log.warning(f"错误: 开始步骤 {start_step} 超出范围。有效范围是 1 到 {total_steps}。")
            return False
        else:
            self.log.info(f"开始步骤 {start_step} 检查通过。")
            return True

    def executor_step_up(self,ret):
        print(f"ret: {ret}")
        if ret != 0:
            self.cmd_project_stop()
            print(f"Failed to execute step {self.step}.")
        else:
            print(f"Successfully executed step {self.step}.")
            self.step += 1
        if self.step > self.max_step:
            self.project_state = ProjectState.QUIT

    def executor_running(self):
        # 执行任务
        sequence = self.dict['configs']['sequence']
        global_step_counter = [0]
        self.executor_run_step(self.step,sequence,global_step_counter)

    def executor_run_step(self, step_num: int, sequence, global_step_counter: list):
        # 遍历当前序列中的每个步骤
        for step_name in sequence:
            # 检查是否是子步骤的标题
            if step_name in self.dict['process'] and 'sequence' in self.dict['process'][step_name]:
                # 递归处理子步骤，但不更新全局步骤计数器
                sub_sequence = self.dict['process'][step_name]['sequence']
                self.executor_run_step(step_num, sub_sequence, global_step_counter)
                continue
                

            # 更新全局步骤计数器
            global_step_counter[0] += 1
            current_step = global_step_counter[0]

            # 检查是否达到了目标步骤
            if current_step == step_num:
                # 在process中查找对应的步骤
                step_info = self.dict['process'][step_name]

                # 获取步骤的object, command, parameters
                obj = step_info['object']
                command = step_info['command']
                parameters = step_info['parameters']
                # 将parameters转换为字符串
                parameters_str = " ".join([f"{key}={value}" for key, value in parameters.items()])
                # 将object, command, parameters串成字符串
                result_str = f"{obj} {command} {parameters_str}"
                ret = self.sub_parser.parse(result_str)
                self.executor_step_up(ret)
                break
        
        
        

    def cmd_project_step(self):
        if self.project_state == ProjectState.READY or self.project_state == ProjectState.PAUSE:
            print("execute one step.")
            self.executor_running()
            return
        else :
            print("Project need Ready.")


    def cmd_init(self):
        self.parser.register("load", self.cmd_load, {"file": ''}, "load file")
        self.parser.register("check", self.check, {}, "show project data")
        self.parser.register("supple", self.cmd_objects_supple, {}, "check objects and supple missing objects")
        self.parser.register("run", self.cmd_project_run, {}, "run project")
        self.parser.register("step", self.cmd_project_step, {}, "run project one step")
        self.parser.register("start", self.cmd_project_start_step, {"step": 1}, "start project from step")
        self.parser.register("stop", self.cmd_project_stop, {}, "stop project")
        self.parser.register("continue", self.cmd_project_continue, {}, "continue project")
        self.parser.register("exit", self.cmd_project_exit, {}, "exit project")

    # 定义了一个递归函数 print_steps，用于打印步骤序列。
    # 在 print_steps 函数中，检查每个步骤是否包含子步骤，如果包含，则递归调用 print_steps 来打印子步骤。
    # 在主函数中调用 print_steps 来打印顶层步骤序列。
    def check(self):
        def print_steps(sequence, global_step_counter, indent=0):
            for step in sequence:
                if step in self.dict['process'] and 'sequence' in self.dict['process'][step]:
                    print(f"{' ' * indent}步骤 {global_step_counter[0]}: {step}")
                    print(f"{' ' * (indent + 2)}子步骤:")
                    print_steps(self.dict['process'][step]['sequence'], global_step_counter, indent + 4)
                else:
                    current_marker = " <-- 当前步骤" if global_step_counter[0] == self.step else ""
                    print(f"{' ' * indent}步骤 {global_step_counter[0]}: {step}{current_marker}")
                    global_step_counter[0] += 1

        print("="*40)
        print(f"当前流程状态: {self.project_state.name}")
        print("="*40)
        
        print("流程中的所有步骤:")
        global_step_counter = [1]
        print_steps(self.dict['configs']['sequence'], global_step_counter)
        
        print("\n涉及的对象:")
        for obj in self.dict['objects']:
            print(f"对象: {obj}")
        
        print("="*40)


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
        
    def cmd_project_start_step(self, step: int):
        self.step = step
        self.project_state = ProjectState.INIT
        print(f"项目从步骤 {step} 开始。")
        self.executor_check_all()

    def cmd_project_run(self):
        if self.dict is None:
            print("No file loaded")
            return
        
        elif self.project_state == ProjectState.INIT:
            self.executor_check_all

        elif self.project_state == ProjectState.READY :
            print("running")
            self.project_state = ProjectState.RUNNING
        

    # stop 即流程控制器不继续派发流程
    def cmd_project_stop(self):
        print(f"project {self.name} stop")
        self.project_state = ProjectState.PAUSE

    def cmd_project_continue(self):
        if self.project_state == ProjectState.PAUSE:
            print(f"project {self.name} continue")
            self.project_state = ProjectState.RUNNING
        else :
            print("Project need Pause.")

    def cmd_project_exit(self):
        print(f"project {self.name} exit")
        self.project_state = ProjectState.QUIT

    def cmd_load(self, file: str):
        if file == '':
            self.log.info("请输入文件名。")
            return

        # 获取文件后缀
        file_extension = os.path.splitext(file)[1]
        if file_extension == '':
            self.log.info("请提供带有后缀的文件。")
            return

        # 构建文件路径
        file_path = os.path.join('src/chemistry_os/src/facilities/projects', file)
        # self.log.info("路径: ", file_path)

        if not os.path.isfile(file_path):
            self.log.info(f"文件 {file} 不存在。")
            return

        # 根据文件后缀分类处理
        if file_extension == '.json':
            self.cmd_load_json(file_path)
        else:
            self.log.info(f"不支持的文件类型: {file_extension}")


    def cmd_load_json(self, json_file_path: str):
        self.file = json_file_path
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # print("JSON file content: ", data)
                # 你可以在这里对解析后的 JSON 数据进行进一步处理
                self.cmd_load_json_data(data)
                self.executor_check_all()

        except json.JSONDecodeError as e:
            self.log.info(f"Error decoding JSON file: {e}")



    def cmd_load_json_data(self,data):
        self.log.info("开始加载 JSON 数据...")
        # 检查 JSON 数据的结构
        self.dict = data
        # 创建并启动线程
        self.data_type = "json"
        self.step = self.dict['configs']['startStep']
        self.max_step = self.count_total_steps(self.dict['configs']['sequence'])

        # 遍历 JSON 中的 objects
        for obj_name, obj_params in self.dict.get('objects', {}).items():
            # 在 Facility.tuple_list 中查找对应的对象
            for i, tuple_t in enumerate(Facility.tuple_list):
                name = tuple_t[0]
                obj_instance = tuple_t[3]  # 对应的对象实例

                if name == obj_name:
                    # 将 JSON 中的参数赋值给对象
                    for param_key, param_value in obj_params.items():
                        if hasattr(obj_instance, param_key):
                            setattr(obj_instance, param_key, param_value)
                            self.log.info(f"设置对象 {name} 的参数 {param_key} 为 {param_value}")
                        else:
                            self.log.warning(f"对象 {name} 不存在参数 {param_key}")
                    break
            else:
                self.log.warning(f"未找到名称为 {obj_name} 的对象，无法设置参数")

