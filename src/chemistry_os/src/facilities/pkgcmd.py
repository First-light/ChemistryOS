import sys
from typing import TypedDict, Dict, Any, Callable

sys.path.append('src/chemistry_os/src')
import shlex
from prettytable import PrettyTable
from structs import FacilityState
from interfaces import IFacility  # 依赖接口而不是具体类
from utilities.utility_log import LogUtils

class CommandInfo(TypedDict):
    cmd: Callable
    function: Callable
    params: Dict[str, Any]
    description: str

class PkgCmdParser:

    def __init__(self, facility:IFacility):
        self.commands: Dict[str, CommandInfo] = {}
        self.facility = facility
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

    def cmd(self, command_line) -> bool:
        
        result = True
        self.obj_state = self.facility.state # 更新状态
        tokens = shlex.split(command_line)
        
        if len(tokens) < 1:
            self.obj_log.warning("指令不能为空")
            result = False
        else:
            command_name = tokens[0]
            if command_name in self.special_commands:
                self.special_commands[command_name]()
            else:
                if self._cmd_check(command_name):
                    if not self._cmd_execute(tokens):result = False
                else:
                    result = False
        return result
    
    def _cmd_check(self, command_name):
        # 优先处理特殊指令
        result = False
        if command_name not in self.commands:
            self.obj_log.warning(f"未知指令 {command_name}")
        elif self.obj_state == FacilityState.BUSY:
            self.obj_log.warning(f"{self.obj_name} 设备忙碌.")
        elif self.obj_state == FacilityState.STOP:
            self.obj_log.warning(f"{self.obj_name} 设备已停机.")
        elif self.obj_state == FacilityState.ERROR:
            self.obj_log.warning(f"{self.obj_name} 设备故障.")
        else:
            result = True
        return result

    

    def _cmd_execute(self,tokens):
        handler = self.commands[tokens[0]]["function"]
        args = tokens[1:]
        params = self.commands[tokens[0]]["params"].copy()
        result = True
        if not params:
            handler()
        else:
            for arg in args:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                else:
                    self.obj_log.warning("错误的指令格式，请按要求输入:'param=value'")
                    result = False
                    break
                if key in params:
                    params[key] = value
                else:
                    self.obj_log.warning(f"未知键值: {key}")
                    result = False
                    break
                if value == '':
                    self.obj_log.warning(f"键值{key}参数不能为空")
                    result = False
                    break
            else:
                if self.obj_state == FacilityState.IDLE:
                    self.obj_state = FacilityState.BUSY
                handler(**params)
                if self.obj_state == FacilityState.BUSY:
                    self.obj_state = FacilityState.IDLE
                else:
                    self.obj_log.error(f"设备运行时状态异常：{self.obj_state}")
                    result = False
        return result

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




