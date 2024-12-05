import shlex

class PkgCmdParser:
    def __init__(self, pkg_name: str):
        self.commands = {}
        self.pkg_name = pkg_name

    def register(self, name, func, params=None, description=""):
        if name in self.commands:
            raise ValueError(f"Command '{name}' is already registered.")
        if params is None:
            params = {}
        self.commands[name] = {
            "function": func,
            "params": params,
            "description": description
        }

    def cmd(self, command_line):
        tokens = shlex.split(command_line)
        if len(tokens) < 1:
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
        self.cmd_print(f"Commands list:")
        print("+" + "-"*78 + "+")
        print(f"| {'Command':<20} | {'Description':<30} | {'Params':<20} |")
        print("+" + "-"*78 + "+")
        for name, info in self.commands.items():
            params = ', '.join([f"{k}={v}" for k, v in info['params'].items()])
            print(f"| {name:<20} | {info['description']:<30} | {params:<20} |")
        print("+" + "-"*78 + "+")

    def cmd_print(self,message):
        print(f"{self.pkg_name}: {message}")


# class CommandParser:
#     def __init__(self):
#         self.commands = {}

#     def register_command(self, name, handler, description=""):
#         self.commands[name] = {
#             "handler": handler,
#             "description": description
#         }

#     def parse(self, command_line):
#         tokens = shlex.split(command_line)
#         if not tokens:
#             return

#         # 解析对象和指令
#         object_command = tokens[0].split(':')
#         if len(object_command) != 2:
#             print("Invalid command format. Expected format: object:command")
#             return

#         object_name, command_name = object_command
#         args = tokens[1:]

#         if command_name in self.commands:
#             handler = self.commands[command_name]["handler"]
#             handler(object_name, args)
#         else:
#             print(f"Unknown command: {command_name}")

#     def list_commands(self):
#         for name, info in self.commands.items():
#             print(f"{name}: {info['description']}")

# # 示例命令处理函数
# def move_command(object_name, args):
#     print(f"Moving {object_name} with args: {args}")

# def stop_command(object_name, args):
#     print(f"Stopping {object_name} with args: {args}")

# # 创建命令解析器实例并注册命令
# parser = CommandParser()
# parser.register_command("move", move_command, "Move the robot")
# parser.register_command("stop", stop_command, "Stop the robot")

# # 示例命令行输入
# parser.parse("robot1:move x=1 y=2 -s")
# parser.parse("robot1:stop -f")
# parser.list_commands()