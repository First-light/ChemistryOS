import sys
sys.path.append('src/chemistry_os/src')
import shlex
from prettytable import PrettyTable

class PkgCmdParser:
    def __init__(self, obj_name: str):
        self.commands = {}
        self.obj_name = obj_name

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
            self.cmd_print(f"Command shouldn't be empty")
            return
        # 解析指令名称
        command_name = tokens[0]
        if command_name not in self.commands:
            if command_name == "list":self.list()
            else: self.cmd_print(f"Unknown command: {command_name}")
            return

        handler = self.commands[command_name]["function"]
        args = tokens[1:]
        params = self.commands[command_name]["params"].copy()

        if not params:
            handler()  # 无参数指令直接执行
        else:
            for arg in args:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                else:
                    self.cmd_print(f"Invalid param syntax,pleace input:'param=value'")
                    return
                if key in params:
                    params[key] = value
                else:
                    self.cmd_print(f"Unknown param: {key}")
                    return
                if value == '':
                    self.cmd_print(f"{key}'s value shouldn't be empty")
                    return
            handler(**params)  # 执行函数

    def list(self):
        table = PrettyTable()
        table.field_names = ["Command", "Description", "Params"]

        for name, info in self.commands.items():
            params = ', '.join([f"{k}={v}" for k, v in info['params'].items()])
            table.add_row([name, info['description'], params])

        self.cmd_print("Commands list:")
        print(table)

    def cmd_print(self,message):
        print(f"{self.obj_name}: {message}")