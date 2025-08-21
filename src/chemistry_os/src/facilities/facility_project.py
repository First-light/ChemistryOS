import sys
sys.path.append('src/chemistry_os/src')
from exceptions import HNSystemError
from facility import Facility
import os
import json
import threading
import time
from facilities.facility_parser import CommandParser
from structs import ProjectState
from structs import FacilityState
from utilities.utility_param import ParamUtils

class Project(Facility):
    
    type = "project"

    def __init__(self, name: str, file: str=None):
        super().__init__(name, Project.type)    
        self.step:int = 1
        self.file = file
        self.top_step_name = ""
        self.project_dict = {}
        self.project_state = ProjectState.INIT
        self.data_type = ""
        self.cmd_load(file)
        self.sub_parser = CommandParser(parse_only=True)
        self.executor_thread = threading.Thread(target=self.executor)
        self.executor_thread.daemon = True
        self.executor_thread.start()
        self.init_dict = ParamUtils.get_init_params(self)
        self.data_dict = {
            "project_state":self.project_state.value,
            "step" : self.step,
            "top_step_name" : "",
        }

    def data_dict_update(self):
        self.data_dict.update({
            "project_state": self.project_state.value,
            "step": self.step,
            "top_step_name" : self.top_step_name
        })
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

            elif self.project_state == ProjectState.END:
                # self.log.info("流程结束")
                # self.project_state = ProjectState.INIT
                
                self.step = self.project_dict['configs']['startStep']

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
        for obj_name in self.project_dict['objects'].keys():
            # 在 Facility.tuple_list 中查找对应的对象
            matching_tuple = next((tuple_t for tuple_t in Facility.tuple_list if tuple_t.name == obj_name), None)

            if matching_tuple:
                obj_state = matching_tuple.facility.state
                # 检查对象状态是否为 IDLE
                if obj_state != FacilityState.IDLE:
                    self.log.warning(f"对象 {obj_name} 当前状态不是空闲 (当前状态: {obj_state})。")
                    all_objects_exist = False
            else:
                self.log.warning(f"对象 {obj_name} 不存在于系统中。")
                all_objects_exist = False

        return all_objects_exist

    def json_check_step(self):
        self.log.info("开始检查所有步骤...")
        sequence_steps = self.project_dict['configs']['sequence']
        process_steps = self.project_dict['process'].keys()

        all_steps_exist = True
        for step in sequence_steps:
            if step in process_steps:
                self.log.info(f"步骤 {step} 存在在流程库中.")
            else:
                self.log.warning(f"！步骤 {step} 不在流程库中.")
                all_steps_exist = False

        return all_steps_exist

    def count_total_steps(self,sequence):
        total_steps = 0
        for step_name in sequence:
            if step_name in self.project_dict['process'] and 'sequence' in self.project_dict['process'][step_name]:
                sub_sequence = self.project_dict['process'][step_name]['sequence']
                total_steps += self.count_total_steps(sub_sequence)
            else:
                total_steps += 1
        return total_steps
    
    def json_check_start_step(self):
        start_step = self.step
        total_steps = self.count_total_steps(self.project_dict['configs']['sequence'])
        
        result = False
        if total_steps < 1:
            self.log.warning(f"无流程储存")
        elif start_step < 1 or start_step > total_steps:
            self.log.warning(f"开始步骤 {start_step} 超出范围。有效范围是 1 到 {total_steps}。")
        else:
            self.log.info(f"开始步骤 {start_step} 检查通过。")
            result = True
        return result

    def executor_step_up(self,ret:bool):
        if ret is not True:
            self.cmd_project_stop()
            self.log.error(f"步骤 {self.step} 执行失败.")
        else:
            self.log.info(f"步骤 {self.step} 执行成功.")
            self.step += 1
        if self.step > self.max_step:
            self.project_state = ProjectState.END
            self.log.info("流程结束")
            # self.project_state = ProjectState.INIT
            self.top_step_name = ""
            self.step = self.project_dict['configs']['startStep']

    def executor_running(self):
        # 执行任务
        sequence = self.project_dict['configs']['sequence']
        global_step_counter = [0]
        self.executor_run_step(self.step,sequence,global_step_counter)

    def executor_run_step(self, step_num: int, sequence, global_step_counter: list):
        # 遍历当前序列中的每个步骤
        for step_name_t in sequence:
            # 检查是否是子步骤的标题
            
            if step_name_t in self.project_dict['process'] and 'sequence' in self.project_dict['process'][step_name_t]:
                # 递归处理子步骤，但不更新全局步骤计数器
                if self.top_step_name == "":self.top_step_name = step_name_t
                sub_sequence = self.project_dict['process'][step_name_t]['sequence']
                ret = self.executor_run_step(step_num, sub_sequence, global_step_counter)#成功找到步骤，返回True
                if ret:
                    break
                else:
                    self.top_step_name = ""
                    continue
                

            # 更新全局步骤计数器
            global_step_counter[0] += 1
            current_step = global_step_counter[0]

            # 检查是否达到了目标步骤
            if current_step == step_num:
                # 在process中查找对应的步骤
                step_info = self.project_dict['process'][step_name_t]

                # 获取步骤的object, command, parameters
                obj = step_info['object']
                command = step_info['command']
                parameters = step_info['parameters']
                
                # 将parameters转换为字符串
                parameters_str = " ".join([f"{key}={value}" for key, value in parameters.items()])
                # 将object, command, parameters串成字符串
                result_str = f"{obj} {command} {parameters_str}"

                if self.top_step_name == "":self.top_step_name = step_name_t 

                try:
                    ret = self.sub_parser.parse(result_str)
                    self.executor_step_up(ret)
                except HNSystemError as e:
                    self.log.error('handle error:', e)
                    self.cmd_project_stop()
                    for tuple_t in Facility.tuple_list:
                        name = tuple_t.name
                        if name == obj:
                            tuple_t.facility.state = ParamUtils.set_facility_state(tuple_t.facility.state,FacilityState.STOP)
                return True
            
        return False
                
        
        
        

    def cmd_project_step(self):
        if self.project_state == ProjectState.READY or self.project_state == ProjectState.PAUSE:
            self.log.info("单步执行")
            self.executor_running()
            return
        else :
            self.log.warning("流程未处于 READY 或 PAUSE 状态")


    def cmd_init(self):
        self.parser.register("load", self.cmd_load, {"file": None}, "load file")
        self.parser.register("check", self.check, {}, "show project data")
        self.parser.register("supple", self.cmd_objects_supple, {}, "check objects and supple missing objects")
        self.parser.register("run", self.cmd_project_run, {}, "run project")
        self.parser.register("step", self.cmd_project_step, {}, "run project one step")
        self.parser.register("start", self.cmd_project_start_step, {"step": 1}, "start project from step")
        self.parser.register("stop", self.cmd_project_stop, {}, "stop project")
        self.parser.register("continue", self.cmd_project_continue, {}, "continue project")
        self.parser.register("exit", self.cmd_project_exit, {}, "exit project")

    def cmd_error_handing(self):
        pass

    def cmd_stop_handing(self):
        pass

    def cmd_reset(self):#从error/stop恢复idle的状态
        pass

    # 定义了一个递归函数 print_steps，用于打印步骤序列。
    # 在 print_steps 函数中，检查每个步骤是否包含子步骤，如果包含，则递归调用 print_steps 来打印子步骤。
    # 在主函数中调用 print_steps 来打印顶层步骤序列。
    def check(self):
        def print_steps(sequence, global_step_counter, indent=0):
            for step in sequence:
                if step in self.project_dict['process'] and 'sequence' in self.project_dict['process'][step]:
                    self.log.info(f"{' ' * indent}步骤 {global_step_counter[0]}: {step}")
                    self.log.info(f"{' ' * (indent + 2)}子步骤:")
                    print_steps(self.project_dict['process'][step]['sequence'], global_step_counter, indent + 4)
                else:
                    current_marker = " <-- 当前步骤" if global_step_counter[0] == self.step else ""
                    self.log.info(f"{' ' * indent}步骤 {global_step_counter[0]}: {step}{current_marker}")
                    global_step_counter[0] += 1

        self.log.info("="*40)
        self.log.info(f"当前流程状态: {self.project_state.name}")
        self.log.info("="*40)
        
        self.log.info("流程中的所有步骤:")
        global_step_counter = [1]
        print_steps(self.project_dict['configs']['sequence'], global_step_counter)
        
        self.log.info("\n涉及的对象:")
        for obj in self.project_dict['objects']:
            self.log.info(f"对象: {obj}")
        
        self.log.info("="*40)


    def cmd_objects_supple(self):
        if self.project_dict is None:
            self.log.info("流程信息为空")
            return
        
        self.log.warning("查找缺失对象")
        obj_name_list = []

        for tuple_t in Facility.tuple_list:
            name = tuple_t[0]
            obj_name_list.append(name)

        for file_obj_name in self.project_dict['objects']:
            if any(obj_name == file_obj_name for obj_name in obj_name_list):
                self.log.info(f"对象 {file_obj_name} 存在")
            else:
                self.log.error(f"对象 {file_obj_name} 不存在")
                break
                # # 读取self.data['objects'][file_obj_name]['type']的信息,调用sub_parser的parse方法，输入“os {type} 键1=键的值 ......”
                # print(f"Create object {file_obj_name} in the system.")
                # # 读取 self.data['objects'][file_obj_name]['type'] 的信息
                # obj_type = self.dict['objects'][file_obj_name]['type']
                # obj_params = self.dict['objects'][file_obj_name]
                # # 构建参数字符串
                # obj_params_str = " ".join([f"{key}={value}" for key, value in obj_params.items() if key != 'type'])
                # # 构建最终的命令字符串
                # result_str = f"os {obj_type} name={file_obj_name} {obj_params_str}"
                # # 调用 sub_parser 的 parse 方法
                # ret = self.sub_parser.parse(result_str)
                # if ret != 0:
                #     print(f"Failed to create object {file_obj_name} in the system.")
                #     break
        
    def cmd_project_start_step(self, step: int):
        self.step = step
        self.project_state = ProjectState.INIT
        self.log.info(f"项目从步骤 {step} 开始。")
        self.executor_check_all()

    def cmd_project_run(self):
        if self.project_dict is None:
            self.log.warning("未装载文件")
            return
        
        elif self.project_state == ProjectState.INIT:
            self.executor_check_all()

        elif self.project_state == ProjectState.READY:
            self.log.info("开始运行")
            self.project_state = ProjectState.RUNNING

        elif self.project_state == ProjectState.PAUSE:
            self.log.warning("PAUSE状态，无法运行。")
        

    # stop 即流程控制器不继续派发流程
    def cmd_project_stop(self):
        self.log.info(f"流程 {self.name} 暂停")
        self.project_state = ProjectState.PAUSE

    def cmd_project_continue(self):
        if self.project_state == ProjectState.PAUSE:
            self.log.info(f"流程 {self.name} 继续")
            self.project_state = ProjectState.RUNNING
        else :
            self.log.info("状态错误，流程无法继续")

    def cmd_project_exit(self):
        
        self.project_state = ProjectState.END

    def cmd_load(self, file: str=None):
        if file is None:
            if self.file:
                self.cmd_load_json(self.file)#使用备份
        else:
            # 构建文件路径
            file_path = os.path.join('src/chemistry_os/src/facilities/projects', file)
            # self.log.info("路径: ", file_path)

            if not os.path.isfile(file_path):
                self.log.info(f"文件 {file} 不存在。")
            else:
                self.cmd_load_json(file_path)



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
        self.project_dict = data
        # 创建并启动线程
        self.data_type = "json"
        self.top_step_name = ""
        self.step = self.project_dict['configs']['startStep']
        self.max_step = self.count_total_steps(self.project_dict['configs']['sequence'])
        # 调用新的函数来设置对象参数
        self.cmd_set_objects_parameters()

    def cmd_set_objects_parameters(self):
        """
        将 JSON 中的参数赋值给系统中已存在的对象
        """
        # 遍历 JSON 中的 objects
        for obj_name, obj_params in self.project_dict.get('objects', {}).items():
            obj_instance = Facility.get_facility_by_name(name=obj_name)
            if obj_instance:
                # 将 JSON 中的参数赋值给对象
                for param_key, param_value in obj_params.items():
                    if hasattr(obj_instance, param_key):
                        # 实际赋值操作
                        setattr(obj_instance, param_key, param_value)
                        self.log.info(f"设置对象 {obj_name} 的参数 {param_key} 为 {param_value}")
            else:
                self.log.warning(f"未找到名称为 {obj_name} 的对象，无法设置参数")