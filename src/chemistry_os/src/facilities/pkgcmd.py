import sys
from typing import TypedDict, Dict, Any, Callable

sys.path.append('src/chemistry_os/src')
import shlex
from prettytable import PrettyTable
from structs import FacilityState
from interfaces import IFacility  # 依赖接口而不是具体类

class CommandInfo(TypedDict):
    cmd: Callable
    function: Callable
    params: Dict[str, Any]
    description: str

class PkgCmdParser:

    def __init__(self, facility:IFacility):
        self.commands: Dict[str, CommandInfo] = {}
        self.obj_name = facility.name
        self.obj_state = facility.state
        self.obj_log = facility.log
        self.special_commands = {
            "list": self.list,
            "lock": self.lock,
            "unlock": self.unlock,
            # 可以在这里添加更多特殊指令及其处理函数
        }


    def register(self, name, func, params=None, description=""):
        if name in self.commands:
            self.obj_log.warning(f"指令 '{name}' 已经注册.")
        if params is None:
            params = {}
        self.commands[name] = {
            "cmd": self.cmd,
            "function": func,
            "params": params,
            "description": description
        }

    def cmd(self, command_line):
        tokens = shlex.split(command_line)
        if len(tokens) < 1:
            self.obj_log.warning("指令不能为空")
            return 2

        # 解析指令名称
        command_name = tokens[0]

        # 优先处理特殊指令
        if command_name in self.special_commands:
            self.special_commands[command_name]()
            return 0

        if command_name not in self.commands:
            self.obj_log.warning(f"未知指令 {command_name}")
            return 2
        
        if self.obj_state == FacilityState.BUSY:
            self.obj_log.warning(f"{self.obj_name} 设备忙碌.")
            return 2
        elif self.obj_state == FacilityState.STOP:
            self.obj_log.warning(f"{self.obj_name} 设备已停机.")
            return 2
        elif self.obj_state == FacilityState.ERROR:
            self.obj_log.warning(f"{self.obj_name} 设备故障.")
            return 2
        else:
            self.obj_state = FacilityState.BUSY

        handler = self.commands[command_name]["function"]
        args = tokens[1:]
        params = self.commands[command_name]["params"].copy()  # 现在类型明确了
        # print(params)
        if not params:
            handler()  # 无参数指令直接执行
        else:
            for arg in args:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    try:
                        # 尝试将 value 转换为浮点数
                        value = float(value)
                    except ValueError:
                        # 如果转换失败，则保持为字符串
                        pass
                else:
                    self.obj_log.warning("错误的指令格式，请按要求输入:'param=value'")
                    return 2
                if key in params:
                    params[key] = value
                else:
                    self.obj_log.warning(f"未知键值: {key}")
                    return 2
                if value == '':
                    self.obj_log.warning(f"键值{key}参数不能为空")
                    return 2
            handler(**params)  # 执行函数

        if self.obj_state == FacilityState.BUSY:
            self.obj_state = FacilityState.IDLE
            return 0
        else:
            self.obj_log.warning(f"{self.obj_name} is {self.obj_state}.")
            return 2
        


    def list(self):
        table = PrettyTable()
        table.field_names = ["Command", "Description", "Params"]

        for name, info in self.commands.items():
            params = ', '.join([f"{k}={v}" for k, v in info['params'].items()])
            table.add_row([name, info['description'], params])

        self.obj_log.info(f"指令列表:\n{table}")

    def lock(self):
        self.obj_log.info("设备锁定")
        self.obj_state = FacilityState.STOP
    
    def unlock(self):
        self.obj_log.info("设备解锁")
        self.obj_state = FacilityState.IDLE

    def cmd_print(self,message):
        print(f"{self.obj_name}: {message}")




