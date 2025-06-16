import sys
sys.path.append('src/chemistry_os/src')
import shlex
from prettytable import PrettyTable
from structs import FacilityState

class PkgCmdParser:
    def __init__(self, obj_name: str, object_state_p):
        self.commands = {}
        self.special_commands = {
            "list": self.list,
            "lock": self.lock,
            "unlock": self.unlock,
            # 可以在这里添加更多特殊指令及其处理函数
        }
        self.obj_name = obj_name
        self.object_state_p = object_state_p

    def register(self, name, func, params=None, description=""):
        if name in self.commands:
            raise ValueError(f"Command '{name}' is already registered.")
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
            self.cmd_print("Command shouldn't be empty")
            return 2

        # 解析指令名称
        command_name = tokens[0]

        # 优先处理特殊指令
        if command_name in self.special_commands:
            self.special_commands[command_name]()
            return 0

        if command_name not in self.commands:
            self.cmd_print(f"Unknown command: {command_name}")
            return 2
        
        if self.object_state_p[0] == FacilityState.BUSY:
            print(f"{self.obj_name} is busy.")
            return 2
        elif self.object_state_p[0] == FacilityState.STOP:
            print(f"{self.obj_name} is stopped.")
            return 2
        elif self.object_state_p[0] == FacilityState.ERROR:
            print(f"{self.obj_name} is in error state.")
            return 2
        else:
            self.object_state_p[0] = FacilityState.BUSY

        handler = self.commands[command_name]["function"]
        args = tokens[1:]
        params = self.commands[command_name]["params"].copy()
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
                    self.cmd_print("Invalid param syntax, please input: 'param=value'")
                    return 2
                if key in params:
                    params[key] = value
                else:
                    self.cmd_print(f"Unknown param: {key}")
                    return 2
                if value == '':
                    self.cmd_print(f"{key}'s value shouldn't be empty")
                    return 2
            handler(**params)  # 执行函数

        if self.object_state_p[0] == FacilityState.BUSY:
            self.object_state_p[0] = FacilityState.IDLE
            return 0
        else:
            print(f"{self.obj_name} is {self.object_state_p[0]}.")
            return 2
        


    def list(self):
        table = PrettyTable()
        table.field_names = ["Command", "Description", "Params"]

        for name, info in self.commands.items():
            params = ', '.join([f"{k}={v}" for k, v in info['params'].items()])
            table.add_row([name, info['description'], params])

        self.cmd_print("Commands list:")
        print(table)

    def lock(self):
        self.cmd_print("lock")
        self.object_state_p[0] = FacilityState.STOP
    
    def unlock(self):
        self.cmd_print("unlock")
        self.object_state_p[0] = FacilityState.IDLE

    def cmd_print(self,message):
        print(f"{self.obj_name}: {message}")


    
        
