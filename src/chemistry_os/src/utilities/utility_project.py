from dataclasses import dataclass
import sys
import os
from datetime import datetime
from typing import Any, Callable, Dict, Literal, overload
import typing
import json
import inspect
sys.path.append('src/chemistry_os/src')
from exceptions import ProjectUtilsError
from utilities.utility_log import LogUtils
from structs import ServerMod
from facility import Facility

class ProjectUtils:
    objects_dict = {}
    configs_dict = {}
    process_dict = {}
    config_sequence = []
    sequence_flags = [
        "PROJECT_SEQUENCE_START"
        ]
    
    _process_counter = 1  # 用于自动分配流程名称
    _function_registry: Dict[str, Callable[[], None]] = {}

    output_dir:str = "src/chemistry_os/src/facilities/projects"
    file_name: str = None

    @staticmethod
    def register_object(name: str, obj_type: str = None, args:dict =None):
        """
        注册对象信息
        :param name: 对象名称
        :param obj_type: 对象类型，如果不提供将尝试从 facility 中获取
        :param kwargs: 对象的其他参数
        """
        # 如果没有提供类型，尝试从 Facility.tuple_list 中获取
        facility_obj = Facility.get_facility_by_name(name)
        if obj_type is None:
            if facility_obj:
                obj_type = facility_obj.type
            else:
                raise ValueError(f"未找到名为 {name} 的对象，且未提供对象类型")
        
        if args is None:
            if facility_obj and  hasattr(facility_obj,"init_dict"):
                args = facility_obj.init_dict
            else:
                args = {}
        # 构建对象信息
        obj_info = {"type": obj_type}
        obj_info.update(args)
        
        ProjectUtils.objects_dict[name] = obj_info
        LogUtils.log.info(f"json对象: {name}, 类型: {obj_type}, 参数: {args}")

    @staticmethod
    def register_function(name: str, func: Callable[[], None]):
        """
        注册函数到函数注册表
        :param name: 函数名称（字符串标识）
        :param func: 要注册的函数
        """
        ProjectUtils._function_registry[name] = func
        LogUtils.log.info(f"已注册函数: {name}")

    @staticmethod
    def register_process(obj_name: str, command_name: str, parameters=None, process_name: str = None):
        """
        处理字符串方式的流程注册
        :param obj_name: 对象名称
        :param command_name: 命令名称
        :param parameters: 参数，支持列表或字典形式
        :param process_name: 流程名称，如果为None则自动生成
        """
        try:
            if parameters is None:
                parameters = {}
                
            # 生成流程名称
            if process_name is None:
                process_name = f"step{ProjectUtils._process_counter}"
                ProjectUtils._process_counter += 1
                
            # 验证对象是否存在
            facility_obj = Facility.get_facility_by_name(obj_name)

            if not facility_obj:
                raise ProjectUtilsError(f"对象 {obj_name} 不存在于系统中",)
            
            # 获取对象的预制参数
            predef_params = ProjectUtils._get_command_params(facility_obj, command_name)
            
            if predef_params is None:
                raise ProjectUtilsError(f"对象 {obj_name} 中未找到命令 {command_name}")
            
            # 处理参数
            final_parameters = ProjectUtils._process_parameters(parameters, predef_params)
            
            # 构建流程信息
            process_info = {
                "object": obj_name,
                "command": command_name,
                "parameters": final_parameters
            }
            
            ProjectUtils.process_dict[process_name] = process_info
            ProjectUtils.config_sequence.append(process_name)
            LogUtils.log.info(f"注册流程: {process_name} -> {obj_name} {command_name} {final_parameters}")
            
            return True
            
        except ProjectUtilsError as e:
            LogUtils.log.error(f"流程注册失败: {e.message}")
            return False

    @staticmethod
    def _get_command_params(facility_obj:Facility, command_name: str):
        if command_name in facility_obj.parser.commands:
            return facility_obj.parser.commands[command_name]['params'].copy()
        else:
            return None

    @staticmethod
    def _process_parameters(input_params, predef_params: dict = {}):
        # 处理列表形式的参数
        if isinstance(input_params, list):
            param_keys = list(predef_params.keys())
            if len(input_params) > len(param_keys):
                raise ProjectUtilsError(f"参数数量过多:只接受 {len(param_keys)} 个参数，但提供了 {len(input_params)} 个")
            
            result_params = predef_params.copy()
            for i, value in enumerate(input_params):
                if i < len(param_keys):
                    key = param_keys[i]
                    result_params[key] = value
                
            return result_params
        
        # 处理字典形式的参数
        elif isinstance(input_params, dict):
            # 检查输入的键是否都存在于预制参数中
            for key in input_params.keys():
                if key not in predef_params:
                    raise ProjectUtilsError(f"未知参数键: {key}，只支持以下参数: {list(predef_params.keys())}")

            return input_params
        
        else:
            raise ProjectUtilsError(f"不支持的参数类型: {type(input_params)}，请使用列表或字典形式")

    @staticmethod
    def register_sub_process_start():
        ProjectUtils.config_sequence.append("PROJECT_SEQUENCE_START")
    
    @staticmethod
    def register_sub_process(name: str = None):
        """
        注册子流程，从最末尾开始往前数，直到到达 config_sequence 的头部或遇到:
        1. 步骤含有 "sequence" 键的流程
        2. SUB_SEQUENCE_START 标签
        
        将数到的步骤从 config_sequence 中去除，并加入到新的子流程中
        :param name: 子流程名称
        """


        # 从末尾开始收集步骤
        collected_steps = []
        stop_index = 0

        # 从后往前遍历
        for i in range(len(ProjectUtils.config_sequence) - 1, -1, -1):#起始，结尾，步长
            step_name = ProjectUtils.config_sequence[i]
            
            # 检查是否是 SUB_SEQUENCE_START 标签
            if step_name == "PROJECT_SEQUENCE_START":
                stop_index = i + 1
                break
            
            # 检查是否是已存在的子流程（含有 sequence 键）
            if step_name in ProjectUtils.process_dict:
                if "sequence" in ProjectUtils.process_dict[step_name]:
                    stop_index = i + 1
                    break
            
            # 将步骤添加到收集列表的开头（保持原顺序）
            collected_steps.insert(0, step_name)
        
        if not collected_steps:
            LogUtils.log.warning("没有找到可以归入子流程的步骤")
            return False
        ProjectUtils.config_sequence = ProjectUtils.config_sequence[:stop_index]
        
        # 创建子流程
        sub_process_info = {
            "sequence": collected_steps
        }
        if name is None:
            name = f"sub_process_{ProjectUtils._process_counter}"
            ProjectUtils._process_counter += 1
        ProjectUtils.process_dict[name] = sub_process_info
        # 将子流程名添加到 config_sequence
        ProjectUtils.config_sequence.append(name)
        # LogUtils.log.info(f"已创建子流程 {name}，包含步骤: {collected_steps}")
        return True

        
    @staticmethod
    def make_func():
        pass

    @staticmethod
    def redefine_make_func(new_func: Callable[[], None]) -> None:
        ProjectUtils.make_func = staticmethod(new_func)


    @staticmethod
    def _build_json_data():
        """
        构建 JSON 数据结构
        :return: 完整的 JSON 数据字典
        """
        ProjectUtils.make_func()

        # 创建临时配置序列，过滤掉 ProjectSequenceFlags 中的标志
        temp_config_sequence = [
            step for step in ProjectUtils.config_sequence 
            if step not in ProjectUtils.sequence_flags
        ]
        
        return {
            "objects": ProjectUtils.objects_dict.copy(),
            "configs": {
                "sequence": temp_config_sequence,
                "startStep": 1,
                "endCondition": "completion"
            },
            "process": ProjectUtils.process_dict.copy()
        }

    
    @staticmethod
    def make(json_name: str = None):
        """
        生成 JSON 文件
        :param json_name: JSON 文件名（不包含扩展名）
        """
        if json_name is None:
            json_name = f"{ProjectUtils.get_program_name()}.json"

        # 确保目录存在
        output_dir = ProjectUtils.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, f"{json_name}")
        
        # 构建和写入 JSON 数据
        json_data = ProjectUtils._build_json_data()

        ProjectUtils.file_name = f"{json_name}"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            LogUtils.log.info(f"JSON 文件已生成: {file_path}")
            ProjectUtils.clear_all()
            return file_path
        except Exception as e:
            LogUtils.log.error(f"生成 JSON 文件时出错: {e}")
            return None
        
    # 修改：redefine_and_make 方法
    @staticmethod
    def redefine_and_make(func_name: str, json_name: str = None):
        """
        通过函数名称查找并执行注册的函数，然后生成JSON文件
        :param func_name: 已注册的函数名称
        :param json_name: JSON文件名（可选）
        """
        file_path = None
        LogUtils.log.info(f"=== 使用函数 '{func_name}' 生成项目文件 ===")
        if func_name not in ProjectUtils._function_registry:
            LogUtils.log.error(f"函数 '{func_name}' 未在注册表中找到")
            LogUtils.log.info(f"可用函数: {list(ProjectUtils._function_registry.keys())}")
        else:
            # 获取注册的函数
            target_func: Callable[[], None] = ProjectUtils._function_registry[func_name]
            
            # 执行原有逻辑
            ProjectUtils.redefine_make_func(target_func)
            file_path = ProjectUtils.make(json_name)
            
            LogUtils.log.info(f"已生成项目文件")
        return file_path


    @staticmethod
    def get_program_name():
        # 获取调用者的文件名
        import inspect
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            while caller_frame and caller_frame.f_code.co_filename.endswith('utility_project.py'):
                caller_frame = caller_frame.f_back
            
            if caller_frame:
                caller_file = os.path.basename(caller_frame.f_code.co_filename)
                base_name = os.path.splitext(caller_file)[0]
            else:
                base_name = "generated_project"
        finally:
            del frame
        return base_name

    
    @staticmethod
    def show_registered_data():
        """显示当前注册的所有数据"""
        LogUtils.log.info("=== 已注册的对象 ===")
        for name, info in ProjectUtils.objects_dict.items():
            LogUtils.log.info(f"  {name}: {info}")
        
        LogUtils.log.info("=== 已注册的流程 ===")
        for name, info in ProjectUtils.process_dict.items():
            LogUtils.log.info(f"  {name}: {info}")
        
        LogUtils.log.info("=== JSON 预览 ===")
        # 使用公共方法构建 JSON 数据并显示预览
        preview_json = ProjectUtils._build_json_data()
        
        # 格式化 JSON 并显示
        try:
            json_preview = json.dumps(preview_json, ensure_ascii=False, indent=2)
            LogUtils.log.info(f"\n{json_preview}")
        except Exception as e:
            LogUtils.log.error(f"生成 JSON 预览时出错: {e}")

    @staticmethod
    def clear_all():
        """清空所有注册的数据"""
        ProjectUtils.objects_dict.clear()
        ProjectUtils.process_dict.clear()
        ProjectUtils.configs_dict.clear()
        ProjectUtils.config_sequence.clear()
        ProjectUtils._process_counter = 1
        LogUtils.log.info("已清空所有注册数据")



